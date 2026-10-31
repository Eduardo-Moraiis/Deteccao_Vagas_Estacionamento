#include "Evaluator.hpp"
#include "DatasetParser.hpp"
#include <iostream>
#include <filesystem>
#include <chrono>
#include <iomanip>
#include <fstream>
#include <ctime>

namespace fs = std::filesystem;

MetricasClima Evaluator::avaliarClima(const string &pastaClima,
                                      const string &nomeClima,
                                      ParkingPipeline &pipeline,
                                      int maxImagens) {
    MetricasClima m;
    m.clima = nomeClima;

    if (!fs::exists(pastaClima)) {
        cerr << "[AVISO] Pasta nao encontrada: " << pastaClima << endl;
        return m;
    }

    cout << "\n=======================================================" << endl;
    cout << "Iniciando avaliacao para o clima: " << nomeClima << endl;
    cout << "Pasta: " << pastaClima << endl;
    cout << "=======================================================" << endl;

    auto inicioTempo = chrono::high_resolution_clock::now();

    // Itera recursivamente por todas as pastas de data dentro do clima
    for (const auto &entry: fs::recursive_directory_iterator(pastaClima)) {
        if (entry.is_regular_file() && entry.path().extension() == ".jpg") {
            string caminhoJPG = entry.path().string();

            // Procura o XML de mesmo nome
            fs::path caminhoXMLPath = entry.path();
            caminhoXMLPath.replace_extension(".xml");

            if (!fs::exists(caminhoXMLPath)) {
                continue;
            }

            // 1. Carrega imagem e XML
            Mat frame = imread(caminhoJPG);
            if (frame.empty()) continue;

            vector<Vaga> vagas = DatasetParser::carregarVagasXML(caminhoXMLPath.string());
            if (vagas.empty()) continue;

            // 2. Executa PDI e Decisão
            Mat binaria = pipeline.processarImagemPDI(frame);
            pipeline.classificarVagas(binaria, vagas);

            // 3. Atualiza matriz de confusão
            for (const auto &v: vagas) {
                m.totalVagas++;
                if (v.ocupadaReal && v.ocupadaPredita) {
                    m.vp++;
                } else if (!v.ocupadaReal && !v.ocupadaPredita) {
                    m.vn++;
                } else if (!v.ocupadaReal && v.ocupadaPredita) {
                    m.fp++; // Falso alarme
                } else if (v.ocupadaReal && !v.ocupadaPredita) {
                    m.fn++; // Perdeu o carro
                }
            }

            m.totalImagens++;

            // Feedback de progresso no console a cada 100 imagens
            if (m.totalImagens % 100 == 0) {
                cout << "  Processadas " << m.totalImagens << " imagens (" << m.totalVagas << " vagas analisadas)..." <<
                        endl;
            }

            // Limite opcional para testes rápidos
            if (maxImagens > 0 && m.totalImagens >= maxImagens) {
                break;
            }
        }
    }

    auto fimTempo = chrono::high_resolution_clock::now();
    chrono::duration<double> duracao = fimTempo - inicioTempo;
    m.tempoTotalSegundos = duracao.count();

    cout << "Concluido clima " << nomeClima << "! Total: " << m.totalImagens
            << " imagens em " << fixed << setprecision(2) << m.tempoTotalSegundos
            << "s (" << m.fps() << " FPS)." << endl;

    return m;
}

void Evaluator::imprimirTabelaComparativa(const vector<MetricasClima> &resultados) {
    cout << "\n\n";
    cout <<
            "========================================================================================================\n";
    cout <<
            "                               TABELA COMPARATIVA DE RESULTADOS (PKLot)                                 \n";
    cout <<
            "========================================================================================================\n";
    cout << left << setw(10) << "Clima"
            << setw(10) << "Imagens"
            << setw(10) << "Vagas"
            << setw(8) << "VP"
            << setw(8) << "VN"
            << setw(8) << "FP"
            << setw(8) << "FN"
            << setw(12) << "Acuracia"
            << setw(12) << "Precisao"
            << setw(10) << "Recall"
            << setw(10) << "F1-Score"
            << setw(8) << "FPS" << "\n";
    cout <<
            "--------------------------------------------------------------------------------------------------------\n";

    for (const auto &r: resultados) {
        cout << left << setw(10) << r.clima
                << setw(10) << r.totalImagens
                << setw(10) << r.totalVagas
                << setw(8) << r.vp
                << setw(8) << r.vn
                << setw(8) << r.fp
                << setw(8) << r.fn
                << fixed << setprecision(2)
                << setw(11) << to_string(r.acuracia()).substr(0, 5) + "%"
                << setw(11) << to_string(r.precisao()).substr(0, 5) + "%"
                << setw(10) << to_string(r.recall()).substr(0, 5) + "%"
                << setw(10) << to_string(r.f1Score()).substr(0, 5) + "%"
                << setw(8) << setprecision(1) << r.fps() << "\n";
    }
    cout <<
            "========================================================================================================\n";
}

void Evaluator::salvarHistoricoCSV(const string &caminhoArquivo,
                                   int limiarTau,
                                   const vector<MetricasClima> &resultados) {
    bool arquivoJaExiste = fs::exists(caminhoArquivo);
    ofstream arquivo(caminhoArquivo, ios::app); // Abre em modo append (não sobrescreve)

    if (!arquivo.is_open()) {
        cerr << "[ERRO] Nao foi possivel abrir o arquivo para gravacao: " << caminhoArquivo << endl;
        return;
    }

    // Se o arquivo for criado agora, escreve o cabeçalho separado por ponto e vírgula (formato Excel Brasil)
    if (!arquivoJaExiste) {
        arquivo <<
                "DataHora;Limiar_Tau;Clima;Imagens;Vagas;VP;VN;FP;FN;Acuracia_Porc;Precisao_Porc;Recall_Porc;F1_Score_Porc;Taxa_Erro_Porc;FPS\n";
    }

    // Obtém a data e hora do experimento
    auto agora = chrono::system_clock::to_time_t(chrono::system_clock::now());
    char bufferData[30];
    tm ltm;
    localtime_s(&ltm, &agora); // Função segura no Windows MSVC
    strftime(bufferData, sizeof(bufferData), "%Y-%m-%d %H:%M:%S", &ltm);

    // Grava as linhas de cada clima com o limiar correspondente
    for (const auto &r: resultados) {
        arquivo << bufferData << ";"
                << limiarTau << ";"
                << r.clima << ";"
                << r.totalImagens << ";"
                << r.totalVagas << ";"
                << r.vp << ";"
                << r.vn << ";"
                << r.fp << ";"
                << r.fn << ";"
                << fixed << setprecision(2)
                << r.acuracia() << ";"
                << r.precisao() << ";"
                << r.recall() << ";"
                << r.f1Score() << ";"
                << r.taxaErro() << ";"
                << setprecision(1) << r.fps() << "\n";
    }

    arquivo.close();
    cout << "\n[HISTORICO] Resultados salvos com sucesso em: " << caminhoArquivo << endl;
}
