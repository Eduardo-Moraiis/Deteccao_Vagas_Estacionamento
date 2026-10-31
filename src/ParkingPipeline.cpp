#include "ParkingPipeline.hpp"

ParkingPipeline::ParkingPipeline(int limiar) : limiarTau(limiar) {}

void ParkingPipeline::definirLimiar(int novoLimiar) {
    limiarTau = novoLimiar;
}

int ParkingPipeline::obterLimiar() const {
    return limiarTau;
}

Mat ParkingPipeline::processarImagemPDI(const Mat& entrada) {
    Mat cinza, suave, binarizada, dilatada;

    // 1. PDI: Conversão de cor (BGR para Escala de Cinza)
    cvtColor(entrada, cinza, COLOR_BGR2GRAY);

    // 2. PDI: Filtragem Espacial (Filtro Gaussiano 3x3 para atenuar ruído)
    GaussianBlur(cinza, suave, Size(3, 3), 1);

    // 3. PDI: Segmentação por Limiarização Adaptativa (Tolerante a sombras)
    adaptiveThreshold(suave, binarizada, 255, 
                      ADAPTIVE_THRESH_GAUSSIAN_C, 
                      THRESH_BINARY_INV, 25, 16);

    // 4. PDI: Morfologia Matemática (Dilatação para conectar arestas do veículo)
    Mat elementoEstruturante = getStructuringElement(MORPH_RECT, Size(3, 3));
    dilate(binarizada, dilatada, elementoEstruturante);

    return dilatada;
}

void ParkingPipeline::classificarVagas(const Mat& imagemBinarizada, vector<Vaga>& vagas) {
    for (auto& vaga : vagas) {
        // Valida se a ROI está dentro dos limites da imagem
        Rect roi = vaga.caixaDelimitadora & Rect(0, 0, imagemBinarizada.cols, imagemBinarizada.rows);
        if (roi.width <= 0 || roi.height <= 0) continue;

        // Recorte da ROI na imagem binarizada
        Mat corteVaga = imagemBinarizada(roi);

        // Cria uma máscara poligonal exata da vaga (elimina ruído dos cantos fora do polígono)
        Mat mascara = Mat::zeros(corteVaga.size(), CV_8UC1);
        vector<Point> pontosLocais;
        for (const auto& pt : vaga.contorno) {
            pontosLocais.push_back(Point(pt.x - roi.x, pt.y - roi.y));
        }
        fillConvexPoly(mascara, pontosLocais, Scalar(255));

        // Aplica a máscara e conta apenas os pixels de dentro da vaga
        Mat vagaIsolada;
        bitwise_and(corteVaga, corteVaga, vagaIsolada, mascara);

        // VC: Extração de característica (densidade de pixels brancos)
        vaga.pixelsBrancos = countNonZero(vagaIsolada);

        // VC: Tomada de decisão por limiar tau
        vaga.ocupadaPredita = (vaga.pixelsBrancos >= limiarTau);
    }
}

void ParkingPipeline::renderizarVisualizacao(Mat& imagemOriginal, const vector<Vaga>& vagas) {
    int livres = 0;
    int ocupadas = 0;

    for (const auto& vaga : vagas) {
        Scalar cor;
        if (vaga.ocupadaPredita) {
            cor = Scalar(0, 0, 255); // Vermelho: Ocupada
            ocupadas++;
        } else {
            cor = Scalar(0, 255, 0); // Verde: Livre
            livres++;
        }

        // Desenha o polígono da vaga
        polylines(imagemOriginal, vaga.contorno, true, cor, 2);

        // Exibe o ID e os pixels detectados
        if (!vaga.contorno.empty()) {
            string info = to_string(vaga.id) + " (" + to_string(vaga.pixelsBrancos) + ")";
            putText(imagemOriginal, info, vaga.contorno[0], 
                    FONT_HERSHEY_PLAIN, 0.9, Scalar(255, 255, 255), 1);
        }
    }

    // Desenha o Placar superior
    string textoPlacar = "Vagas Livres: " + to_string(livres) + " / Total: " + to_string(vagas.size());
    rectangle(imagemOriginal, Point(20, 20), Point(420, 65), Scalar(0, 0, 0), FILLED);
    putText(imagemOriginal, textoPlacar, Point(30, 52), FONT_HERSHEY_SIMPLEX, 0.7, Scalar(0, 255, 255), 2);
}