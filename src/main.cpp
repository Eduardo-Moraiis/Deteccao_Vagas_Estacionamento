#include <iostream>
#include <vector>
#include "ParkingPipeline.hpp"
#include "Evaluator.hpp"

using namespace std;

int main() {
    cout << "=====================================================" << endl;
    cout << "      AVALIACAO DE DESEMPENHO PKLot POR CLIMA        " << endl;
    cout << "=====================================================" << endl;

    for(int tau=700; tau<=2500; tau+=100) {
        cout << "=====================================================" << endl;
        cout << "      TAU: " << tau << "      " << endl;
        cout << "=====================================================" << endl;
        int tauTeste = tau; // Experimente variar: 700, 900, 1100, 1300...
        ParkingPipeline pipeline(tauTeste);

        string baseUFPR04 = "../data/PKLot/PKLot/UFPR04/";
        vector<MetricasClima> resultados;
        int limitePorClima = 200;

        // 1. Executa as três condições
        resultados.push_back(Evaluator::avaliarClima(baseUFPR04 + "Sunny", "Sunny", pipeline, limitePorClima));
        resultados.push_back(Evaluator::avaliarClima(baseUFPR04 + "Cloudy", "Cloudy", pipeline, limitePorClima));
        resultados.push_back(Evaluator::avaliarClima(baseUFPR04 + "Rainy", "Rainy", pipeline, limitePorClima));

        // 2. Imprime no console a tabela bonita
        Evaluator::imprimirTabelaComparativa(resultados);

        // 3. Salva no arquivo CSV histórico na raiz do projeto
        Evaluator::salvarHistoricoCSV("../historico_experimentos.csv", pipeline.obterLimiar(), resultados);
    }

    return 0;
}