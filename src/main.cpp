#include <iostream>
#include <vector>
#include <string>
#include "ParkingPipeline.hpp"
#include "Evaluator.hpp"

using namespace std;

int main() {
    cout << "=====================================================" << endl;
    cout << "   AVALIACAO GLOBAL DO DATASET COMPLETO (PKLot)      " << endl;
    cout << "=====================================================" << endl;

    // limiar ótimo comprovado nos experimentos preliminares
    int tauOtimo = 900;
    ParkingPipeline pipeline(tauOtimo);

    // O valor -1 desativa qualquer limite e processa TODAS as fotos
    int limitePorClima = -1;

    // Lista dos 3 pátios da base PKLot
    vector<string> patios = {"UFPR04", "UFPR05", "PUCPR"};
    vector<string> climas = {"Sunny", "Cloudy", "Rainy"};

    vector<MetricasClima> resultadosGlobais;

    string caminhoBasePKLot = "../data/PKLot/PKLot/";

    // Percorre cada pátio e cada clima
    for (const auto& patio : patios) {
        cout << "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" << endl;
        cout << "Iniciando processamento do patio: " << patio << endl;
        cout << ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" << endl;

        for (const auto& clima : climas) {
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