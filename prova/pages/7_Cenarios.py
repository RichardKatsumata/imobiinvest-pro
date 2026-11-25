"""
Página 7 — Matriz de Cenários Macroeconômicos
Compara os cenários Pessimista, Realista (Base) e Otimista para um investimento imobiliário.
"""

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.calculos import CENARIOS_FATORES, analisar_cenarios
from utils.formatters import brl, pct
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
    page_title="Cenários Macroeconômicos | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Modelagem de Cenários e Stress Test (Scenario Analysis)",
    subtitle="Avaliação comparativa sob regimes Pessimista (Stress), Realista (Base Case) e Otimista (Upside).",
    category="MACROECONOMIC STRESS TESTING",
    code="MOD-07",
)

COR_PESSIMISTA = COLOR_NEG
COR_REALISTA   = COLOR_GOLD
COR_OTIMISTA   = COLOR_POS

# ── Sidebar — entradas ────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand("Scenario Analysis")
    st.markdown('<div class="sidebar-section-label">Premissas do Caso Base</div>', unsafe_allow_html=True)

    investimento = st.number_input(
        "Capital Investido / CAPEX (R$)",
        min_value=0.0,
        value=300_000.0,
        step=1_000.0,
        format="%.2f",
    )

    aluguel_mensal = st.number_input(
        "Receita Mensal Base (R$)",
        min_value=0.0,
        value=2_500.0,
        step=50.0,
        format="%.2f",
    )

    taxa_vacancia_pct = st.slider(
        "Vacância Estrutural Base (%)",
        min_value=0,
        max_value=50,
        value=8,
        step=1,
    )

    despesas_mensais = st.number_input(
        "OPEX Mensal Base (R$)",
        min_value=0.0,
        value=400.0,
        step=50.0,
        format="%.2f",
    )

    reajuste_anual_pct = st.slider(
        "Indexador Anual (%)",
        min_value=0,
        max_value=15,
        value=3,
        step=1,
    )

    periodos = st.slider(
        "Horizonte de Projeção (meses)",
        min_value=12,
        max_value=360,
        value=120,
        step=12,
    )

    tma_mensal_pct = st.number_input(
        "TMA Mensal Base (%)",
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

    with st.expander("Calibragem de Multiplicadores por Cenário", expanded=False):
        st.caption("Fator multiplicador aplicado sobre as premissas do Caso Base.")

        col_p, col_r, col_o = st.columns(3)

        fp = CENARIOS_FATORES["Pessimista"]
        fr = CENARIOS_FATORES["Realista"]
        fo = CENARIOS_FATORES["Otimista"]

        with col_p:
            st.markdown(f'<span style="color:{COR_PESSIMISTA}; font-weight:600; font-size:0.75rem;">PESSIMISTA</span>', unsafe_allow_html=True)
            p_aluguel   = st.slider("Aluguel ×",   0.5, 1.5, float(fp["aluguel"]),   0.05, key="p_alug")
            p_vacancia  = st.slider("Vacância ×",  0.5, 3.0, float(fp["vacancia"]),  0.1,  key="p_vac")
            p_despesas  = st.slider("OPEX ×",      0.5, 2.0, float(fp["despesas"]),  0.05, key="p_desp")
            p_tma       = st.slider("TMA ×",       0.5, 2.0, float(fp["tma"]),       0.05, key="p_tma")

        with col_r:
            st.markdown(f'<span style="color:{COR_REALISTA}; font-weight:600; font-size:0.75rem;">REALISTA</span>', unsafe_allow_html=True)
            r_aluguel   = st.slider("Aluguel ×",   0.5, 1.5, float(fr["aluguel"]),   0.05, key="r_alug")
            r_vacancia  = st.slider("Vacância ×",  0.5, 3.0, float(fr["vacancia"]),  0.1,  key="r_vac")
            r_despesas  = st.slider("OPEX ×",      0.5, 2.0, float(fr["despesas"]),  0.05, key="r_desp")
            r_tma       = st.slider("TMA ×",       0.5, 2.0, float(fr["tma"]),       0.05, key="r_tma")

        with col_o:
            st.markdown(f'<span style="color:{COR_OTIMISTA}; font-weight:600; font-size:0.75rem;">OTIMISTA</span>', unsafe_allow_html=True)
            o_aluguel   = st.slider("Aluguel ×",   0.5, 1.5, float(fo["aluguel"]),   0.05, key="o_alug")
            o_vacancia  = st.slider("Vacância ×",  0.0, 3.0, float(fo["vacancia"]),  0.1,  key="o_vac")
            o_despesas  = st.slider("OPEX ×",      0.5, 2.0, float(fo["despesas"]),  0.05, key="o_desp")
            o_tma       = st.slider("TMA ×",       0.5, 2.0, float(fo["tma"]),       0.05, key="o_tma")

    st.divider()
    comparar = st.button("Processar Matriz de Cenários", type="primary", use_container_width=True)

# ── Análise ───────────────────────────────────────────────────────────────────
if comparar:
    taxa_vacancia  = taxa_vacancia_pct  / 100.0
    reajuste_anual = reajuste_anual_pct / 100.0
    tma_mensal     = tma_mensal_pct     / 100.0

    fatores_custom = {
        "Pessimista": {"aluguel": p_aluguel, "vacancia": p_vacancia,
                       "despesas": p_despesas, "tma": p_tma},
        "Realista":   {"aluguel": r_aluguel, "vacancia": r_vacancia,
                       "despesas": r_despesas, "tma": r_tma},
        "Otimista":   {"aluguel": o_aluguel, "vacancia": o_vacancia,
                       "despesas": o_despesas, "tma": o_tma},
    }

    with st.spinner("Executando simulações estocásticas e determinísticas por cenário..."):
        resultados = analisar_cenarios(
            investimento=investimento,
            aluguel_base=aluguel_mensal,
            vacancia_base=taxa_vacancia,
            despesas_base=despesas_mensais,
            reajuste_anual=reajuste_anual,
            periodos=periodos,
            tma_base_mensal=tma_mensal,
            valor_residual=valor_residual,
            fatores=fatores_custom,
        )

    cenarios   = ["Pessimista", "Realista", "Otimista"]
    cores_mapa = {
        "Pessimista": COR_PESSIMISTA,
        "Realista":   COR_REALISTA,
        "Otimista":   COR_OTIMISTA,
    }

    # ── Tabela comparativa ────────────────────────────────────────────────────
    st.subheader("Matriz Comparativa de Indicadores")

    def fmt_vpl(v):
        if isinstance(v, float) and math.isnan(v):
            return "—"
        return brl(v)

    def fmt_pct(v):
        if isinstance(v, float) and math.isnan(v):
            return "—"
        return pct(v)

    def fmt_mes(v):
        if isinstance(v, float) and math.isinf(v):
            return "Não atingido"
        if isinstance(v, float) and math.isnan(v):
            return "—"
        return f"{int(v)} meses"

    rows = {
        "Valor Presente Líquido (VPL)": [fmt_vpl(resultados[c]["vpl"])                for c in cenarios],
        "TIR Anual Efetiva":            [fmt_pct(resultados[c]["tir_anual"])          for c in cenarios],
        "Payback Nominal":              [fmt_mes(resultados[c]["payback_simples"])    for c in cenarios],
        "Payback Descontado":           [fmt_mes(resultados[c]["payback_descontado"]) for c in cenarios],
        "Retorno Sobre Capital (ROI)":  [fmt_pct(resultados[c]["roi"])                for c in cenarios],
    }

    df_comp = pd.DataFrame(rows, index=cenarios).T
    df_comp.index.name = "Indicador Financeiro"

    st.dataframe(df_comp, use_container_width=True)

    st.divider()

    # ── Gráfico de barras agrupadas: VPL (esq) e ROI/TIR (dir) ───────────────
    col_bar1, col_bar2 = st.columns(2)

    with col_bar1:
        fig_vpl_bar = go.Figure()
        for cenario in cenarios:
            r = resultados[cenario]
            vpl_val = r["vpl"] if not math.isnan(r["vpl"]) else 0.0
            fig_vpl_bar.add_trace(go.Bar(
                name=cenario,
                x=[cenario],
                y=[vpl_val],
                marker_color=cores_mapa[cenario],
                text=[brl(vpl_val)],
                textposition="outside",
                textfont=dict(size=11, color="#F8FAFC", family="JetBrains Mono, monospace"),
            ))
        apply_chart_style(fig_vpl_bar, title="Valor Presente Líquido por Cenário (R$)", height=400, showlegend=False)
        fig_vpl_bar.update_yaxes(title="VPL (R$)")
        st.plotly_chart(fig_vpl_bar, use_container_width=True)

    with col_bar2:
        fig_bar = go.Figure()
        for cenario in cenarios:
            r = resultados[cenario]
            roi_val = r["roi"] if not math.isnan(r["roi"]) else 0.0
            tir_val = r["tir_anual"] if not math.isnan(r["tir_anual"]) else 0.0

            fig_bar.add_trace(go.Bar(
                name=cenario,
                x=["ROI Acumulado (%)", "TIR Anual (%)"],
                y=[roi_val, tir_val],
                marker_color=cores_mapa[cenario],
                text=[pct(roi_val), pct(tir_val)],
                textposition="outside",
                textfont=dict(size=11, color="#F8FAFC", family="JetBrains Mono, monospace"),
            ))

        apply_chart_style(fig_bar, title="Taxas de Retorno: ROI e TIR Anual (%)", height=400)
        fig_bar.update_layout(barmode="group")
        fig_bar.update_yaxes(title="Percentual (%)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Gráfico de fluxo acumulado ────────────────────────────────────────────
    fig_fluxo = go.Figure()

    for cenario in cenarios:
        fluxos = resultados[cenario]["fluxos"]
        acum   = []
        soma   = 0.0
        for fc in fluxos:
            soma += fc
            acum.append(soma)

        meses = list(range(len(acum)))

        fig_fluxo.add_trace(go.Scatter(
            x=meses,
            y=acum,
            mode="lines",
            name=cenario,
            line=dict(color=cores_mapa[cenario], width=2.2),
        ))

    fig_fluxo.add_hline(
        y=0,
        line=dict(color=COLOR_MUTED, width=1, dash="dash"),
        annotation_text="Equilíbrio de Caixa",
        annotation_position="right",
    )

    apply_chart_style(fig_fluxo, title="Trajetória do Fluxo de Caixa Acumulado por Cenário", height=420)
    fig_fluxo.update_xaxes(title="Período (Meses)")
    fig_fluxo.update_yaxes(title="Fluxo Acumulado (R$)")
    st.plotly_chart(fig_fluxo, use_container_width=True)

    # ── Destaque do melhor e pior cenário ─────────────────────────────────────
    st.divider()
    vpls_num = {c: resultados[c]["vpl"] for c in cenarios if not math.isnan(resultados[c]["vpl"])}
    if vpls_num:
        melhor = max(vpls_num, key=vpls_num.get)
        pior   = min(vpls_num, key=vpls_num.get)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f'<div class="alert-box alert-success">'
                f'<strong>Cenário Upside ({melhor}):</strong> VPL projetado de {brl(vpls_num[melhor])}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f'<div class="alert-box alert-danger">'
                f'<strong>Cenário Stress ({pior}):</strong> VPL projetado de {brl(vpls_num[pior])}'
                f'</div>',
                unsafe_allow_html=True,
            )

        if "Otimista" in vpls_num and "Pessimista" in vpls_num:
            spread = vpls_num["Otimista"] - vpls_num["Pessimista"]
            st.markdown(
                f'<div class="alert-box alert-warning">'
                f'<strong>Dispersão de Risco (Spread Upside vs. Stress):</strong> {brl(spread)} '
                f'de amplitude total no Valor Presente Líquido.'
                f'</div>',
                unsafe_allow_html=True,
            )

else:
    st.info("Configure o Caso Base na barra lateral e acione Processar Matriz de Cenários.")
    st.markdown(
        """
        ### Metodologia de Stress Testing e Cenários

        A avaliação multi-cenário submete o fluxo de caixa a choques simultâneos nos vetores de receita, vacância, custos operacionais e custo de oportunidade:

        | Vetor de Risco | Pessimista (Stress) | Realista (Base Case) | Otimista (Upside) |
        |---|---|---|---|
        | **Receita Locatícia** | × 0,85 | × 1,00 | × 1,15 |
        | **Taxa de Vacância** | × 1,50 | × 1,00 | × 0,50 |
        | **Encargos Operacionais (OPEX)** | × 1,20 | × 1,00 | × 0,85 |
        | **Taxa Mínima de Atratividade (TMA)** | × 1,30 | × 1,00 | × 0,80 |
        """
    )
