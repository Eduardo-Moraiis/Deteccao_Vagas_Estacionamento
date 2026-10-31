# Smart Parking: Detecção e Monitoramento de Vagas com PDI Clássico em C++

[![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.cppreference.com/w/cpp/20)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x%20%2F%205.x-green.svg)](https://opencv.org/)
[![CMake](https://img.shields.io/badge/CMake-3.20%2B-red.svg)](https://cmake.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CEFET-MG](https://img.shields.io/badge/CEFET--MG-Vis%C3%A3o%20Computacional-darkblue.svg)](https://www.cefetmg.br/)

Sistema de monitoramento inteligente e contagem automática de vagas de estacionamento em tempo real desenvolvido em **C++** e **OpenCV**, validado sobre o conjunto de dados acadêmico **PKLot (UFPR/PUCPR)**.

O projeto adota uma abordagem estritamente fundamentada em **Processamento Digital de Imagens (PDI) clássico** e heurísticas determinísticas de Visão Computacional, dispensando redes neurais profundas para viabilizar a execução em hardware embarcado de baixo custo (*Edge Computing*).

---

## 📌 Contexto e Motivação

Em estacionamentos de grande porte, a busca por vagas livres gera congestionamento interno, perda de tempo e emissão desnecessária de poluentes (*cruising for parking*). As soluções comerciais convencionais frequentemente empregam sensores físicos dedicados (ultrassônicos ou magnéticos) instalados em cada vaga individual, o que impõe elevados custos de implantação, infraestrutura elétrica e manutenção contínua.

Este projeto propõe uma alternativa escalável: **o reaproveitamento de câmeras de vigilância (CCTV) já existentes** para monitorar dezenas de vagas simultaneamente através de técnicas de visão computacional.

---

## ⚙️ Diferencial de Engenharia: Por que PDI Clássico?

Ao contrário da tendência contemporânea de aplicar redes neurais convolucionais (CNNs/YOLO) indiscriminadamente, a opção consciente por PDI clássico apoia-se em quatro pilares de engenharia:

1. **Aderência a Sistemas Embarcados (*Edge Computing*):** Dispensa aceleradores gráficos dedicados (GPUs) e conexão com a nuvem, operando com consumo energético mínimo em microcomputadores e chips automotivos (ex.: Raspberry Pi).
2. **Determinismo e Tempo Real Estrito:** Taxa de processamento constante de **~22 FPS** por lote de inferência em CPU convencional.
3. **Interpretabilidade Total (*White-Box*):** As decisões do algoritmo são 100% explicáveis geometricamente e radiometricamente, permitindo auditoria direta dos modos de falha.
4. **Sem Dependência de Treinamento:** Não requer GPUs para longas rotinas de treinamento nem incorre em risco de *overfitting* espacial.

---

## 🔬 Pipeline Metodológico

O fluxo de processamento é dividido em duas macroetapas bem definidas:

### 1. Processamento Digital de Imagens (Nível Global)
* **Conversão de Cores:** Conversão de BGR para Escala de Cinza (redução de dimensionalidade matricial de 3 para 1 canal).
* **Filtragem Espacial:** Filtro Gaussiano ($3 \times 3$, $\sigma = 1$) para atenuação de ruídos de alta frequência do sensor da câmera.
* **Segmentação:** Limiarização Adaptativa (`ADAPTIVE_THRESH_GAUSSIAN_C` com `THRESH_BINARY_INV`, bloco $25 \times 25$, $C = 16$), tornando a binarização resiliente a gradientes de luminosidade na cena.
* **Morfologia Matemática:** Dilatação com elemento estruturante retangular ($3 \times 3$) para consolidar as arestas e texturas do veículo contra o piso uniforme.

### 2. Visão Computacional e Decisão (Nível de ROI)
* **Mapeamento de Regiões de Interesse (ROIs):** Extração das coordenadas poligonais de cada vaga a partir dos arquivos descritores XML da PKLot.
* **Isolamento Espacial:** Aplicação de máscara convexa (`fillConvexPoly` + `bitwise_and`), eliminando ruídos e faixas de trânsito externas ao perímetro da vaga.
* **Extração de Atributos:** Contagem da densidade de pixels brancos/ativos (`cv::countNonZero`).
* **Classificador Determinístico:** Regra por limiar de decisão ($\tau$): se $\text{Pixels} \ge \tau$, a vaga é rotulada como **Ocupada (Vermelho)**; caso contrário, **Livre (Verde)**.

---

## 📊 Resultados Experimentais e Calibração

Os experimentos foram conduzidos sobre o subconjunto **UFPR04** do dataset PKLot (28 vagas por tomada), avaliando **200 imagens por condição climática** (totalizando **16.800 avaliações de vagas** por rodada de teste).

### Calibração do Hiperparâmetro $\tau$ (Varredura de 700 a 2500)
Foi conduzida uma varredura empírica sistemática do limiar $\tau$ com passo de 100 pixels para identificar a zona de operação ideal:

* **$\tau < 900$ (Alta Sensibilidade):** Recall elevado ($\approx 96\%$), porém com alto índice de Falsos Positivos ($FP$) provocados por sombras duras de árvores e reflexos de poças d'água.
* **$\tau > 900$ (Baixa Sensibilidade):** Queda drástica de revocação no cenário nublado, pois a iluminação difusa gera texturas suaves que não atingem limiares elevados ($FN$ expressivos).
* **$\mathbf{\tau = 900}$ (Ponto Ótimo):** Estabeleceu o melhor equilíbrio (*trade-off*), maximizando a Acurácia Global e o F1-Score Médio.

### Desempenho Quantitativo na Configuração Ótima ($\tau = 900$)

| Condição Climática | Imagens | Vagas Avaliadas | VP | VN | FP | FN | Acurácia | Precisão | Recall | F1-Score | FPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ensolarado (`Sunny`)** | 200 | 5.600 | 1.681 | 2.932 | 702 | 285 | **82,38%** | 70,54% | 85,50% | 77,31% | 22,0 |
| **Nublado (`Cloudy`)** | 200 | 5.600 | 3.799 | 1.041 | 222 | 538 | **86,43%** | 94,48% | 87,60% | **90,91%** | 21,8 |
| **Chuvoso (`Rainy`)** | 200 | 5.600 | 1.191 | 3.772 | 463 | 174 | **88,62%** | 72,01% | 87,25% | 78,90% | 22,4 |
| **MÉDIA / GLOBAL** | **600** | **16.800** | **6.671** | **7.745** | **1.387** | **997** | **85,81%** | **82,79%** | **86,99%** | **82,37%** | **22,1** |

---

## 🔍 Análise Crítica: Onde o Método Brilha e Onde Falha?

Conforme exigido na avaliação metodológica da disciplina:

* **Onde o método funciona melhor:** No cenário **Nublado (`Cloudy`)**, com **F1-Score de 90,91%**. A ausência de luz solar direta elimina sombras duras e reflexos especulares; o asfalto cinza uniforme contrapõe-se nitidamente à descontinuidade dos veículos.
* **Onde o método apresenta limitações:**
    * **Sombras Duras (`Sunny`):** Sombras projetadas de árvores, postes ou veículos adjacentes sobre o asfalto claro criam bordas abruptas que a limiarização adaptativa interpreta como descontinuidade estrutural, elevando os Falsos Positivos ($FP = 702$).
    * **Reflexos Especulares (`Rainy`):** O asfalto molhado atua como espelho d'água, refletindo claridade do céu e iluminação artificial, além de gerar textura pelo impacto de gotas de chuva ($FP = 463$).

---

## 📁 Estrutura do Repositório

* `CMakeLists.txt`: Configuração modular de compilação com CMake.
* `.gitignore`: Regras para ignorar pastas de build, ambientes virtuais e datasets.
* `historico_experimentos.csv`: Log consolidado de todas as baterias de teste executadas.
* `include/DatasetParser.hpp`: Interface do leitor de XML via pugixml.
* `include/Evaluator.hpp`: Interface de métricas e benchmarking estatístico.
* `include/ParkingPipeline.hpp`: Interface do pipeline de PDI e classificação.
* `src/DatasetParser.cpp`: Implementação da extração de ROIs e anotações.
* `src/Evaluator.cpp`: Execução em lote e cálculo de matriz de confusão.
* `src/ParkingPipeline.cpp`: Implementação dos operadores clássicos do OpenCV.
* `src/main.cpp`: Ponto de entrada e orquestrador dos testes.
* `scripts/visualizar_resultados.py`: Script Python para geração automática de gráficos e tabelas LaTeX.
* `graficos/`: Diretório com as figuras científicas geradas em 300 DPI (`fig1` a `fig4`).

---

## 🚀 Como Compilar e Executar

### Pré-requisitos
* Compilador C++ com suporte a **C++20** (MSVC 2019/2022 no Windows ou GCC/Clang no Linux);
* **CMake 3.20+**;
* **OpenCV 4.x ou 5.x** instalado e referenciado no ambiente (`OPENCV_DIR`);
* Python 3.9+ com `pandas`, `matplotlib`, `seaborn` e `tabulate`.

### 1. Compilação do Núcleo em C++
Abra o projeto no **CLion** ou compile via linha de comando:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
./build/projeto_estacionamento
```

*Nota: A biblioteca `pugixml` é baixada e compilada automaticamente pelo CMake via `FetchContent`.*

### 2. Geração dos Gráficos e Tabelas (Python)
Para processar o arquivo `historico_experimentos.csv` e salvar as figuras:

```bash
pip install pandas matplotlib seaborn tabulate
python scripts/visualizar_resultados.py
```

As imagens são salvas automaticamente no diretório `graficos/` em 300 DPI, prontas para diagramação em LaTeX / Overleaf.

---

## 📚 Referências

1. **ALMEIDA, P. et al.** PKLot – A robust dataset for parking lot classification. *Expert Systems with Applications*, v. 42, n. 11, p. 4937-4949, 2015.
2. **GONZALEZ, R. C.; WOODS, R. E.** *Processamento Digital de Imagens*. 3. ed. Pearson, 2010.
3. **OPENCV.** *Open Source Computer Vision Library*. Disponível em: https://opencv.org/.

---

## 👨‍💻 Autores e Vínculo Acadêmico

* **Instituição:** Centro Federal de Educação Tecnológica de Minas Gerais (CEFET-MG)
* **Disciplina:** Visão Computacional
* **Docente Responsável:** Profª Drª Natália Batista
* **Desenvolvedor:** Eduardo Morais Silva Martins