#pragma once

#include <vector>
#include <opencv2/opencv.hpp>
#include "DatasetParser.hpp"

using namespace std;
using namespace cv;

class ParkingPipeline {
private:
    int limiarTau; // Limiar de pixels brancos para decidir se está ocupada

public:
    // Construtor: define o valor inicial de corte (tau)
    ParkingPipeline(int limiar = 700);

    // Permite calibrar o limiar tau em tempo de execução
    void definirLimiar(int novoLimiar);
    int obterLimiar() const;

    // Aplica o pré-processamento de PDI na imagem inteira
    Mat processarImagemPDI(const Mat& entrada);

    // Avalia o estado de cada vaga sobre a imagem binarizada
    void classificarVagas(const Mat& imagemBinarizada, vector<Vaga>& vagas);

    // Desenha as caixas, textos e placar na imagem final
    void renderizarVisualizacao(Mat& imagemOriginal, const vector<Vaga>& vagas);
};