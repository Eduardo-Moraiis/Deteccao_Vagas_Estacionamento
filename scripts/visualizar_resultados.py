import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Configuração de estilo para publicação acadêmica (ABNT / IEEE)
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

ARQUIVO_CSV = "historico_experimentos.csv"
if not os.path.exists(ARQUIVO_CSV):
    if os.path.exists(os.path.join("..", ARQUIVO_CSV)):
        ARQUIVO_CSV = os.path.join("..", ARQUIVO_CSV)
    else:
        print(f"[ERRO] Arquivo '{ARQUIVO_CSV}' não encontrado!")
        exit(1)

df = pd.read_csv(ARQUIVO_CSV, sep=";")
print(f"[OK] Carregadas {len(df)} linhas de experimentos.")

# ------------------------------------------------------------------------------
# IDENTIFICAÇÃO AUTOMÁTICA DO MELHOR LIMIAR TAU (PONTO ÓTIMO)
# ------------------------------------------------------------------------------
resumo_tau = (
    df.groupby("Limiar_Tau")
    .agg(
        {
            "Acuracia_Porc": "mean",
            "F1_Score_Porc": "mean",
            "Precisao_Porc": "mean",
            "Recall_Porc": "mean",
        }
    )
    .reset_index()
)

idx_otimo = resumo_tau["F1_Score_Porc"].idxmax()
tau_otimo = int(resumo_tau.loc[idx_otimo, "Limiar_Tau"])
f1_max = resumo_tau.loc[idx_otimo, "F1_Score_Porc"]
acc_max = resumo_tau.loc[idx_otimo, "Acuracia_Porc"]

print(
    f"\n>>> LIMIAR ÓTIMO IDENTIFICADO: tau = {tau_otimo} (F1 Médio: {f1_max:.2f}% | Acurácia Média: {acc_max:.2f}%) <<<\n"
)

# Filtra apenas os dados do limiar ótimo para gráficos de detalhe
df_otimo = df[df["Limiar_Tau"] == tau_otimo].drop_duplicates(
    subset=["Clima"], keep="last"
)


# ==============================================================================
# FIGURA 1: Curva de Trade-off (Precisão x Recall x F1) por Clima
# ==============================================================================
limiares_unicos = df["Limiar_Tau"].unique()

if len(limiares_unicos) > 1:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    climaticos = ["Sunny", "Cloudy", "Rainy"]
    nomes_pt = {
        "Sunny": "Ensolarado (Sunny)",
        "Cloudy": "Nublado (Cloudy)",
        "Rainy": "Chuvoso (Rainy)",
    }

    for i, clima in enumerate(climaticos):
        sub_df = (
            df[df["Clima"] == clima]
            .sort_values(by="Limiar_Tau")
            .drop_duplicates(subset=["Limiar_Tau"], keep="last")
        )

        if not sub_df.empty:
            axes[i].plot(
                sub_df["Limiar_Tau"],
                sub_df["Acuracia_Porc"],
                label="Acurácia",
                marker="o",
                color="#1f77b4",
                linewidth=1.8,
                markersize=4,
            )
            axes[i].plot(
                sub_df["Limiar_Tau"],
                sub_df["Precisao_Porc"],
                label="Precisão",
                marker="s",
                color="#2ca02c",
                linewidth=1.8,
                markersize=4,
            )
            axes[i].plot(
                sub_df["Limiar_Tau"],
                sub_df["Recall_Porc"],
                label="Recall",
                marker="^",
                color="#ff7f0e",
                linewidth=1.8,
                markersize=4,
            )
            axes[i].plot(
                sub_df["Limiar_Tau"],
                sub_df["F1_Score_Porc"],
                label="F1-Score",
                marker="d",
                color="#d62728",
                linewidth=2.2,
                linestyle="--",
                markersize=5,
            )

            # Destaca a linha do limiar ótimo
            axes[i].axvline(
                x=tau_otimo,
                color="black",
                linestyle=":",
                linewidth=1.5,
                alpha=0.8,
                label=f"Ótimo ($\\tau={tau_otimo}$)",
            )

            axes[i].set_title(nomes_pt[clima], fontweight="bold")
            axes[i].set_xlabel("Limiar de Pixels ($\\tau$)")
            axes[i].set_ylim(0, 105)
            axes[i].grid(True, linestyle="--", alpha=0.5)

    axes[0].set_ylabel("Taxa de Desempenho (%)")
    axes[0].legend(loc="lower left", frameon=True)

    plt.suptitle(
        f"Calibração do Hiperparâmetro $\\tau$ nas Três Condições Climáticas (Destaque em $\\tau={tau_otimo}$)",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()
    caminho_fig1 = os.path.join(PASTA_GRAFICOS, "fig1_curvas_calibracao_clima.png")
    plt.savefig(caminho_fig1, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SALVO] {caminho_fig1}")


# ==============================================================================
# FIGURA 2: Visão Global Consolidada (Média dos 3 Climas vs. Tau)
# ==============================================================================
if len(limiares_unicos) > 1:
    plt.figure(figsize=(8.5, 4.8))
    plt.plot(
        resumo_tau["Limiar_Tau"],
        resumo_tau["Acuracia_Porc"],
        label="Acurácia Global",
        marker="o",
        color="#1f77b4",
        linewidth=2.2,
    )
    plt.plot(
        resumo_tau["Limiar_Tau"],
        resumo_tau["F1_Score_Porc"],
        label="F1-Score Médio",
        marker="d",
        color="#d62728",
        linewidth=2.5,
        linestyle="--",
    )
    plt.plot(
        resumo_tau["Limiar_Tau"],
        resumo_tau["Precisao_Porc"],
        label="Precisão Média",
        marker="s",
        color="#2ca02c",
        linewidth=1.8,
        alpha=0.7,
    )
    plt.plot(
        resumo_tau["Limiar_Tau"],
        resumo_tau["Recall_Porc"],
        label="Recall Médio",
        marker="^",
        color="#ff7f0e",
        linewidth=1.8,
        alpha=0.7,
    )

    plt.axvline(
        x=tau_otimo,
        color="black",
        linestyle=":",
        linewidth=1.8,
        label=f"Ponto Ótimo ($\\tau={tau_otimo}$)",
    )
    plt.scatter(
        [tau_otimo],
        [acc_max],
        color="blue",
        s=80,
        zorder=5,
        edgecolors="black",
    )
    plt.annotate(
        f"Acurácia Máx: {acc_max:.2f}%\nF1 Máx: {f1_max:.2f}%",
        xy=(tau_otimo, acc_max),
        xytext=(tau_otimo + 80, acc_max - 8),
        arrowprops=dict(facecolor="black", arrowstyle="->", lw=1.2),
        fontweight="bold",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3),
    )

    plt.title(
        "Desempenho Médio Global do Sistema em Função do Limiar $\\tau$",
        fontweight="bold",
    )
    plt.xlabel("Limiar de Pixels Ativos ($\\tau$)")
    plt.ylabel("Desempenho Médio (%)")
    plt.ylim(20, 102)
    plt.legend(loc="lower left", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    caminho_fig2 = os.path.join(PASTA_GRAFICOS, "fig2_desempenho_global_tau.png")
    plt.savefig(caminho_fig2, dpi=300)
    plt.close()
    print(f"[SALVO] {caminho_fig2}")


# ==============================================================================
# FIGURA 3: Comparativo de Métricas no Ponto Ótimo (tau = 900)
# ==============================================================================
metricas_plot = [
    "Acuracia_Porc",
    "Precisao_Porc",
    "Recall_Porc",
    "F1_Score_Porc",
]
nomes_plot = ["Acurácia", "Precisão", "Recall", "F1-Score"]

df_melted = pd.melt(
    df_otimo,
    id_vars=["Clima"],
    value_vars=metricas_plot,
    var_name="Métrica",
    value_name="Valor",
)
df_melted["Métrica"] = df_melted["Métrica"].map(
    dict(zip(metricas_plot, nomes_plot))
)
df_melted["Clima"] = df_melted["Clima"].replace(
    {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Rainy": "Chuvoso"}
)

plt.figure(figsize=(9, 4.8))
cores_barras = ["#4c72b0", "#55a868", "#dd8452", "#c44e52"]
bar_plot = sns.barplot(
    data=df_melted,
    x="Clima",
    y="Valor",
    hue="Métrica",
    palette=cores_barras,
    edgecolor="black",
    linewidth=0.8,
)

for p in bar_plot.patches:
    h = p.get_height()
    if not np.isnan(h) and h > 0:
        bar_plot.annotate(
            f"{h:.1f}%",
            (p.get_x() + p.get_width() / 2.0, h),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            xytext=(0, 2),
            textcoords="offset points",
        )

plt.title(
    f"Desempenho por Condição Climática na Configuração Ótima ($\\tau = {tau_otimo}$)",
    fontweight="bold",
)
plt.ylabel("Taxa (%)")
plt.xlabel("Condição Climática")
plt.ylim(0, 115)
plt.legend(loc="upper right", frameon=True)
plt.tight_layout()

caminho_fig3 = os.path.join(PASTA_GRAFICOS, "fig3_comparativo_climas_otimo.png")
plt.savefig(caminho_fig3, dpi=300)
plt.close()
print(f"[SALVO] {caminho_fig3}")


# ==============================================================================
# FIGURA 4: Matrizes de Confusão Visuais no Ponto Ótimo (tau = 900)
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

for i, (_, row) in enumerate(df_otimo.iterrows()):
    clima = row["Clima"]
    vp = int(row["VP"])
    vn = int(row["VN"])
    fp = int(row["FP"])
    fn = int(row["FN"])
    total = vp + vn + fp + fn

    matriz = np.array([[vp, fn], [fp, vn]])

    rotulos = np.array(
        [
            [f"VP\n{vp}\n({vp/total*100:.1f}%)", f"FN\n{fn}\n({fn/total*100:.1f}%)"],
            [f"FP\n{fp}\n({fp/total*100:.1f}%)", f"VN\n{vn}\n({vn/total*100:.1f}%)"],
        ]
    )

    sns.heatmap(
        matriz,
        annot=rotulos,
        fmt="",
        cmap="Blues",
        cbar=False,
        ax=axes[i],
        xticklabels=["Predito: Ocupada", "Predito: Livre"],
        yticklabels=["Real: Ocupada", "Real: Livre"],
        annot_kws={"size": 10, "weight": "bold"},
    )

    clima_map = {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Rainy": "Chuvoso"}
    axes[i].set_title(
        f"{clima_map.get(clima, clima)} ($\\tau = {tau_otimo}$)\nAcurácia: {row['Acuracia_Porc']:.2f}%",
        fontweight="bold",
    )

plt.suptitle(
    f"Matrizes de Confusão do PDI Clássico no Ponto Ótimo ($\\tau = {tau_otimo}$)",
    fontsize=13,
    fontweight="bold",
    y=1.02,
)
plt.tight_layout()

caminho_fig4 = os.path.join(PASTA_GRAFICOS, "fig4_matrizes_confusao_otimo.png")
plt.savefig(caminho_fig4, dpi=300, bbox_inches="tight")
plt.close()
print(f"[SALVO] {caminho_fig4}")


# ==============================================================================
# TABELA FORMATADA EM MARKDOWN E LATEX PARA O OVERLEAF
# ==============================================================================
print("\n" + "=" * 90)
print(f"       TABELA DE RESULTADOS NO PONTO ÓTIMO (TAU = {tau_otimo}) - COPIE PARA O ARTIGO       ")
print("=" * 90)
colunas_tabela = [
    "Clima",
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
    "FPS",
]
print(df_otimo[colunas_tabela].to_markdown(index=False))

print("\n" + "-" * 90)
print("CÓDIGO LATEX FORMATADO PARA O TEMPLATE OVERLEAF / ABNT:")
print("-" * 90)
print(r"\begin{table}[htbp]")
print(r"\centering")
print(
    rf"\caption{{Desempenho quantitativo do método de PDI clássico com limiar ótimo $\tau = {tau_otimo}$ por condição climática no dataset PKLot (UFPR04).}}"
)
print(r"\label{tab:resultados_otimos}")
print(r"\begin{tabular}{lcccccccc}")
print(r"\hline")
print(
    r"\textbf{Condição} & \textbf{Vagas} & \textbf{VP} & \textbf{VN} & \textbf{FP} & \textbf{FN} & \textbf{Acurácia} & \textbf{F1-Score} & \textbf{FPS} \\ \hline"
)
for _, r in df_otimo.iterrows():
    c_nome = {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Rainy": "Chuvoso"}.get(
        r["Clima"], r["Clima"]
    )
    print(
        f"{c_nome} & {int(r['Vagas'])} & {int(r['VP'])} & {int(r['VN'])} & {int(r['FP'])} & {int(r['FN'])} & {r['Acuracia_Porc']:.2f}\\% & {r['F1_Score_Porc']:.2f}\\% & {r['FPS']:.1f} \\\\"
    )
print(r"\hline")
print(r"\end{tabular}")
print(r"\end{table}")
print("=" * 90)
print(f"\n[SUCESSO] Todas as 4 figuras salvas em: '{os.path.abspath(PASTA_GRAFICOS)}'")