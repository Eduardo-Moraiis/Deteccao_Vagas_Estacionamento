#pragma once

#include <vector>
#include <string>
#include <opencv2/opencv.hpp>

using namespace std;
using namespace cv;

// Estrutura que representa uma vaga individual
struct Vaga {
  int id;
  bool ocupadaReal;          // Rótulo do dataset (0 = Livre, 1 = Ocupada)
  bool ocupadaPredita = false; // Predição do nosso algoritmo de PDI
  int pixelsBrancos = 0;     // Quantidade de pixels detectados na vaga
  vector<Point> contorno;    // 4 vértices do polígono da vaga
  Rect caixaDelimitadora;    // Bounding Box para recorte (ROI)
};

class DatasetParser {
public:
  // Carrega todas as vagas a partir do XML da PKLot
  static vector<Vaga> carregarVagasXML(const string& caminhoXML);
};