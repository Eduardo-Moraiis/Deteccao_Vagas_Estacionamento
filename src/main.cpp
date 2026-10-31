#include <iostream>
#include <opencv2/opencv.hpp>

using namespace std;
using namespace cv;

int main() {
    cout << "OpenCV carregado na versao: " << CV_VERSION << endl;

    // Cria uma imagem preta de 300x500
    Mat tela = Mat::zeros(300, 500, CV_8UC3);

    // Desenha um retangulo verde simulando uma vaga livre
    rectangle(tela, Point(50, 50), Point(200, 250), Scalar(0, 255, 0), 3);
    putText(tela, "LIVRE", Point(70, 160), FONT_HERSHEY_SIMPLEX, 0.9, Scalar(0, 255, 0), 2);

    // Desenha um retangulo vermelho simulando uma vaga ocupada
    rectangle(tela, Point(250, 50), Point(400, 250), Scalar(0, 0, 255), 3);
    putText(tela, "OCUPADA", Point(260, 160), FONT_HERSHEY_SIMPLEX, 0.7, Scalar(0, 0, 255), 2);

    imshow("Teste Inicial - Smart Parking", tela);
    waitKey(0); // Espera qualquer tecla para fechar

    return 0;
}