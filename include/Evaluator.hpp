#pragma once

#include <string>
#include <vector>
#include "ParkingPipeline.hpp"

using namespace std;

struct MetricasClima {
    string clima;
    int totalImagens = 0;
    int totalVagas = 0;
    int vp = 0;
    int vn = 0;
    int fp = 0;
    int fn = 0;
    double tempoTotalSegundos = 0.0;

    double acuracia() const {
        return (totalVagas > 0) ? (double) (vp + vn) / totalVagas * 100.0 : 0.0;
    }

    double precisao() const {
        return (vp + fp > 0) ? (double) vp / (vp + fp) * 100.0 : 0.0;
    }

    double recall() const {
        return (vp + fn > 0) ? (double) vp / (vp + fn) * 100.0 : 0.0;
    }

    double f1Score() const {
        double p = precisao();
        double r = recall();
        return (p + r > 0.0) ? 2.0 * (p * r) / (p + r) : 0.0;
    }

    double taxaErro() const {
        return (totalVagas > 0) ? (double) (fp + fn) / totalVagas * 100.0 : 0.0;
    }

    double fps() const {
        return (tempoTotalSegundos > 0.0) ? (double) totalImagens / tempoTotalSegundos : 0.0;
    }
};

class Evaluator {
public:
    static MetricasClima avaliarClima(const string &pastaClima,
                                      const string &nomeClima,
                                      ParkingPipeline &pipeline,
                                      int maxImagens = -1);

    static void imprimirTabelaComparativa(const vector<MetricasClima> &resultados);

    static void salvarHistoricoCSV(const string &caminhoArquivo, int limiarTau,
                                   const vector<MetricasClima> &resultados);
};
