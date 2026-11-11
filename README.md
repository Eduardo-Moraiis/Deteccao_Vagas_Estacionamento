# Smart Parking: Detecção e Monitoramento de Vagas com PDI Clássico em C++

[![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.cppreference.com/w/cpp/20)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x%20%2F%205.x-green.svg)](https://opencv.org/)
[![CMake](https://img.shields.io/badge/CMake-3.20%2B-red.svg)](https://cmake.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CEFET-MG](https://img.shields.io/badge/CEFET--MG-Vis%C3%A3o%20Computacional-darkblue.svg)](https://www.cefetmg.br/)

Sistema de detecção e contagem automática de vagas de estacionamento desenvolvido em **C++** e **OpenCV**, avaliado sobre a base **PKLot (UFPR/PUCPR)**.

O projeto adota uma abordagem estritamente baseada em **Processamento Digital de Imagens (PDI) clássico** e heurísticas determinísticas, sem redes neurais nem etapa de treinamento, visando execução em hardware de baixo custo (*Edge Computing*).

---

## 📌 Contexto e Motivação

Em estacionamentos de grande porte, a busca por vagas livres gera congestionamento interno, perda de tempo e emissão desnecessária de poluentes. Soluções com sensores por vaga (ultrassônicos ou magnéticos) têm custo elevado de instalação e manutenção.

Este projeto propõe reaproveitar **câmeras de vigilância (CCTV) já existentes** para monitorar dezenas de vagas simultaneamente por visão computacional.

---

## ⚙️ Por que PDI clássico?

1. **Edge Computing:** executa em CPU, sem GPU e sem nuvem.
2. **Tempo previsível:** custo linear no número de pixels, cerca de **21 FPS** em CPU com um único *thread* (inclui leitura do JPEG e do XML).
3. **Explicabilidade (*white-box*):** cada decisão decorre de propriedades observáveis da imagem, o que permite auditar os modos de falha.
4. **Sem treinamento:** não há risco de sobreajuste a uma câmera específica.

O custo dessa escolha é a exatidão: o método é inferior a classificadores treinados (veja a seção de comparação com o PKLot).

---

## 🔬 Pipeline Metodológico

### 1. PDI global (uma vez por quadro)
* **Tons de cinza:** `cvtColor` (BGR para cinza).
* **Filtro gaussiano:** $3 \times 3$, $\sigma = 1$, para atenuar ruído.
* **Limiarização adaptativa:** `ADAPTIVE_THRESH_GAUSSIAN_C` com `THRESH_BINARY_INV`, bloco $25 \times 25$, $C = 16$. Um pixel fica ativo quando é mais escuro que a média local em mais de $C$ níveis.
* **Dilatação:** elemento retangular $3 \times 3$, para conectar as arestas do veículo.

### 2. Decisão por vaga (nível de ROI)
* **Polígono da vaga:** quatro vértices lidos do XML da PKLot (`pugixml`).
* **Máscara convexa:** `fillConvexPoly` + `bitwise_and`, restringindo a contagem ao interior da vaga.
* **Característica:** número de pixels ativos (`cv::countNonZero`).
* **Regra:** se pixels $\ge \tau$, a vaga é **ocupada** (vermelho); caso contrário, **livre** (verde).

---

## 📊 Resultados

### 1. Calibração do limiar $\tau$ (UFPR04)

Varredura de $\tau = 700$ a $2500$ (passo 100) no pátio **UFPR04**, com **200 imagens por clima** (16.800 avaliações de vagas por valor de $\tau$).

* **$\tau < 900$:** recall alto ($\approx 96\%$), mas muitos falsos positivos (sombras duras e poças d'água).
* **$\tau > 900$:** o recall cai, principalmente no nublado, onde a luz difusa gera pouco contraste.
* **$\tau = 900$:** melhor compromisso, com **acurácia global de 85,81%** e **F1 médio de 82,37%** nesse subconjunto.

| Clima (UFPR04, 200 imagens) | VP | VN | FP | FN | Acurácia | Precisão | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Ensolarado | 1.681 | 2.932 | 702 | 285 | 82,38% | 70,54% | 85,50% | 77,31% |
| Nublado | 3.799 | 1.041 | 222 | 538 | 86,43% | 94,48% | 87,60% | 90,91% |
| Chuvoso | 1.191 | 3.772 | 463 | 174 | 88,62% | 72,01% | 87,25% | 78,90% |
| **Global** | **6.671** | **7.745** | **1.387** | **997** | **85,81%** | **82,79%** | **86,99%** | **82,37%** |

### 2. Benchmark em toda a base (τ = 900)

Todas as imagens processadas da PKLot: **12.416 imagens** e **719.528 decisões de vaga**.

| Pátio | Condição | Imagens | Vagas | Acurácia | Precisão | Recall | F1 | FPS |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| UFPR04 | Ensolarado | 2.098 | 58.744 | 86,63% | 84,73% | 92,19% | 88,31% | 21,5 |
| UFPR04 | Nublado | 1.408 | 39.424 | 88,31% | 74,51% | 91,67% | 82,21% | 21,9 |
| UFPR04 | Chuvoso | 285 | 7.980 | 88,90% | 76,94% | 89,04% | 82,55% | 22,2 |
| UFPR05 | Ensolarado | 2.500 | 100.000 | 78,39% | 79,75% | 83,73% | 81,69% | 21,4 |
| UFPR05 | Nublado | 1.426 | 57.040 | 79,00% | 81,48% | 83,51% | 82,48% | 21,7 |
| UFPR05 | Chuvoso | 226 | 9.040 | 75,56% | 85,45% | 76,72% | 80,85% | 21,7 |
| PUCPR | Ensolarado | 2.314 | 231.400 | 69,78% | 70,81% | 44,55% | 54,69% | 20,5 |
| PUCPR | Nublado | 1.328 | 132.800 | 77,53% | 69,50% | 52,66% | 59,92% | 20,7 |
| PUCPR | Chuvoso | 831 | 83.100 | 61,80% | 86,59% | 50,16% | 63,52% | 20,5 |
| **Total** | **Todas** | **12.416** | **719.528** | **74,89%** | **78,08%** | **64,22%** | **70,47%** | **21,2** |

Consolidado por pátio:

| Pátio | Vagas/imagem | Acurácia | Precisão | Recall | F1 | FP | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| UFPR04 (4º andar) | 28 | 87,42% | 81,52% | 91,90% | 86,40% | 9.613 | 3.736 |
| UFPR05 (5º andar) | 40 | 78,45% | 80,66% | 83,21% | 81,92% | 19.443 | 16.353 |
| PUCPR (10º andar) | 100 | 70,59% | 74,54% | 47,95% | 58,36% | 31.476 | 100.056 |

### 3. Comparação com o *baseline* do PKLot

O artigo da base (Almeida et al., 2015) treina SVMs com descritores de textura (LBP e LPQ). Não é uma comparação direta: o *baseline* treina e usa metade dos dias para teste, enquanto este projeto não treina e avalia todas as imagens com um único limiar calibrado no UFPR04. O cenário mais próximo é "treinar/calibrar no UFPR04 e testar nos demais pátios":

| Pátio de teste | Baseline (fusão) | Baseline (melhor único) | Este projeto | Diferença (fusão) |
| :--- | :---: | :---: | :---: | :---: |
| UFPR04 (mesmo pátio) | 99,64% | 99,55% | 87,42% | −12,22 p.p. |
| UFPR05 | 88,33% | 84,92% | 78,45% | −9,88 p.p. |
| PUCPR | 88,40% | 84,25% | 70,59% | −17,81 p.p. |

O *baseline* é superior em exatidão em todos os casos. A tendência qualitativa é a mesma: a PUCPR é o pátio mais difícil nos dois trabalhos.

---

## 🔍 Análise Crítica: onde o método funciona e onde falha

**Onde funciona melhor:** com a câmera mais próxima (UFPR04, 28 vagas por imagem), a acurácia chega a 87,42% e o recall a 91,90%. As vagas têm muitos pixels e o contraste entre o carro e o asfalto é claro.

**Modos de falha:**

1. **Sombras duras (sol, falso positivo):** a limiarização adaptativa ativa pixels mais escuros que a vizinhança; a borda de uma sombra no asfalto gera um gradiente semelhante à borda de um veículo.
2. **Reflexos em pavimento molhado (chuva, falso positivo):** poças refletem o céu e as luminárias, e o impacto das gotas gera ruído de alta frequência que a dilatação agrupa.
3. **Textura do piso (PUCPR, falso positivo):** nas imagens binarizadas da PUCPR, o piso de bloquete sob pouca iluminação gera uma nuvem de pixels ativos que se assemelha a um veículo. É uma observação qualitativa ainda não quantificada por pátio.
4. **Altura da câmera e escala da vaga (falso negativo):** na PUCPR (10º andar, 100 vagas em $1280 \times 720$) cada vaga tem poucos pixels, e um carro raramente atinge $\tau = 900$. O recall cai para 47,95%, e 83% dos falsos negativos de todo o benchmark ocorrem nesse pátio.

**Achado central:** o limiar absoluto $\tau$ não é invariante à escala da cena. A sua transferência entre câmeras exigiria $\tau_i \propto \text{Área}_i$ (limiar proporcional à área do polígono da vaga).

### Limitações conhecidas

* O subconjunto de calibração (200 imagens por clima) faz parte do UFPR04 avaliado no benchmark, então os números desse pátio são otimistas.
* Não há divisão treino/teste nem comparação direta com métodos supervisionados.
* A condição chuvosa tem poucas imagens (285, 226 e 831 por pátio).
* **Em verificação:** na PUCPR Sunny, o número de vagas livres contadas é muito maior que o da Tabela 1 do artigo do PKLot (231.400 vagas contra 208.433). Uma hipótese é que `<space>` sem o atributo `occupied` esteja sendo lido como livre. Enquanto isso não for verificado, trate os números da PUCPR Sunny e o total com cautela.

---

## 📁 Estrutura do Repositório

* `CMakeLists.txt`: configuração de compilação (`pugixml` via `FetchContent`).
* `include/` e `src/`: código C++ (`DatasetParser`, `ParkingPipeline`, `Evaluator`, `main.cpp`).
* `scripts/visualizar_resultados.py`: gráficos da calibração de $\tau$ (lê `historico_experimentos.csv`).
* `scripts/visualizar_benchmark_global.py`: gráficos e tabelas LaTeX do benchmark completo (lê `historico_final_tau_900.csv`).
* `historico_experimentos.csv`: varredura de $\tau$ no UFPR04.
* `historico_final_tau_900.csv`: benchmark completo com $\tau = 900$.
* `graficos/`: figuras em 300 DPI (calibração, benchmark e galeria de exemplos).
* `relatorio_tex/`: artigo em LaTeX (abnTeX2).
* `relatorio.md`: relatório técnico de desenvolvimento.
* `data/`: base PKLot (não versionada).

---

## 🚀 Como Compilar e Executar

### Pré-requisitos
* Compilador com suporte a **C++20** (MSVC 2019/2022, GCC ou Clang);
* **CMake 3.20+**;
* **OpenCV 4.x ou 5.x** (com o módulo `highgui` para a galeria);
* **Base PKLot** em `data/PKLot/PKLot/` (pastas `UFPR04`, `UFPR05` e `PUCPR`). A base é distribuída pelos autores sob solicitação: <http://web.inf.ufpr.br/vri/parking-lot-database>;
* Python 3.9+ com `pandas`, `matplotlib` e `seaborn`.

### 1. Compilação

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 2. Execução

O executável procura a base em `../data/PKLot/PKLot/`, relativo à pasta de execução (por exemplo, `cmake-build-*`).

```bash
# Benchmark completo (padrão): processa todas as imagens e grava ../historico_final_tau_900.csv
./projeto_estacionamento

# Galeria 3x3: uma amostra por pátio e clima, com caixas, placar e janela das imagens binarizadas
./projeto_estacionamento --galeria

# Apenas gera e salva os mosaicos em ../graficos/, sem abrir janelas
./projeto_estacionamento --galeria --sem-janelas
```

Na galeria, as caixas são **vermelhas** (ocupada) ou **verdes** (livre) segundo a predição, e a faixa inferior de cada célula mostra o total de vagas, as contagens preditas e o gabarito. Os mosaicos são salvos em `../graficos/galeria_exemplos.png` e `../graficos/galeria_binarizada.png`. Teclas: `s` salva de novo; `q` ou ESC sai.

### 3. Gráficos e tabelas (Python)

```bash
pip install pandas matplotlib seaborn

# Calibração de tau (UFPR04)
python scripts/visualizar_resultados.py

# Benchmark completo: figuras benchmark_fig1 a benchmark_fig4 e tabelas .tex (booktabs)
python scripts/visualizar_benchmark_global.py --csv historico_final_tau_900.csv --saida graficos
```

---

## 📚 Referências

1. **ALMEIDA, P. R. L. et al.** PKLot – A robust dataset for parking lot classification. *Expert Systems with Applications*, v. 42, n. 11, p. 4937-4949, 2015.
2. **GONZALEZ, R. C.; WOODS, R. E.** *Processamento Digital de Imagens*. 3. ed. São Paulo: Pearson, 2010.
3. **BRADLEY, D.; ROTH, G.** Adaptive thresholding using the integral image. *Journal of Graphics Tools*, v. 12, n. 2, p. 13-21, 2007.
4. **BRADSKI, G.** The OpenCV library. *Dr. Dobb's Journal of Software Tools*, 2000. <https://opencv.org/>

---

## 👨‍💻 Autores e Vínculo Acadêmico

* **Instituição:** Centro Federal de Educação Tecnológica de Minas Gerais (CEFET-MG)
* **Disciplina:** Visão Computacional
* **Docente responsável:** Profª Drª Natália Batista
* **Desenvolvedor:** Eduardo Morais Silva Martins