import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 13,
    }
)

PASTA_GRAFICOS = "graficos"
os.makedirs(PASTA_GRAFICOS, exist_ok=True)

ARQUIVO_CSV = "historico_final_tau_900.csv"
if not os.path.exists(ARQUIVO_CSV):
    if os.path.exists(os.path.join("..", ARQUIVO_CSV)):
        ARQUIVO_CSV = os.path.join("..", ARQUIVO_CSV)

# Tenta carregar do CSV; caso não ache, usa os dados do benchmark executado
if os.path.exists(ARQUIVO_CSV):
    df_raw = pd.read_csv(ARQUIVO_CSV, sep=";")
    # Filtra as linhas que contêm os pátios (UFPR04, UFPR05, PUCPR)
    df = df_raw[df_raw["Clima"].str.contains("_", na=False)].copy()
    if df.empty:
        df = df_raw.copy()
else:
    df = pd.DataFrame()

# Se por algum motivo o CSV não tiver as linhas completas, carrega direto os dados da rodada:
if len(df) < 9:
    dados_benchmark = """DataHora;Limiar_Tau;Clima;Imagens;Vagas;VP;VN;FP;FN;Acuracia_Porc;Precisao_Porc;Recall_Porc;F1_Score_Porc;Taxa_Erro_Porc;FPS
2026-10-31 11:29:43;900;UFPR04_Sunny;2098;58744;29658;21232;5343;2511;86.63;84.73;92.19;88.31;13.37;21.5
2026-10-31 11:29:43;900;UFPR04_Cloudy;1408;39424;10646;24169;3642;967;88.31;74.51;91.67;82.21;11.69;21.9
2026-10-31 11:29:43;900;UFPR04_Rainy;285;7980;2095;4999;628;258;88.90;76.94;89.04;82.55;11.10;22.2
2026-10-31 11:29:43;900;UFPR05_Sunny;2500;100000;48214;30175;12241;9370;78.39;79.75;83.73;81.69;21.61;21.4
2026-10-31 11:29:43;900;UFPR05_Cloudy;1426;57040;28196;16868;6408;5568;79.00;81.48;83.51;82.48;21.00;21.7
2026-10-31 11:29:43;900;UFPR05_Rainy;226;9040;4663;2168;794;1415;75.56;85.45;76.72;80.85;24.44;21.7
2026-10-31 11:29:43;900;PUCPR_Sunny;2314;231400;42212;119248;17404;52536;69.78;70.81;44.55;54.69;30.22;20.5
2026-10-31 11:29:43;900;PUCPR_Cloudy;1328;132800;22308;80646;9791;20055;77.53;69.50;52.66;59.92;22.47;20.7
2026-10-31 11:29:43;900;PUCPR_Rainy;831;83100;27640;23714;4281;27465;61.80;86.59;50.16;63.52;38.20;20.5"""
    import io

    df = pd.read_csv(io.StringIO(dados_benchmark), sep=";")

# Separa a coluna Clima em "Patio" e "Condicao"
df[["Patio", "Condicao"]] = df["Clima"].str.split("_", expand=True)
df["Condicao_PT"] = df["Condicao"].replace(
    {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Rainy": "Chuvoso"}
)

print(f"[OK] Analisando {len(df)} conjuntos de dados da base PKLot completa.")
print(f"Total de Vagas Processadas: {df['Vagas'].sum():,} | Imagens: {df['Imagens'].sum():,}")


# ==============================================================================
# FIGURA 1: Comparativo de Acurácia e F1 por Pátio e Clima
# ==============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))

sns.barplot(
    data=df,
    x="Patio",
    y="Acuracia_Porc",
    hue="Condicao_PT",
    palette="Blues_d",
    ax=axes[0],
    edgecolor="black",
)
axes[0].set_title(
    "Acurácia (%) por Pátio e Condição Climática", fontweight="bold"
)
axes[0].set_ylabel("Acurácia (%)")
axes[0].set_xlabel("Pátio Avaliado")
axes[0].set_ylim(40, 100)
for p in axes[0].patches:
    h = p.get_height()
    if h > 0:
        axes[0].annotate(
            f"{h:.1f}%",
            (p.get_x() + p.get_width() / 2.0, h),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            xytext=(0, 2),
            textcoords="offset points",
        )

sns.barplot(
    data=df,
    x="Patio",
    y="F1_Score_Porc",
    hue="Condicao_PT",
    palette="Reds_d",
    ax=axes[1],
    edgecolor="black",
)
axes[1].set_title(
    "F1-Score (%) por Pátio e Condição Climática", fontweight="bold"
)
axes[1].set_ylabel("F1-Score (%)")
axes[1].set_xlabel("Pátio Avaliado")
axes[1].set_ylim(40, 100)
for p in axes[1].patches:
    h = p.get_height()
    if h > 0:
        axes[1].annotate(
            f"{h:.1f}%",
            (p.get_x() + p.get_width() / 2.0, h),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            xytext=(0, 2),
            textcoords="offset points",
        )

plt.suptitle(
    "Benchmark Completo do PDI Clássico nos 3 Pátios da Base PKLot ($\\tau = 900$)",
    fontweight="bold",
    fontsize=13,
)
plt.tight_layout()
caminho_fig1 = os.path.join(PASTA_GRAFICOS, "benchmark_fig1_patio_clima.png")
plt.savefig(caminho_fig1, dpi=300)
plt.close()
print(f"[SALVO] {caminho_fig1}")


# ==============================================================================
# FIGURA 2: O Efeito da Altura da Câmera (Recall e Falsos Negativos)
# ==============================================================================
resumo_patio = (
    df.groupby("Patio")
    .agg(
        {
            "Vagas": "sum",
            "VP": "sum",
            "VN": "sum",
            "FP": "sum",
            "FN": "sum",
        }
    )
    .reset_index()
)

resumo_patio["Acuracia"] = (
        (resumo_patio["VP"] + resumo_patio["VN"]) / resumo_patio["Vagas"] * 100.0
)
resumo_patio["Recall"] = (
        resumo_patio["VP"] / (resumo_patio["VP"] + resumo_patio["FN"]) * 100.0
)
resumo_patio["Precisao"] = (
        resumo_patio["VP"] / (resumo_patio["VP"] + resumo_patio["FP"]) * 100.0
)
resumo_patio["F1"] = (
        2
        * (resumo_patio["Precisao"] * resumo_patio["Recall"])
        / (resumo_patio["Precisao"] + resumo_patio["Recall"])
)

# Descrição física de cada pátio para o gráfico
resumo_patio["Descricao"] = [
    "PUCPR\n(10º Andar - 100 vagas\nCâmera Alta / Vagas Menores)",
    "UFPR04\n(4º Andar - 28 vagas\nCâmera Próxima / Vagas Maiores)",
    "UFPR05\n(5º Andar - 45 vagas\nDistância Intermediária)",
]

fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(resumo_patio))
largura = 0.22

rects1 = ax.bar(
    x - largura * 1.5,
    resumo_patio["Acuracia"],
    largura,
    label="Acurácia",
    color="#1f77b4",
    edgecolor="black",
    )
rects2 = ax.bar(
    x - largura * 0.5,
    resumo_patio["Precisao"],
    largura,
    label="Precisão",
    color="#2ca02c",
    edgecolor="black",
    )
rects3 = ax.bar(
    x + largura * 0.5,
    resumo_patio["Recall"],
    largura,
    label="Recall (Sensibilidade)",
    color="#ff7f0e",
    edgecolor="black",
    )
rects4 = ax.bar(
    x + largura * 1.5,
    resumo_patio["F1"],
    largura,
    label="F1-Score",
    color="#d62728",
    edgecolor="black",
    )

ax.set_ylabel("Desempenho Médio Consolidado (%)")
ax.set_title(
    "Impacto da Altura da Câmera e Resolução das Vagas no Desempenho ($\\tau = 900$)",
    fontweight="bold",
)
ax.set_xticks(x)
ax.set_xticklabels(resumo_patio["Descricao"], fontweight="bold")
ax.set_ylim(30, 105)
ax.legend(loc="lower left", frameon=True)

for bar_group in [rects1, rects2, rects3, rects4]:
    for bar in bar_group:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )

plt.tight_layout()
caminho_fig2 = os.path.join(PASTA_GRAFICOS, "benchmark_fig2_impacto_camera.png")
plt.savefig(caminho_fig2, dpi=300)
plt.close()
print(f"[SALVO] {caminho_fig2}")


# ==============================================================================
# FIGURA 3: Heatmap 3x3 de Acurácia (Pátio x Clima)
# ==============================================================================
tabela_pivot = df.pivot(
    index="Patio", columns="Condicao_PT", values="Acuracia_Porc"
)
tabela_pivot = tabela_pivot[["Ensolarado", "Nublado", "Chuvoso"]]

plt.figure(figsize=(7, 4.2))
sns.heatmap(
    tabela_pivot,
    annot=True,
    fmt=".2f",
    cmap="YlGnBu",
    cbar=True,
    linewidths=1,
    linecolor="white",
    annot_kws={"size": 12, "weight": "bold"},
)
plt.title(
    "Matriz Térmica de Acurácia (%) — Pátio vs. Clima ($\\tau = 900$)",
    fontweight="bold",
)
plt.ylabel("Pátio / Ângulo da Câmera", fontweight="bold")
plt.xlabel("Condição Climática", fontweight="bold")
plt.tight_layout()

caminho_fig3 = os.path.join(PASTA_GRAFICOS, "benchmark_fig3_heatmap_pivot.png")
plt.savefig(caminho_fig3, dpi=300)
plt.close()
print(f"[SALVO] {caminho_fig3}")


# ==============================================================================
# FIGURA 4: Matriz de Confusão Global Agregada (669.528 Decisões)
# ==============================================================================
total_vp = int(df["VP"].sum())
total_vn = int(df["VN"].sum())
total_fp = int(df["FP"].sum())
total_fn = int(df["FN"].sum())
total_geral = total_vp + total_vn + total_fp + total_fn

matriz_global = np.array([[total_vp, total_fn], [total_fp, total_vn]])

rotulos_global = np.array(
    [
        [
            f"VP\n{total_vp:,}\n({total_vp/total_geral*100:.1f}%)",
            f"FN (Não viu o carro)\n{total_fn:,}\n({total_fn/total_geral*100:.1f}%)",
        ],
        [
            f"FP (Alarme Falso)\n{total_fp:,}\n({total_fp/total_geral*100:.1f}%)",
            f"VN\n{total_vn:,}\n({total_vn/total_geral*100:.1f}%)",
        ],
    ]
)

plt.figure(figsize=(6.5, 5))
sns.heatmap(
    matriz_global,
    annot=rotulos_global,
    fmt="",
    cmap="Blues",
    cbar=False,
    xticklabels=["Predito: Ocupada", "Predito: Livre"],
    yticklabels=["Real: Ocupada", "Real: Livre"],
    annot_kws={"size": 11, "weight": "bold"},
)

acuracia_global = (total_vp + total_vn) / total_geral * 100.0
plt.title(
    f"Matriz de Confusão Global do Dataset PKLot Completo\nTotal: {total_geral:,} Vagas Avaliadas | Acurácia Geral: {acuracia_global:.2f}%",
    fontweight="bold",
)
plt.tight_layout()
caminho_fig4 = os.path.join(
    PASTA_GRAFICOS, "benchmark_fig4_matriz_global_total.png"
)
plt.savefig(caminho_fig4, dpi=300)
plt.close()
print(f"[SALVO] {caminho_fig4}")


# ==============================================================================
# TABELA FORMATADA PARA O RELATÓRIO ABNT / OVERLEAF
# ==============================================================================
print("\n" + "=" * 95)
print(
    "                TABELA COMPLETA DO BENCHMARK GLOBAL (PKLot 12.416 Imagens)                "
)
print("=" * 95)
print(
    df[
        [
            "Patio",
            "Condicao_PT",
            "Imagens",
            "Vagas",
            "VP",
            "VN",
            "FP",
            "FN",
            "Acuracia_Porc",
            "Precisao_Porc",
            "Recall_Porc",
            "F1_Score_Porc",
        ]
    ].to_markdown(index=False)
)

print("\n" + "-" * 95)
print("CÓDIGO LATEX DA TABELA CONSOLIDADA PARA O OVERLEAF:")
print("-" * 95)
print(r"\begin{table}[htbp]")
print(r"\centering")
print(
    r"\caption{Resultados experimentais em larga escala do método de PDI clássico ($\tau = 900$) sobre o conjunto integral do dataset PKLot.}"
)
print(r"\label{tab:benchmark_global_pklot}")
print(r"\begin{tabular}{llccccccc}")
print(r"\hline")
print(
    r"\textbf{Pátio} & \textbf{Condição} & \textbf{Imagens} & \textbf{Vagas} & \textbf{Acurácia} & \textbf{Precisão} & \textbf{Recall} & \textbf{F1-Score} & \textbf{FPS} \\ \hline"
)
for _, r in df.iterrows():
    print(
        f"{r['Patio']} & {r['Condicao_PT']} & {int(r['Imagens'])} & {int(r['Vagas']):,} & {r['Acuracia_Porc']:.2f}\\% & {r['Precisao_Porc']:.2f}\\% & {r['Recall_Porc']:.2f}\\% & {r['F1_Score_Porc']:.2f}\\% & {r['FPS']:.1f} \\\\"
    )
print(r"\hline")
print(
    rf"\textbf{{TOTAL}} & \textbf{{Todas}} & \textbf{{{df['Imagens'].sum():,}}} & \textbf{{{total_geral:,}}} & \textbf{{{acuracia_global:.2f}\\%}} & \textbf{{--}} & \textbf{{--}} & \textbf{{--}} & \textbf{{21.5}} \\\\"
)
print(r"\hline")
print(r"\end{tabular}")
print(r"\end{table}")
print("=" * 95)
print(
    f"\n[SUCESSO] 4 novas figuras do benchmark salvas em: '{os.path.abspath(PASTA_GRAFICOS)}'"
)