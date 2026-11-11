"""
Visualização do benchmark global do PDI clássico (PKLot, 3 pátios x 3 climas).

Uso (a partir da pasta scripts/ ou da raiz do projeto):
    python visualizar_benchmark_global.py
    python visualizar_benchmark_global.py --csv ../historico_final_tau_900.csv --saida ../graficos

Gera, em --saida:
    benchmark_fig1_patio_clima.png, benchmark_fig2_impacto_camera.png,
    benchmark_fig3_heatmap_pivot.png, benchmark_fig4_matriz_global_total.png,
    tabela_benchmark.tex, tabela_patios.tex   (para \\input no artigo)

Todas as métricas são recalculadas a partir das contagens VP/VN/FP/FN, e os
totais (vagas, acurácia, FPS) vêm dos dados, sem valores digitados à mão.
"""
import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PATIOS = ["UFPR04", "UFPR05", "PUCPR"]
CLIMAS = ["Sunny", "Cloudy", "Rainy"]
CLIMA_PT = {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Rainy": "Chuvoso"}
DESC_PATIO = {
    "UFPR04": "UFPR04\n(4º andar)",
    "UFPR05": "UFPR05\n(5º andar)",
    "PUCPR": "PUCPR\n(10º andar)",
}
COLS = ["Clima", "Imagens", "Vagas", "VP", "VN", "FP", "FN", "FPS"]

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10, "axes.titlesize": 12,
    "axes.labelsize": 11, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.fontsize": 9, "figure.titlesize": 13,
})


# ----------------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------------
def achar_csv(caminho):
    candidatos = [caminho] if caminho else []
    nome = "historico_final_tau_900.csv"
    candidatos += [nome, os.path.join("..", nome), os.path.join("..", "..", nome)]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    sys.exit(f"[ERRO] CSV não encontrado. Tentei: {candidatos}")


def metricas(vp, vn, fp, fn):
    """Métricas em % a partir das contagens (aceita escalares ou Series)."""
    n = vp + vn + fp + fn
    prec = vp / (vp + fp) * 100
    rec = vp / (vp + fn) * 100
    return dict(
        Acuracia=(vp + vn) / n * 100, Precisao=prec, Recall=rec,
        F1=2 * prec * rec / (prec + rec),
    )


def fps_agregado(g):
    """FPS global = imagens totais / tempo total (média harmônica ponderada)."""
    return g["Imagens"].sum() / (g["Imagens"] / g["FPS"]).sum()


def br(x, casas=2):
    """Número no formato PT-BR (milhar com ponto, decimal com vírgula)."""
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def rotular_barras(ax, fmt="{:.1f}%", tam=8):
    for cont in ax.containers:
        ax.bar_label(cont, labels=[fmt.format(v) for v in cont.datavalues],
                     fontsize=tam, fontweight="bold", padding=2)


# ----------------------------------------------------------------------------
# Carga e validação
# ----------------------------------------------------------------------------
def carregar(caminho_csv):
    df = pd.read_csv(caminho_csv, sep=";")
    faltam = [c for c in COLS if c not in df.columns]
    if faltam:
        sys.exit(f"[ERRO] Colunas ausentes no CSV: {faltam}")

    # Se o CSV acumulou rodadas (modo append), usa a mais recente de cada Clima.
    if "DataHora" in df.columns:
        df = df.sort_values("DataHora").drop_duplicates("Clima", keep="last")

    df = df[df["Clima"].str.contains("_", na=False)].copy()
    df[["Patio", "Condicao"]] = df["Clima"].str.split("_", n=1, expand=True)
    df["Patio"] = pd.Categorical(df["Patio"], PATIOS, ordered=True)
    df["Condicao"] = pd.Categorical(df["Condicao"], CLIMAS, ordered=True)
    df = df.sort_values(["Patio", "Condicao"]).reset_index(drop=True)
    df["Condicao_PT"] = df["Condicao"].map(CLIMA_PT)

    # Consistência interna: VP+VN+FP+FN deve ser igual ao número de vagas.
    soma = df[["VP", "VN", "FP", "FN"]].sum(axis=1)
    if not (soma == df["Vagas"]).all():
        print("[AVISO] VP+VN+FP+FN difere de Vagas em alguma linha:")
        print(df.loc[soma != df["Vagas"], ["Clima", "Vagas"]])

    # Recalcula métricas a partir das contagens e confere com o CSV.
    m = metricas(df["VP"], df["VN"], df["FP"], df["FN"])
    for k, col in [("Acuracia", "Acuracia_Porc"), ("Precisao", "Precisao_Porc"),
                   ("Recall", "Recall_Porc"), ("F1", "F1_Score_Porc")]:
        df[k] = m[k]
        if col in df.columns and (df[col] - df[k]).abs().max() > 0.01:
            print(f"[AVISO] {col} do CSV difere do valor recalculado.")

    tau = int(df["Limiar_Tau"].iloc[0]) if "Limiar_Tau" in df.columns else None
    return df, tau


def resumo_por_patio(df):
    r = df.groupby("Patio", observed=True)[["Imagens", "Vagas", "VP", "VN", "FP", "FN"]].sum()
    r = r.join(pd.DataFrame(metricas(r["VP"], r["VN"], r["FP"], r["FN"])))
    r["VagasPorImagem"] = r["Vagas"] / r["Imagens"]
    r["FPS"] = df.groupby("Patio", observed=True).apply(fps_agregado, include_groups=False)
    return r.reset_index()


# ----------------------------------------------------------------------------
# Figuras
# ----------------------------------------------------------------------------
def fig1(df, tau, pasta, dpi):
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    for ax, col, titulo, pal in [
        (axes[0], "Acuracia", "Acurácia (%)", "Blues_d"),
        (axes[1], "F1", "F1-Score (%)", "Reds_d"),
    ]:
        sns.barplot(data=df, x="Patio", y=col, hue="Condicao_PT",
                    hue_order=list(CLIMA_PT.values()), palette=pal, ax=ax,
                    edgecolor="black")
        ax.set_title(f"{titulo} por pátio e condição climática", fontweight="bold")
        ax.set_ylabel(titulo)
        ax.set_xlabel("Pátio avaliado")
        ax.set_ylim(40, 100)
        ax.legend(title="Condição", loc="upper right", ncol=3,)
        rotular_barras(ax)
    plt.suptitle(f"Benchmark completo do PDI clássico na base PKLot ($\\tau = {tau}$)",
                 fontweight="bold")
    plt.tight_layout()
    caminho = os.path.join(pasta, "benchmark_fig1_patio_clima.png")
    plt.savefig(caminho, dpi=dpi)
    plt.close()
    return caminho


def fig2(resumo, tau, pasta, dpi):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(resumo))
    larg = 0.2
    series = [("Acuracia", "Acurácia", "#1f77b4"), ("Precisao", "Precisão", "#2ca02c"),
              ("Recall", "Recall", "#ff7f0e"), ("F1", "F1-Score", "#d62728")]
    for i, (col, nome, cor) in enumerate(series):
        barras = ax.bar(x + (i - 1.5) * larg, resumo[col], larg, label=nome,
                        color=cor, edgecolor="black")
        ax.bar_label(barras, labels=[f"{v:.1f}%" for v in resumo[col]],
                     fontsize=8, fontweight="bold", padding=2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{DESC_PATIO[p]}\n{v:.0f} vagas/imagem"
                        for p, v in zip(resumo["Patio"], resumo["VagasPorImagem"])],
                       fontweight="bold")
    ax.set_ylabel("Desempenho consolidado (%)")
    ax.set_ylim(30, 105)
    ax.set_title(f"Impacto da altura da câmera e da escala das vagas ($\\tau = {tau}$)",
                 fontweight="bold")
    ax.legend(loc="upper right", ncol=2)
    plt.tight_layout()
    caminho = os.path.join(pasta, "benchmark_fig2_impacto_camera.png")
    plt.savefig(caminho, dpi=dpi)
    plt.close()
    return caminho


def fig3(df, tau, pasta, dpi):
    piv = df.pivot(index="Patio", columns="Condicao_PT", values="Acuracia")
    piv = piv[list(CLIMA_PT.values())].loc[PATIOS]
    plt.figure(figsize=(7, 4.2))
    sns.heatmap(piv, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=1,
                linecolor="white", annot_kws={"size": 12, "weight": "bold"},
                cbar_kws={"label": "Acurácia (%)"})
    plt.title(f"Acurácia (%) por pátio e clima ($\\tau = {tau}$)", fontweight="bold")
    plt.ylabel("Pátio")
    plt.xlabel("Condição climática")
    plt.tight_layout()
    caminho = os.path.join(pasta, "benchmark_fig3_heatmap_pivot.png")
    plt.savefig(caminho, dpi=dpi)
    plt.close()
    return caminho


def fig4(df, pasta, dpi):
    vp, vn, fp, fn = (int(df[c].sum()) for c in ["VP", "VN", "FP", "FN"])
    n = vp + vn + fp + fn
    mat = np.array([[vp, fn], [fp, vn]])
    rot = np.array([
        [f"VP\n{vp:,}\n({vp / n * 100:.1f}%)", f"FN (carro não detectado)\n{fn:,}\n({fn / n * 100:.1f}%)"],
        [f"FP (alarme falso)\n{fp:,}\n({fp / n * 100:.1f}%)", f"VN\n{vn:,}\n({vn / n * 100:.1f}%)"],
    ])
    plt.figure(figsize=(6.5, 5))
    sns.heatmap(mat, annot=rot, fmt="", cmap="Blues", cbar=False,
                xticklabels=["Predito: ocupada", "Predito: livre"],
                yticklabels=["Real: ocupada", "Real: livre"],
                annot_kws={"size": 11, "weight": "bold"})
    plt.title(f"Matriz de confusão global — {n:,} vagas avaliadas\n"
              f"Acurácia geral: {(vp + vn) / n * 100:.2f}%", fontweight="bold")
    plt.tight_layout()
    caminho = os.path.join(pasta, "benchmark_fig4_matriz_global_total.png")
    plt.savefig(caminho, dpi=dpi)
    plt.close()
    return caminho


# ----------------------------------------------------------------------------
# Tabelas LaTeX (booktabs, formato PT-BR) para \input no artigo
# ----------------------------------------------------------------------------
def tabela_benchmark_tex(df, tau):
    tot = {c: int(df[c].sum()) for c in ["Imagens", "Vagas", "VP", "VN", "FP", "FN"]}
    mt = metricas(tot["VP"], tot["VN"], tot["FP"], tot["FN"])
    L = [r"\begin{table}[htbp]", r"\centering",
         rf"\caption{{Resultados do método de PDI clássico ($\tau={tau}$) sobre as imagens processadas da base PKLot.}}",
         r"\label{tab:benchmark}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{llrrrrrrr}", r"\toprule",
         r"\textbf{Pátio} & \textbf{Condição} & \textbf{Imagens} & \textbf{Vagas} & \textbf{Acurácia} & \textbf{Precisão} & \textbf{Recall} & \textbf{F1} & \textbf{FPS} \\",
         r"\midrule"]
    for _, r in df.iterrows():
        L.append(f"{r['Patio']} & {r['Condicao_PT']} & {br(r['Imagens'], 0)} & {br(r['Vagas'], 0)} & "
                 f"{br(r['Acuracia'])}\\% & {br(r['Precisao'])}\\% & {br(r['Recall'])}\\% & "
                 f"{br(r['F1'])}\\% & {br(r['FPS'], 1)} \\\\")
    L += [r"\midrule",
          f"\\textbf{{Total}} & \\textbf{{Todas}} & \\textbf{{{br(tot['Imagens'], 0)}}} & \\textbf{{{br(tot['Vagas'], 0)}}} & "
          f"\\textbf{{{br(mt['Acuracia'])}\\%}} & \\textbf{{{br(mt['Precisao'])}\\%}} & \\textbf{{{br(mt['Recall'])}\\%}} & "
          f"\\textbf{{{br(mt['F1'])}\\%}} & \\textbf{{{br(fps_agregado(df), 1)}}} \\\\",
          r"\bottomrule", r"\end{tabular}",
          r"\fonte{Elaborado pelo autor, a partir de \texttt{historico\_final\_tau\_900.csv}.}",
          r"\end{table}"]
    return "\n".join(L) + "\n"


def tabela_patios_tex(resumo, tau):
    L = [r"\begin{table}[htbp]", r"\centering",
         rf"\caption{{Resultados consolidados por pátio ($\tau={tau}$).}}",
         r"\label{tab:patios}", r"\small", r"\begin{tabular}{lrrrrrrr}", r"\toprule",
         r"\textbf{Pátio} & \textbf{Vagas/imagem} & \textbf{Acurácia} & \textbf{Precisão} & \textbf{Recall} & \textbf{F1} & \textbf{FP} & \textbf{FN} \\",
         r"\midrule"]
    for _, r in resumo.iterrows():
        L.append(f"{r['Patio']} & {br(r['VagasPorImagem'], 0)} & {br(r['Acuracia'])}\\% & "
                 f"{br(r['Precisao'])}\\% & {br(r['Recall'])}\\% & {br(r['F1'])}\\% & "
                 f"{br(r['FP'], 0)} & {br(r['FN'], 0)} \\\\")
    L += [r"\bottomrule", r"\end{tabular}",
          r"\fonte{Elaborado pelo autor. Vagas por imagem = vagas avaliadas / imagens processadas.}",
          r"\end{table}"]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="caminho do historico_final_tau_900.csv")
    ap.add_argument("--saida", default="graficos", help="pasta de saída (padrão: graficos)")
    ap.add_argument("--dpi", type=int, default=300)
    a = ap.parse_args()

    os.makedirs(a.saida, exist_ok=True)
    df, tau = carregar(achar_csv(a.csv))
    if len(df) != 9:
        print(f"[AVISO] Esperadas 9 linhas (3 pátios x 3 climas); encontradas {len(df)}.")

    resumo = resumo_por_patio(df)
    tot_vagas, tot_img = int(df["Vagas"].sum()), int(df["Imagens"].sum())
    print(f"[OK] {len(df)} conjuntos | {tot_img:,} imagens | {tot_vagas:,} vagas | "
          f"FPS global {fps_agregado(df):.1f}")

    saidas = [fig1(df, tau, a.saida, a.dpi), fig2(resumo, tau, a.saida, a.dpi),
              fig3(df, tau, a.saida, a.dpi), fig4(df, a.saida, a.dpi)]
    for s in saidas:
        print(f"[SALVO] {s}")

    for nome, conteudo in [("tabela_benchmark.tex", tabela_benchmark_tex(df, tau)),
                           ("tabela_patios.tex", tabela_patios_tex(resumo, tau))]:
        caminho = os.path.join(a.saida, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"[SALVO] {caminho}")

    cols = ["Patio", "Condicao_PT", "Imagens", "Vagas", "VP", "VN", "FP", "FN",
            "Acuracia", "Precisao", "Recall", "F1"]
    print("\n" + df[cols].round(2).to_string(index=False))
    print("\nConsolidado por pátio:")
    print(resumo.round(2).to_string(index=False))


if __name__ == "__main__":
    main()