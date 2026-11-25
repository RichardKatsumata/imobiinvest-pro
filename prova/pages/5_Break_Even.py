"""
Página 5 — Análise de Break-Even
Calcula os quatro pontos de equilíbrio de um imóvel para locação usando o Método da Bisseção.
"""

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import custo_total, listar_empreendimentos
from utils.calculos import break_even_locacao, fluxo_locacao
from utils.formatters import brl, pct
from utils.numericos import calcular_vpl
from utils.ui import (
    load_css,
    render_sidebar_brand,
    render_header,
    apply_chart_style,
    COLOR_GOLD,
    COLOR_POS,
    COLOR_NEG,
    COLOR_MUTED,
)

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Análise de Break-Even | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Fronteiras de Equilíbrio (Break-Even Analysis)",
    subtitle="Determinação numérica do aluguel mínimo operacional, financeiro, econômico e taxa crítica de ocupação via Método da Bisseção.",
    category="EQUILIBRIUM MODELLING",
    code="MOD-05",
)

empreendimentos = listar_empreendimentos()

# ── Sidebar — entradas ────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand("Equilibrium Modelling")
    st.markdown('<div class="sidebar-section-label">Parâmetros Estruturais</div>', unsafe_allow_html=True)

    opcoes_emp = ["— Sem vínculo —"] + [f"{e['id']} — {e['nome']}" for e in empreendimentos]
    emp_sel_label = st.selectbox("Ativo de Referência", opcoes_emp)
    emp_sel = None
    if emp_sel_label != "— Sem vínculo —":
        emp_id_s = int(emp_sel_label.split(" — ")[0])
        emp_sel = next((e for e in empreendimentos if e["id"] == emp_id_s), None)

    if "last_emp_be" not in st.session_state:
        st.session_state.last_emp_be = emp_sel_label
        st.session_state.be_inv = custo_total(emp_sel) if emp_sel else 300_000.0
    elif st.session_state.last_emp_be != emp_sel_label:
        st.session_state.last_emp_be = emp_sel_label
        if emp_sel:
            st.session_state.be_inv = custo_total(emp_sel)

    investimento = st.number_input(
        "Capital Investido / CAPEX (R$)",
        min_value=0.0,
        step=1_000.0,
        format="%.2f",
        key="be_inv",
    )

    despesas_mensais = st.number_input(
        "Encargos Fixos / OPEX (R$/mês)",
        min_value=0.0,
        value=500.0,
        step=50.0,
        format="%.2f",
    )

    taxa_vacancia_pct = st.slider(
        "Taxa de Vacância Estimada (%)",
        min_value=0,
        max_value=50,
        value=5,
        step=1,
    )

    reajuste_anual_pct = st.slider(
        "Reajuste Anual Contratual (%)",
        min_value=0,
        max_value=15,
        value=3,
        step=1,
    )

    periodos = st.slider(
        "Horizonte de Análise (meses)",
        min_value=12,
        max_value=360,
        value=120,
        step=12,
    )

    tma_mensal_pct = st.number_input(
        "Custo de Capital / TMA (% a.m.)",
        min_value=0.0,
        value=0.8,
        step=0.1,
        format="%.2f",
    )

    valor_residual = st.number_input(
        "Valor Residual (R$)",
        min_value=0.0,
        value=0.0,
        step=1_000.0,
        format="%.2f",
    )

    st.divider()
    calcular = st.button("Calcular Fronteiras de Equilíbrio", type="primary", use_container_width=True)

# ── Cálculo ───────────────────────────────────────────────────────────────────
if calcular:
    taxa_vacancia  = taxa_vacancia_pct  / 100.0
    reajuste_anual = reajuste_anual_pct / 100.0
    tma_mensal     = tma_mensal_pct     / 100.0

    with st.spinner("Executando Método da Bisseção para localização de raízes..."):
        be = break_even_locacao(
            investimento=investimento,
            despesas_mensais=despesas_mensais,
            taxa_vacancia=taxa_vacancia,
            reajuste_anual=reajuste_anual,
            periodos=periodos,
            tma_mensal=tma_mensal,
            valor_residual=valor_residual,
        )

    al_op   = be["aluguel_operacional"]
    al_fin  = be["aluguel_financeiro"]
    al_eco  = be["aluguel_economico"]
    ocu_min = be["taxa_ocupacao_minima"]
    al_ref  = be.get("aluguel_referencia_ocupacao", al_op * 2)
    hists   = be.get("historicos", {})

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.subheader("Pontos Críticos de Equilíbrio (Solver: Bisseção)")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Break-Even Operacional", brl(al_op), delta=f"{len(hists.get('Operacional', []))} iter.", delta_color="off")
        st.caption("Neutraliza exatamente o OPEX mensal considerando a vacância estrutural.")

    with c2:
        val_fin = brl(al_fin) if not (isinstance(al_fin, float) and math.isnan(al_fin)) else "—"
        st.metric("Break-Even Financeiro", val_fin, delta=f"{len(hists.get('Financeiro', []))} iter.", delta_color="off")
        st.caption("Recupera 100% do capital nominal investido dentro do horizonte estipulado.")

    with c3:
        val_eco = brl(al_eco) if not (isinstance(al_eco, float) and math.isnan(al_eco)) else "—"
        st.metric("Break-Even Econômico (VPL = 0)", val_eco, delta=f"{len(hists.get('Econômico', []))} iter.", delta_color="off")
        st.caption("Remunera integralmente o custo de oportunidade (TMA) exigido pelo investidor.")

    with c4:
        val_ocu = pct(ocu_min * 100) if not (isinstance(ocu_min, float) and math.isnan(ocu_min)) else "—"
        st.metric("Taxa de Ocupação Crítica", val_ocu, delta=f"Ref.: {brl(al_ref)}", delta_color="off")
        st.caption("Ocupação mínima necessária para preservar VPL não-negativo no aluguel de referência.")

    st.divider()

    # ── Gráfico 1: VPL × Aluguel ──────────────────────────────────────────────
    al_max = al_eco * 1.8 if not (isinstance(al_eco, float) and math.isnan(al_eco)) and al_eco > 0 else max(despesas_mensais * 10, 5000.0)
    n_pts_al = 250
    alugueis = [i * al_max / (n_pts_al - 1) for i in range(n_pts_al)]
    vpls = []
    for a in alugueis:
        fl = fluxo_locacao(investimento, float(a), taxa_vacancia, despesas_mensais,
                           reajuste_anual, periodos, valor_residual)
        vpls.append(calcular_vpl(fl, tma_mensal))

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=alugueis,
        y=vpls,
        mode="lines",
        name="Curva de VPL",
        line=dict(color=COLOR_GOLD, width=2.5),
    ))
    fig1.add_hline(
        y=0,
        line=dict(color=COLOR_MUTED, width=1, dash="dash"),
        annotation_text="Fronteira VPL = 0",
        annotation_position="right",
    )

    be_lines = [
        (al_op,  "Operacional", COLOR_POS),
        (al_fin, "Financeiro",  COLOR_GOLD),
        (al_eco, "Econômico",   COLOR_NEG),
    ]
    for val, label, cor in be_lines:
        if not (isinstance(val, float) and math.isnan(val)):
            fig1.add_vline(
                x=val,
                line=dict(color=cor, width=1.5, dash="dot"),
                annotation_text=f"{label}: {brl(val)}",
                annotation_position="top right",
                annotation_font_color=cor,
            )

    apply_chart_style(fig1, title="Curva de Valor Presente Líquido em Função do Aluguel Mensal", height=420)
    fig1.update_xaxes(title="Aluguel Mensal Bruto (R$)")
    fig1.update_yaxes(title="VPL (R$)")
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # ── Gráfico 2: VPL × Taxa de Ocupação ────────────────────────────────────
    n_pts_oc = 200
    ocupacoes = [i / (n_pts_oc - 1) for i in range(n_pts_oc)]
    vpls_ocu = []
    for ocu in ocupacoes:
        fl = fluxo_locacao(investimento, al_ref, 1.0 - ocu, despesas_mensais,
                           reajuste_anual, periodos, valor_residual)
        vpls_ocu.append(calcular_vpl(fl, tma_mensal))

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=[o * 100.0 for o in ocupacoes],
        y=vpls_ocu,
        mode="lines",
        name="VPL",
        line=dict(color=COLOR_GOLD, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(197, 160, 89, 0.08)",
    ))
    fig2.add_hline(
        y=0,
        line=dict(color=COLOR_MUTED, width=1, dash="dash"),
        annotation_text="VPL = 0",
        annotation_position="right",
    )

    if not (isinstance(ocu_min, float) and math.isnan(ocu_min)):
        fig2.add_vline(
            x=ocu_min * 100,
            line=dict(color=COLOR_NEG, width=1.5, dash="dot"),
            annotation_text=f"Ocupação Crítica: {pct(ocu_min * 100)}",
            annotation_position="top right",
            annotation_font_color=COLOR_NEG,
        )

    apply_chart_style(
        fig2,
        title=f"Sensibilidade do VPL à Taxa de Ocupação Física (Aluguel Ref.: {brl(al_ref)})",
        height=400,
        showlegend=False,
    )
    fig2.update_xaxes(title="Taxa de Ocupação Física (%)", range=[0, 100])
    fig2.update_yaxes(title="VPL (R$)")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Histórico de Iterações da Bisseção ────────────────────────────────────
    with st.expander("Auditoria Numérica — Tabelas de Iterações do Método da Bisseção"):
        t_op, t_fin, t_eco, t_ocu = st.tabs(["Operacional", "Financeiro", "Econômico (VPL=0)", "Ocupação Crítica"])
        for aba_h, chave_h in [(t_op, "Operacional"), (t_fin, "Financeiro"), (t_eco, "Econômico"), (t_ocu, "Ocupação Mínima")]:
            with aba_h:
                lista_h = hists.get(chave_h, [])
                if lista_h:
                    st.caption(f"Convergência alcançada em **{len(lista_h)} iterações** pelo Método da Bisseção.")
                    st.dataframe(pd.DataFrame(lista_h), use_container_width=True, hide_index=True)
                else:
                    st.info("Ponto determinado analiticamente ou fora do domínio de busca.")

else:
    st.info("Configure os parâmetros estruturais na barra lateral e acione Calcular Fronteiras de Equilíbrio.")
    st.markdown(
        r"""
        ### Metodologia de Fronteiras de Equilíbrio

        A modelagem de Break-Even determina os níveis mínimos de receita e ocupação exigidos para preservar a solvência e a atratividade econômica do ativo:

        | Fronteira | Equação de Equilíbrio (Resolvida via Bisseção) |
        |---|---|
        | **Operacional** | $f(A) = A(1 - v) - \text{OPEX} = 0$ |
        | **Financeiro** | $f(A) = \sum_{t=0}^T FC_t(A) = 0$ (Payback Nominal = Horizonte) |
        | **Econômico** | $f(A) = \text{VPL}(A, \text{TMA}) = 0$ (Geração de Valor Nula) |
        | **Ocupação Crítica** | $f(\text{ocu}) = \text{VPL}(\text{ocu}, \text{TMA}) = 0$ |
        """
    )
