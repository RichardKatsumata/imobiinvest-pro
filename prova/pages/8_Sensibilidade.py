"""
Página 8 — Análise de Sensibilidade Paramétrica
Tornado chart e curvas de resposta para mensurar a elasticidade do VPL a cada variável.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.calculos import analise_sensibilidade
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
    page_title="Análise de Sensibilidade | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Análise de Sensibilidade e Elasticidade de VPL (Tornado Analysis)",
    subtitle="Hierarquização de variáveis críticas por impacto no Valor Presente Líquido sob perturbações simétricas.",
    category="PARAMETRIC RISK & ELASTICITY",
    code="MOD-08",
)

# ── Sidebar — entradas ────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand("Risk & Elasticity")
    st.markdown('<div class="sidebar-section-label">Parâmetros de Referência</div>', unsafe_allow_html=True)

    investimento = st.number_input(
        "Capital Investido / CAPEX (R$)",
        min_value=0.0,
        value=300_000.0,
        step=1_000.0,
        format="%.2f",
    )

    aluguel_mensal = st.number_input(
        "Receita Mensal (R$)",
        min_value=0.0,
        value=2_500.0,
        step=50.0,
        format="%.2f",
    )

    taxa_vacancia_pct = st.slider(
        "Taxa de Vacância (%)",
        min_value=0,
        max_value=50,
        value=8,
        step=1,
    )

    despesas_mensais = st.number_input(
        "OPEX Mensal (R$)",
        min_value=0.0,
        value=400.0,
        step=50.0,
        format="%.2f",
    )

    reajuste_anual_pct = st.slider(
        "Reajuste Anual (%)",
        min_value=0,
        max_value=15,
        value=3,
        step=1,
    )

    periodos = st.slider(
        "Horizonte (meses)",
        min_value=12,
        max_value=360,
        value=120,
        step=12,
    )

    tma_mensal_pct = st.number_input(
        "TMA Mensal (%)",
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

    variacao_pct_slider = st.slider(
        "Amplitude de Perturbação (±%)",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
    )

    st.divider()
    analisar = st.button("Executar Análise de Sensibilidade", type="primary", use_container_width=True)

# ── Análise ───────────────────────────────────────────────────────────────────
if analisar:
    taxa_vacancia  = taxa_vacancia_pct  / 100.0
    reajuste_anual = reajuste_anual_pct / 100.0
    tma_mensal     = tma_mensal_pct     / 100.0
    variacao_dec   = variacao_pct_slider / 100.0

    with st.spinner("Calculando matriz jacobiana discreta e amplitudes de VPL..."):
        resultado = analise_sensibilidade(
            investimento=investimento,
            aluguel=aluguel_mensal,
            vacancia=taxa_vacancia,
            despesas=despesas_mensais,
            reajuste_anual=reajuste_anual,
            periodos=periodos,
            tma_mensal=tma_mensal,
            valor_residual=valor_residual,
            variacao_pct=variacao_dec,
            n_pontos=11,
        )

    vpl_base = list(resultado.values())[0]["vpl_base"]

    tornado_rows = []
    for label, dados in resultado.items():
        pontos = dados["pontos"]
        vpls   = [p["vpl"] for p in pontos]
        vpl_min = min(vpls)
        vpl_max = max(vpls)
        amplitude = vpl_max - vpl_min
        amp_rel = abs(amplitude / vpl_base) * 100 if vpl_base != 0 else 0
        tornado_rows.append({
            "label":     label,
            "vpl_min":   vpl_min,
            "vpl_max":   vpl_max,
            "amplitude": amplitude,
            "amp_rel":   amp_rel,
        })

    tornado_rows.sort(key=lambda x: x["amplitude"], reverse=True)
    var_maior = tornado_rows[0]["label"]

    st.markdown(
        f'<div class="alert-box alert-warning">'
        f'<strong>Fator Crítico de Exposição:</strong> A variável <strong>{var_maior}</strong> apresenta '
        f'a maior elasticidade sobre o resultado, gerando oscilação de <strong>{brl(tornado_rows[0]["amplitude"])}</strong> '
        f'({pct(tornado_rows[0]["amp_rel"])} em relação ao |VPL Base|).'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Tornado chart ──────────────────────────────────────────────────────────
    labels   = [r["label"]   for r in tornado_rows]
    vpl_mins = [r["vpl_min"] for r in tornado_rows]
    vpl_maxs = [r["vpl_max"] for r in tornado_rows]

    fig_tornado = go.Figure()

    fig_tornado.add_trace(go.Bar(
        name=f"Limite Inferior de VPL (±{variacao_pct_slider}%)",
        y=labels,
        x=[v - vpl_base for v in vpl_mins],
        orientation="h",
        marker_color=COLOR_NEG,
        marker_opacity=0.85,
        base=vpl_base,
        hovertemplate="<b>%{y}</b><br>VPL Mínimo: %{customdata}<extra></extra>",
        customdata=[brl(v) for v in vpl_mins],
    ))

    fig_tornado.add_trace(go.Bar(
        name=f"Limite Superior de VPL (±{variacao_pct_slider}%)",
        y=labels,
        x=[v - vpl_base for v in vpl_maxs],
        orientation="h",
        marker_color=COLOR_POS,
        marker_opacity=0.85,
        base=vpl_base,
        hovertemplate="<b>%{y}</b><br>VPL Máximo: %{customdata}<extra></extra>",
        customdata=[brl(v) for v in vpl_maxs],
    ))

    fig_tornado.add_vline(
        x=vpl_base,
        line=dict(color=COLOR_GOLD, width=1.5, dash="dash"),
        annotation_text=f"VPL Base: {brl(vpl_base)}",
        annotation_position="top",
        annotation_font_color=COLOR_GOLD,
    )

    apply_chart_style(
        fig_tornado,
        title="Diagrama de Tornado — Amplitude de Impacto no VPL por Fator",
        height=max(360, 58 * len(labels)),
    )
    fig_tornado.update_layout(
        barmode="overlay",
        margin=dict(l=130, r=30, t=55, b=45),
        yaxis=dict(autorange="reversed"),
    )
    fig_tornado.update_xaxes(title="Valor Presente Líquido (R$)")
    st.plotly_chart(fig_tornado, use_container_width=True)

    st.divider()

    # ── Tabela de ranking ──────────────────────────────────────────────────────
    st.subheader("Matriz de Elasticidade e Ranking de Risco")

    df_rank = pd.DataFrame([{
        "Fator de Risco":  r["label"],
        "VPL Mínimo":      brl(r["vpl_min"]),
        "VPL Máximo":      brl(r["vpl_max"]),
        "Amplitude (Δ)":   brl(r["amplitude"]),
        "Elasticidade Relativa (% |VPL Base|)": pct(r["amp_rel"]),
    } for r in tornado_rows])

    st.dataframe(df_rank, use_container_width=True, hide_index=True)

    st.divider()

    # ── Sparklines por parâmetro ───────────────────────────────────────────────
    st.subheader("Curvas de Resposta Univariada")
    st.caption(f"Comportamento do VPL sob perturbação contínua de ±{variacao_pct_slider}% em cada parâmetro isoladamente.")

    items  = [(r["label"], resultado[r["label"]]) for r in tornado_rows]
    n_cols = 2
    rows_spark = [items[i:i + n_cols] for i in range(0, len(items), n_cols)]

    for linha in rows_spark:
        cols = st.columns(n_cols)
        for col_idx, (label, dados) in enumerate(linha):
            with cols[col_idx]:
                pontos = dados["pontos"]
                fatores_pct = [p["fator"] * 100 - 100 for p in pontos]
                vpls_spark  = [p["vpl"] for p in pontos]
                amplitu     = dados["amplitude"]

                cor_spark = COLOR_GOLD if label == var_maior else COLOR_MUTED

                fig_spark = go.Figure()
                fig_spark.add_trace(go.Scatter(
                    x=fatores_pct,
                    y=vpls_spark,
                    mode="lines+markers",
                    name=label,
                    line=dict(color=cor_spark, width=2),
                    marker=dict(size=5, color=cor_spark),
                    hovertemplate="Choque: %{x:.1f}%<br>VPL: %{customdata}<extra></extra>",
                    customdata=[brl(v) for v in vpls_spark],
                ))

                fig_spark.add_hline(y=vpl_base, line=dict(color=COLOR_GOLD, width=1, dash="dot"))
                fig_spark.add_hline(y=0, line=dict(color=COLOR_NEG, width=0.8, dash="dash"))

                apply_chart_style(
                    fig_spark,
                    title=f"{label} — Amplitude: {brl(amplitu)}",
                    height=250,
                    showlegend=False,
                )
                fig_spark.update_xaxes(title="Choque Paramétrico (%)", ticksuffix="%")
                fig_spark.update_yaxes(title="VPL (R$)")
                st.plotly_chart(fig_spark, use_container_width=True)

    st.divider()

    # ── Diagnóstico de Risco ───────────────────────────────────────────────────
    st.subheader("Diagnóstico Institucional de Risco")

    variaveis_risco = [r["label"] for r in tornado_rows if r["vpl_min"] < 0]

    if variaveis_risco:
        lista_risco = ", ".join(f"<strong>{v}</strong>" for v in variaveis_risco)
        st.markdown(
            f'<div class="alert-box alert-danger">'
            f'<strong>Alerta de Reversão de Viabilidade:</strong> Os fatores {lista_risco} possuem potencial '
            f'para levar o VPL a território negativo dentro da banda de estresse de ±{variacao_pct_slider}%.'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="alert-box alert-success">'
            f'<strong>Resiliência Estrutural Confirmada:</strong> Nenhum fator isolado reverte a viabilidade (VPL < 0) '
            f'dentro da banda de perturbação de ±{variacao_pct_slider}%.'
            f'</div>',
            unsafe_allow_html=True,
        )

else:
    st.info("Configure os parâmetros de referência na barra lateral e acione Executar Análise de Sensibilidade.")
    st.markdown(
        r"""
        ### Metodologia de Sensibilidade Univariada (Ceteris Paribus)

        O modelo aplica choques simétricos de $\pm X\%$ em cada variável de entrada mantendo as demais constantes (*ceteris paribus*), ordenando os fatores de risco pela amplitude absoluta induzida no VPL.
        """
    )
