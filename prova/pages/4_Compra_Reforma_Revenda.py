"""
Compra, Reforma e Revenda (House Flipping) — ImobiInvest Pro
Análise de viabilidade de desinvestimento imobiliário com Break-Even via Bisseção.
"""

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import listar_empreendimentos, salvar_simulacao
from utils.calculos import break_even_venda_detalhado, resultado_flip
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
    page_title="Desinvestimento & Flip | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Estado de sessão ──────────────────────────────────────────────────────────
if "flip_resultado" not in st.session_state:
    st.session_state.flip_resultado = None
if "flip_params" not in st.session_state:
    st.session_state.flip_params = {}
if "flip_hist_be" not in st.session_state:
    st.session_state.flip_hist_be = []

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Estruturação de Compra, Retrofit e Desinvestimento (Flip)",
    subtitle="Decomposição de margem líquida em cascata, tributação sobre ganho de capital e preço crítico de saída via Bisseção.",
    category="CAPITAL GAIN & EXIT STRATEGY",
    code="MOD-04",
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Parâmetros do flip
# ─────────────────────────────────────────────────────────────────────────────
empreendimentos = listar_empreendimentos()

with st.sidebar:
    render_sidebar_brand("Exit Strategy")
    st.markdown('<div class="sidebar-section-label">Parâmetros da Operação</div>', unsafe_allow_html=True)

    opcoes_emp = ["— Sem vínculo —"] + [f"{e['id']} — {e['nome']}" for e in empreendimentos]
    emp_selecionado_label = st.selectbox("Ativo de Referência", opcoes_emp)

    emp_selecionado = None
    if emp_selecionado_label != "— Sem vínculo —":
        emp_id_sel = int(emp_selecionado_label.split(" — ")[0])
        emp_selecionado = next((e for e in empreendimentos if e["id"] == emp_id_sel), None)

    if "last_emp_flip" not in st.session_state:
        st.session_state.last_emp_flip = emp_selecionado_label
        st.session_state.flip_compra = float(emp_selecionado.get("valor_aquisicao") or 300_000.0) if emp_selecionado else 300_000.0
        st.session_state.flip_reforma = float(emp_selecionado.get("valor_reforma") or 50_000.0) if emp_selecionado else 50_000.0
        st.session_state.flip_outros = (
            float(emp_selecionado.get("valor_documentacao") or 0)
            + float(emp_selecionado.get("valor_itbi") or 0)
            + float(emp_selecionado.get("valor_corretagem") or 0)
            + float(emp_selecionado.get("outros_custos") or 0)
        ) if emp_selecionado else 15_000.0
    elif st.session_state.last_emp_flip != emp_selecionado_label:
        st.session_state.last_emp_flip = emp_selecionado_label
        if emp_selecionado:
            st.session_state.flip_compra = float(emp_selecionado.get("valor_aquisicao") or 0.0)
            st.session_state.flip_reforma = float(emp_selecionado.get("valor_reforma") or 0.0)
            st.session_state.flip_outros = (
                float(emp_selecionado.get("valor_documentacao") or 0)
                + float(emp_selecionado.get("valor_itbi") or 0)
                + float(emp_selecionado.get("valor_corretagem") or 0)
                + float(emp_selecionado.get("outros_custos") or 0)
            )

    st.divider()

    valor_compra = st.number_input(
        "Valor de Aquisição (R$)",
        min_value=0.0,
        step=5_000.0,
        format="%.2f",
        key="flip_compra",
    )
    valor_reforma = st.number_input(
        "Orçamento de Reforma / Retrofit (R$)",
        min_value=0.0,
        step=1_000.0,
        format="%.2f",
        key="flip_reforma",
    )
    outros_custos = st.number_input(
        "Custos Transacionais / ITBI / Cartório (R$)",
        min_value=0.0,
        step=500.0,
        format="%.2f",
        key="flip_outros",
    )
    valor_venda = st.number_input(
        "ValorAlvo de Desinvestimento / Venda (R$)",
        min_value=0.0,
        step=5_000.0,
        format="%.2f",
        value=450_000.0,
    )

    st.divider()

    corretagem_pct_input = st.slider(
        "Comissão de Corretagem na Saída (%)",
        min_value=0,
        max_value=10,
        value=6,
        step=1,
    )
    corretagem_pct = corretagem_pct_input / 100.0

    imposto_pct_input = st.slider(
        "Alíquota sobre Ganho de Capital (%)",
        min_value=0,
        max_value=30,
        value=15,
        step=1,
    )
    imposto_pct = imposto_pct_input / 100.0

    st.divider()
    analisar = st.button("Avaliar Operação", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────
if analisar:
    with st.spinner("Calculando estrutura de resultado e preço de equilíbrio via Bisseção..."):
        resultado = resultado_flip(
            valor_compra=valor_compra,
            valor_reforma=valor_reforma,
            outros_custos=outros_custos,
            valor_venda=valor_venda,
            corretagem_pct=corretagem_pct,
            imposto_pct=imposto_pct,
        )
        be_venda, hist_be = break_even_venda_detalhado(
            custo_total=resultado["custo_total"],
            corretagem_pct=corretagem_pct,
            imposto_pct=imposto_pct,
        )
        resultado["break_even_venda"] = be_venda

    st.session_state.flip_resultado = resultado
    st.session_state.flip_hist_be = hist_be
    st.session_state.flip_params = {
        "valor_compra": valor_compra,
        "valor_reforma": valor_reforma,
        "outros_custos": outros_custos,
        "valor_venda": valor_venda,
        "corretagem_pct": corretagem_pct,
        "imposto_pct": imposto_pct,
    }

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.flip_resultado is None:
    st.info("Configure os parâmetros da operação no painel lateral e acione Avaliar Operação.")
    st.stop()

res = st.session_state.flip_resultado
params = st.session_state.flip_params
hist_be = st.session_state.flip_hist_be

lucro_liq = res["lucro_liquido"]
cor_lucro = COLOR_POS if lucro_liq >= 0 else COLOR_NEG

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.subheader("Síntese Financeira da Operação")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    label="Capital Total Alocado (CAPEX)",
    value=brl(res["custo_total"]),
)
kpi2.metric(
    label="Resultado Líquido (Pós-IR)",
    value=brl(lucro_liq),
    delta="Operação Superavitária" if lucro_liq >= 0 else "Operação Deficitária",
    delta_color="normal" if lucro_liq >= 0 else "inverse",
)
kpi3.metric(
    label="Retorno Sobre Capital (ROI)",
    value=pct(res["roi"]),
    delta="Acima do CAPEX" if res["roi"] > 0 else "Abaixo do CAPEX",
    delta_color="normal" if res["roi"] > 0 else "inverse",
)
kpi4.metric(
    label="Preço Mínimo de Saída (Bisseção)",
    value=brl(res["break_even_venda"]) if res["break_even_venda"] != float("inf") else "Inviável",
    delta=f"{len(hist_be)} iterações",
    delta_color="off",
)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 1 — Cascata (Waterfall)
# ─────────────────────────────────────────────────────────────────────────────
corretagem_val = params["valor_venda"] * params["corretagem_pct"]
imposto_val = res["imposto"]

waterfall_labels = [
    "Aquisição",
    "Retrofit",
    "Custos Transacionais",
    "Corretagem",
    "Imposto (Ganho Capital)",
    "Receita de Venda",
    "Lucro Líquido",
]
waterfall_values = [
    -params["valor_compra"],
    -params["valor_reforma"],
    -params["outros_custos"],
    -corretagem_val,
    -imposto_val,
    params["valor_venda"],
    lucro_liq,
]
waterfall_measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"]

fig_waterfall = go.Figure(
    go.Waterfall(
        name="Resultado",
        orientation="v",
        measure=waterfall_measure,
        x=waterfall_labels,
        y=waterfall_values,
        texttemplate="%{text}",
        text=[brl(abs(v)) for v in waterfall_values],
        textposition="outside",
        textfont=dict(color="#F8FAFC", size=11, family="JetBrains Mono, monospace"),
        connector=dict(line=dict(color="#334155", width=1)),
        increasing={"marker": {"color": COLOR_POS}},
        decreasing={"marker": {"color": COLOR_NEG}},
        totals={"marker": {"color": cor_lucro}},
        hovertemplate="<b>%{x}</b><br>Montante: R$ %{y:,.2f}<extra></extra>",
    )
)
apply_chart_style(fig_waterfall, title="Decomposição de Margem da Operação (Waterfall)", height=420, showlegend=False)
fig_waterfall.update_yaxes(title="Montante (R$)")
st.plotly_chart(fig_waterfall, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Gráfico 2 — Curva de Break-Even
# ─────────────────────────────────────────────────────────────────────────────
custo_tot = res["custo_total"]
be = res["break_even_venda"]

n_pontos = 200
venda_min = max(custo_tot * 0.5, 0.0)
venda_max = max(custo_tot * 2.0, params["valor_venda"] * 1.3, 10_000.0)
vendas = [venda_min + i * (venda_max - venda_min) / (n_pontos - 1) for i in range(n_pontos)]

lucros = [
    resultado_flip(
        valor_compra=params["valor_compra"],
        valor_reforma=params["valor_reforma"],
        outros_custos=params["outros_custos"],
        valor_venda=v,
        corretagem_pct=params["corretagem_pct"],
        imposto_pct=params["imposto_pct"],
    )["lucro_liquido"]
    for v in vendas
]

fig_be = go.Figure()
fig_be.add_trace(
    go.Scatter(
        x=vendas,
        y=lucros,
        mode="lines",
        name="Lucro Líquido Projetado",
        line=dict(color=COLOR_GOLD, width=2.5),
        hovertemplate="Preço de Venda: R$ %{x:,.2f}<br>Lucro Líquido: R$ %{y:,.2f}<extra></extra>",
    )
)

if be != float("inf"):
    fig_be.add_vline(
        x=be,
        line=dict(color=COLOR_MUTED, width=1.5, dash="dash"),
        annotation_text=f"Break-even: {brl(be)}",
        annotation_font_color=COLOR_MUTED,
        annotation_position="top right",
    )

fig_be.add_hline(y=0, line=dict(color="#334155", width=1.5, dash="dot"))

fig_be.add_trace(
    go.Scatter(
        x=[params["valor_venda"]],
        y=[lucro_liq],
        mode="markers",
        name="Preço Alvo Atual",
        marker=dict(
            color=cor_lucro,
            size=11,
            symbol="diamond",
            line=dict(color="#F8FAFC", width=1.5),
        ),
        hovertemplate=(
            f"<b>Preço Alvo Atual</b><br>"
            f"Venda: {brl(params['valor_venda'])}<br>"
            f"Lucro Líquido: {brl(lucro_liq)}<extra></extra>"
        ),
    )
)

apply_chart_style(fig_be, title="Sensibilidade do Lucro Líquido ao Preço de Saída", height=400)
fig_be.update_xaxes(title="Valor de Venda (R$)", tickformat=",.0f")
fig_be.update_yaxes(title="Lucro Líquido (R$)")
st.plotly_chart(fig_be, use_container_width=True)

# ── Detalhamento Numérico da Bisseção ─────────────────────────────────────────
if hist_be:
    with st.expander(f"Auditoria Numérica — Convergência do Método da Bisseção ({len(hist_be)} iterações)"):
        st.caption("Determinação da raiz da função não-linear `Lucro_Líquido(Preço_Venda) = 0` considerando tributação progressiva sobre lucro positivo:")
        st.dataframe(pd.DataFrame(hist_be), use_container_width=True, hide_index=True)

# ── Salvar Simulação ──────────────────────────────────────────────────────────
st.divider()
if emp_selecionado is not None:
    if st.button("Arquivar Operação de Flip no Dossiê do Ativo", type="primary"):
        sim_data = {
            "tipo": "Flip (Compra, Reforma e Revenda)",
            **params,
            "custo_total": res["custo_total"],
            "corretagem": res["corretagem"],
            "lucro_bruto": res["lucro_bruto"],
            "imposto": res["imposto"],
            "lucro_liquido": res["lucro_liquido"],
            "roi": res["roi"],
            "break_even_venda": res["break_even_venda"] if not math.isinf(res["break_even_venda"]) else None,
        }
        salvar_simulacao(emp_selecionado["id"], sim_data)
        st.success(f"Análise de desinvestimento arquivada para o ativo '{emp_selecionado['nome']}'.")
else:
    st.caption("Selecione um Ativo de Referência no painel lateral para arquivar esta análise no relatório executivo.")
