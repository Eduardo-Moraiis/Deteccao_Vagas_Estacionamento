#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <opencv2/opencv.hpp>
#include "ParkingPipeline.hpp"
#include "DatasetParser.hpp"
#include "Evaluator.hpp"

using namespace std;
namespace fs = std::filesystem;

// Raiz da base PKLot, relativa ao diretório de execução (cmake-build-*)
static const string CAMINHO_BASE_PKLOT = "../data/PKLot/PKLot/";
static const int TAU_OTIMO = 900;

// ============================================================================
// MODO 1 (padrão): avaliação global do dataset completo - comportamento original
// ============================================================================
static int executarBenchmark() {
    cout << "=====================================================" << endl;
    cout << "   AVALIACAO GLOBAL DO DATASET COMPLETO (PKLot)      " << endl;
    cout << "=====================================================" << endl;

    // limiar ótimo comprovado nos experimentos preliminares
    int tauOtimo = TAU_OTIMO;
    ParkingPipeline pipeline(tauOtimo);

    // O valor -1 desativa qualquer limite e processa TODAS as fotos
    int limitePorClima = -1;

    // Lista dos 3 pátios da base PKLot
    vector<string> patios = {"UFPR04", "UFPR05", "PUCPR"};
    vector<string> climas = {"Sunny", "Cloudy", "Rainy"};

    vector<MetricasClima> resultadosGlobais;

    string caminhoBasePKLot = CAMINHO_BASE_PKLOT;

    // Percorre cada pátio e cada clima
    for (const auto &patio: patios) {
        cout << "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" << endl;
        cout << "Iniciando processamento do patio: " << patio << endl;
        cout << ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" << endl;

        for (const auto &clima: climas) {
            string pastaClima = caminhoBasePKLot + patio + "/" + clima;
            string identificador = patio + "_" + clima;

            MetricasClima m = Evaluator::avaliarClima(pastaClima, identificador, pipeline, limitePorClima);
            resultadosGlobais.push_back(m);
        }
    }

    // 1. Imprime a tabela comparativa geral no console
    Evaluator::imprimirTabelaComparativa(resultadosGlobais);

    // 2. Salva o resultado massivo no histórico CSV
    Evaluator::salvarHistoricoCSV("../historico_final_tau_900.csv", tauOtimo, resultadosGlobais);

    cout << "\n[FINALIZADO] Todas as imagens foram processadas e registradas com sucesso!" << endl;
    return 0;
}

// ============================================================================
// MODO 2 (--galeria): mosaico 3x3 (pátio x clima) + mosaico das imagens binarizadas
// ============================================================================
struct AmostraGaleria {
    string patio;
    string clima;
    string caminhoSemExtensao; // relativo a CAMINHO_BASE_PKLOT, sem .jpg/.xml
};

// Linhas = pátios (UFPR04, UFPR05, PUCPR); colunas = clima (Sunny, Cloudy, Rainy)
static const vector<AmostraGaleria> AMOSTRAS = {
    {"UFPR04", "Sunny", "UFPR04/Sunny/2013-01-29/2013-01-29_20_26_23"},
    {"UFPR04", "Cloudy", "UFPR04/Cloudy/2013-01-29/2013-01-29_16_21_18"},
    {"UFPR04", "Rainy", "UFPR04/Rainy/2013-01-21/2013-01-21_10_00_05"},

    {"UFPR05", "Sunny", "UFPR05/Sunny/2013-14-16/2013-04-16_07_50_02"},
    {"UFPR05", "Cloudy", "UFPR05/Cloudy/2013-03-13/2013-03-13_08_10_02"},
    {"UFPR05", "Rainy", "UFPR05/Rainy/2013-02-26/2013-02-26_13_19_33"},

    {"PUCPR", "Sunny", "PUCPR/Sunny/2012-11-20/2012-11-20_15_09_41"},
    {"PUCPR", "Cloudy", "PUCPR/Cloudy/2012-09-28/2012-09-28_07_51_02"},
    {"PUCPR", "Rainy", "PUCPR/Rainy/2012-11-10/2012-11-10_08_12_43"},
};

// Tamanho de cada célula do mosaico (proporção 16:9 das imagens 1280x720)
static const int LARG_CELULA = 640;
static const int ALT_CELULA = 360;

// Localiza o .jpg da amostra. Se o caminho exato não existir (ex.: nome de pasta
// de data diferente), procura o arquivo pelo nome dentro de pátio/clima.
static string localizarJPG(const AmostraGaleria &a) {
    string direto = CAMINHO_BASE_PKLOT + a.caminhoSemExtensao + ".jpg";
    if (fs::exists(direto)) return direto;

    string nomeArquivo = fs::path(a.caminhoSemExtensao).filename().string() + ".jpg";
    string pastaBusca = CAMINHO_BASE_PKLOT + a.patio + "/" + a.clima;
    if (fs::exists(pastaBusca)) {
        for (const auto &entry: fs::recursive_directory_iterator(pastaBusca)) {
            if (entry.is_regular_file() && entry.path().filename().string() == nomeArquivo) {
                cerr << "[AVISO] Caminho exato nao encontrado; usando: " << entry.path().string() << endl;
                return entry.path().string();
            }
        }
    }
    return "";
}

// Célula cinza indicando que a amostra não pôde ser carregada
static Mat celulaIndisponivel(const AmostraGaleria &a) {
    Mat c(ALT_CELULA, LARG_CELULA, CV_8UC3, Scalar(60, 60, 60));
    putText(c, a.patio + " - " + a.clima, Point(20, 150), FONT_HERSHEY_SIMPLEX, 0.8, Scalar(0, 255, 255), 2);
    putText(c, "Amostra nao encontrada", Point(20, 190), FONT_HERSHEY_SIMPLEX, 0.7, Scalar(255, 255, 255), 2);
    return c;
}

// Desenha as caixas (verde = livre, vermelho = ocupada, segundo a PREDIÇÃO) e o placar.
// 'escala' converte as coordenadas da imagem original para a célula redimensionada.
static void desenharCaixasEPlacar(Mat &celula, const vector<Vaga> &vagas, double escala,
                                  const string &titulo) {
    int ocupadasPred = 0;
    int ocupadasReal = 0;

    for (const auto &v: vagas) {
        if (v.ocupadaPredita) ocupadasPred++;
        if (v.ocupadaReal) ocupadasReal++;

        vector<Point> poligono;
        for (const auto &p: v.contorno) {
            poligono.push_back(Point(cvRound(p.x * escala), cvRound(p.y * escala)));
        }
        Scalar cor = v.ocupadaPredita ? Scalar(0, 0, 255) : Scalar(0, 255, 0);
        polylines(celula, poligono, true, cor, 2);
    }

    int total = (int) vagas.size();
    int livresPred = total - ocupadasPred;

    // Placar em UMA linha, em faixa fina na base da célula
    const int ALTURA_FAIXA = 20;
    const double FONTE = 0.5;
    rectangle(celula, Point(0, celula.rows - ALTURA_FAIXA), Point(celula.cols, celula.rows),
              Scalar(0, 0, 0), FILLED);

    int x = 6;
    int y = celula.rows - 6;
    auto escrever = [&](const string &texto, const Scalar &cor) {
        putText(celula, texto, Point(x, y), FONT_HERSHEY_SIMPLEX, FONTE, cor, 1, LINE_AA);
        int base = 0;
        x += getTextSize(texto, FONT_HERSHEY_SIMPLEX, FONTE, 1, &base).width;
    };
    escrever(titulo, Scalar(0, 255, 255));
    escrever("  |  Vagas: " + to_string(total), Scalar(255, 255, 255));
    escrever("  Ocupadas: " + to_string(ocupadasPred), Scalar(80, 80, 255));
    escrever("  Livres: " + to_string(livresPred), Scalar(80, 255, 80));
    escrever("  |  Gabarito: " + to_string(ocupadasReal), Scalar(180, 180, 180));

    rectangle(celula, Point(0, 0), Point(celula.cols - 1, celula.rows - 1), Scalar(255, 255, 255), 1);
}

// Processa uma amostra e devolve (célula colorida com caixas, célula binarizada com caixas)
static pair<Mat, Mat> processarAmostra(const AmostraGaleria &a, ParkingPipeline &pipeline) {
    string caminhoJPG = localizarJPG(a);
    if (caminhoJPG.empty()) {
        cerr << "[ERRO] JPG nao encontrado para: " << a.caminhoSemExtensao << endl;
        return {celulaIndisponivel(a), celulaIndisponivel(a)};
    }

    fs::path caminhoXML = fs::path(caminhoJPG).replace_extension(".xml");
    Mat frame = imread(caminhoJPG);
    vector<Vaga> vagas = DatasetParser::carregarVagasXML(caminhoXML.string());
    if (frame.empty() || vagas.empty()) {
        cerr << "[ERRO] Falha ao carregar imagem/XML: " << caminhoJPG << endl;
        return {celulaIndisponivel(a), celulaIndisponivel(a)};
    }

    // Mesmo pipeline do benchmark: PDI global + classificação por vaga
    Mat binaria = pipeline.processarImagemPDI(frame);
    pipeline.classificarVagas(binaria, vagas);

    double escala = (double) LARG_CELULA / frame.cols;
    string titulo = a.patio + " - " + a.clima;

    Mat celulaCor, celulaBin, celulaBinBGR;
    resize(frame, celulaCor, Size(LARG_CELULA, ALT_CELULA), 0, 0, INTER_AREA);
    resize(binaria, celulaBin, Size(LARG_CELULA, ALT_CELULA), 0, 0, INTER_AREA);
    cvtColor(celulaBin, celulaBinBGR, COLOR_GRAY2BGR);

    desenharCaixasEPlacar(celulaCor, vagas, escala, titulo);
    desenharCaixasEPlacar(celulaBinBGR, vagas, escala, titulo);

    return {celulaCor, celulaBinBGR};
}

static int executarGaleria(bool mostrarJanelas) {
    cout << "=====================================================" << endl;
    cout << "   GALERIA 3x3 DE AMOSTRAS (PKLot) - tau = " << TAU_OTIMO << endl;
    cout << "=====================================================" << endl;

    ParkingPipeline pipeline(TAU_OTIMO);

    Mat mosaicoCor(3 * ALT_CELULA, 3 * LARG_CELULA, CV_8UC3, Scalar(0, 0, 0));
    Mat mosaicoBin(3 * ALT_CELULA, 3 * LARG_CELULA, CV_8UC3, Scalar(0, 0, 0));

    for (size_t i = 0; i < AMOSTRAS.size(); i++) {
        int linha = (int) i / 3;
        int coluna = (int) i % 3;
        cout << "Processando " << AMOSTRAS[i].patio << " / " << AMOSTRAS[i].clima << "..." << endl;

        pair<Mat, Mat> celulas = processarAmostra(AMOSTRAS[i], pipeline);
        Rect destino(coluna * LARG_CELULA, linha * ALT_CELULA, LARG_CELULA, ALT_CELULA);
        celulas.first.copyTo(mosaicoCor(destino));
        celulas.second.copyTo(mosaicoBin(destino));
    }

    // Salva automaticamente os mosaicos (usados como figuras do artigo)
    const string arquivoCor = "../graficos/galeria_exemplos.png";
    const string arquivoBin = "../graficos/galeria_binarizada.png";
    fs::create_directories("../graficos");
    bool okCor = imwrite(arquivoCor, mosaicoCor);
    bool okBin = imwrite(arquivoBin, mosaicoBin);
    if (okCor && okBin) {
        cout << "\n[SALVO] " << arquivoCor << "\n[SALVO] " << arquivoBin << endl;
    } else {
        cerr << "[ERRO] Nao foi possivel salvar os mosaicos em ../graficos/" << endl;
    }

    if (!mostrarJanelas) {
        return (okCor && okBin) ? 0 : 1;
    }

    const string janelaCor = "Galeria PKLot - Deteccao (verde = livre, vermelho = ocupada)";
    const string janelaBin = "Galeria PKLot - Imagens binarizadas (adaptiveThreshold + dilatacao)";

    // Janelas redimensionáveis; o mosaico interno mantém 1920x1080 para salvar em boa resolução
    namedWindow(janelaCor, WINDOW_NORMAL);
    namedWindow(janelaBin, WINDOW_NORMAL);
    resizeWindow(janelaCor, 1440, 810);
    resizeWindow(janelaBin, 1440, 810);
    moveWindow(janelaCor, 20, 20);
    moveWindow(janelaBin, 80, 80);
    imshow(janelaCor, mosaicoCor);
    imshow(janelaBin, mosaicoBin);

    cout << "\n[ATALHOS] 's' = salvar novamente | 'q' ou ESC = sair\n" << endl;

    while (true) {
        int tecla = waitKey(50) & 0xFF;
        if (tecla == 27 || tecla == 'q') break;

        if (tecla == 's') {
            imwrite(arquivoCor, mosaicoCor);
            imwrite(arquivoBin, mosaicoBin);
            cout << "[SALVO] " << arquivoCor << " e " << arquivoBin << endl;
        }

        // Encerra se o usuário fechar qualquer uma das janelas no botão X
        if (getWindowProperty(janelaCor, WND_PROP_VISIBLE) < 1 ||
            getWindowProperty(janelaBin, WND_PROP_VISIBLE) < 1) {
            break;
        }
    }

    destroyAllWindows();
    return 0;
}

// ============================================================================
int main(int argc, char **argv) {
    // Sem argumentos: comportamento original (benchmark completo).
    // --galeria: gera e salva os mosaicos 3x3 (deteccao + binarizadas) e abre as janelas.
    // --galeria --sem-janelas: apenas gera e salva os PNGs (sem abrir janelas).
    bool galeria = false;
    bool semJanelas = false;

    for (int i = 1; i < argc; i++) {
        string opcao = argv[i];
        if (opcao == "--galeria") {
            galeria = true;
        } else if (opcao == "--sem-janelas") {
            semJanelas = true;
        } else {
            cout << "Uso: " << argv[0] << " [--galeria] [--sem-janelas]\n"
                    << "  (sem argumentos)         avaliacao global do dataset completo (benchmark)\n"
                    << "  --galeria                salva os mosaicos 3x3 em ../graficos/ e exibe as janelas\n"
                    << "  --galeria --sem-janelas  apenas salva os mosaicos, sem abrir janelas" << endl;
            return (opcao == "--ajuda" || opcao == "--help") ? 0 : 1;
        }
    }

    if (galeria) {
        return executarGaleria(!semJanelas);
    }
    if (semJanelas) {
        cout << "[AVISO] --sem-janelas so tem efeito junto com --galeria." << endl;
        return 1;
    }
    return executarBenchmark();
}