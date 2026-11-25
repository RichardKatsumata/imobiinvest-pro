"""
Simulador de Renda Locatícia — ImobiInvest Pro
Modelagem de fluxo de caixa descontado por renda de aluguel (Newton-Raphson e Trapézios).
"""

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import custo_total, listar_empreendimentos, salvar_simulacao
from utils.calculos import fluxo_locacao, indicadores_locacao, vpl_continuo_locacao
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
    page_title="Simulador de Locação | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Estado de sessão ──────────────────────────────────────────────────────────
if "sim_resultado" not in st.session_state:
    st.session_state.sim_resultado = None
if "sim_fluxos" not in st.session_state:
    st.session_state.sim_fluxos = None
if "sim_params" not in st.session_state:
    st.session_state.sim_params = {}
if "sim_vpl_cont" not in st.session_state:
    st.session_state.sim_vpl_cont = None
if "sim_pts_trap" not in st.session_state:
    st.session_state.sim_pts_trap = []

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Modelagem de Renda Locatícia (Income Valuation)",
    subtitle="Projeção de fluxo de caixa operacional, TIR via Método de Newton-Raphson e VPL Contínuo via Regra dos Trapézios.",
    category="INCOME VALUATION",
    code="MOD-03",
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Parâmetros da simulação
# ─────────────────────────────────────────────────────────────────────────────
empreendimentos = listar_empreendimentos()

with st.sidebar:
    render_sidebar_brand("Income Valuation")
    st.markdown('<div class="sidebar-section-label">Premissas Operacionais</div>', unsafe_allow_html=True)

    opcoes_emp = ["— Sem vínculo —"] + [f"{e['id']} — {e['nome']}" for e in empreendimentos]
    emp_selecionado_label = st.selectbox("Ativo de Referência", opcoes_emp)

    emp_selecionado = None
    if emp_selecionado_label != "— Sem vínculo —":
        emp_id_sel = int(emp_selecionado_label.split(" — ")[0])
        emp_selecionado = next((e for e in empreendimentos if e["id"] == emp_id_sel), None)

    if "last_emp_loc" not in st.session_state:
        st.session_state.last_emp_loc = emp_selecionado_label
        st.session_state.inv_loc_val = custo_total(emp_selecionado) if emp_selecionado else 300_000.0
    elif st.session_state.last_emp_loc != emp_selecionado_label:
        st.session_state.last_emp_loc = emp_selecionado_label
        if emp_selecionado:
            st.session_state.inv_loc_val = custo_total(emp_selecionado)

    st.divider()

    investimento = st.number_input(
        "Investimento Total / CAPEX (R$)",
        min_value=0.0,
        step=10_000.0,
        format="%.2f",
        key="inv_loc_val",
        help="Custo total de aquisição e estruturação do ativo",
    )

    aluguel_mensal = st.number_input(
        "Receita Bruta de Locação (R$/mês)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        value=2_500.0,
    )

    taxa_vacancia_pct = st.slider(
        "Taxa de Vacância Projetada (%)",
        min_value=0,
        max_value=50,
        value=5,
        step=1,
    )
    taxa_vacancia = taxa_vacancia_pct / 100.0

    despesas_mensais = st.number_input(
        "Despesas Operacionais / OPEX (R$/mês)",
        min_value=0.0,
        step=50.0,
        format="%.2f",
        value=300.0,
    )

    reajuste_anual_pct = st.slider(
        "Indexador Anual de Reajuste (%)",
        min_value=0,
        max_value=20,
        value=6,
        step=1,
    )
    reajuste_anual = reajuste_anual_pct / 100.0

    periodos = st.slider(
        "Horizonte de Projeção (meses)",
        min_value=12,
        max_value=360,
        value=120,
        step=12,
    )

    tma_mensal_pct = st.number_input(
        "Custo de Capital / TMA Mensal (%)",
        min_value=0.0,
        step=0.1,
        format="%.2f",
        value=0.80,
    )
    tma_mensal = tma_mensal_pct / 100.0

    valor_residual = st.number_input(
        "Valor Residual de Saída (R$)",
        min_value=0.0,
        step=10_000.0,
        format="%.2f",
        value=0.0,
    )

    st.divider()
    calcular = st.button("Executar Simulação", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────
if calcular:
    with st.spinner("Processando motor numérico (Newton-Raphson e Regra dos Trapézios)..."):
        fluxos = fluxo_locacao(
            investimento=investimento,
            aluguel_mensal=aluguel_mensal,
            taxa_vacancia=taxa_vacancia,
            despesas_mensais=despesas_mensais,
            reajuste_anual=reajuste_anual,
            periodos=periodos,
            valor_residual=valor_residual,
        )
        indicadores = indicadores_locacao(fluxos, tma_mensal)
        vpl_cont, pts_trap = vpl_continuo_locacao(
            investimento=investimento,
            aluguel_mensal=aluguel_mensal,
            taxa_vacancia=taxa_vacancia,
            despesas_mensais=despesas_mensais,
            reajuste_anual=reajuste_anual,
            periodos=periodos,
            tma_mensal=tma_mensal,
            valor_residual=valor_residual,
            n_trapezios=min(periodos * 2, 360),
        )

    st.session_state.sim_resultado = indicadores
    st.session_state.sim_fluxos = fluxos
    st.session_state.sim_vpl_cont = vpl_cont
    st.session_state.sim_pts_trap = pts_trap
    st.session_state.sim_params = {
        "investimento": investimento,
        "aluguel_mensal": aluguel_mensal,
        "taxa_vacancia": taxa_vacancia,
        "despesas_mensais": despesas_mensais,
        "reajuste_anual": reajuste_anual,
        "periodos": periodos,
        "tma_mensal": tma_mensal,
        "valor_residual": valor_residual,
    }

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.sim_resultado is None:
    st.info("Defina as premissas operacionais no painel lateral e acione Executar Simulação.")
    st.stop()

ind = st.session_state.sim_resultado
fluxos = st.session_state.sim_fluxos
vpl_cont = st.session_state.sim_vpl_cont
pts_trap = st.session_state.sim_pts_trap

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.subheader("Indicadores Executivos de Rentabilidade")

vpl_val = ind["vpl"]
tir_anual_val = ind.get("tir_anual", float("nan"))
payback_val = ind["payback_simples"]
payback_desc_val = ind["payback_descontado"]
roi_val = ind["roi"]

vpl_delta_str = "Geração de Valor (VPL > 0)" if vpl_val >= 0 else "Abaixo da TMA (VPL < 0)"
vpl_delta_color = "normal" if vpl_val >= 0 else "inverse"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric(
    label="VPL Discreto",
    value=brl(vpl_val),
    delta=vpl_delta_str,
    delta_color=vpl_delta_color,
)
kpi2.metric(
    label="VPL Contínuo (Trapézios)",
    value=brl(vpl_cont),
    delta=f"Spread {brl(vpl_cont - vpl_val)}",
    delta_color="off",
)
kpi3.metric(
    label="TIR Anual (Newton-Raphson)",
    value=pct(tir_anual_val) if not math.isnan(tir_anual_val) else "—",
    delta=f"{pct(ind.get('tir_mensal', float('nan')))} a.m." if not math.isnan(ind.get("tir_mensal", float("nan"))) else None,
    delta_color="off",
)
kpi4.metric(
    label="Payback Simples / Desc.",
    value=f"{int(payback_val)} meses" if not (math.isinf(payback_val) or math.isnan(payback_val)) else "Não atingido",
    delta=f"Desc.: {int(payback_desc_val)} m" if not (math.isinf(payback_desc_val) or math.isnan(payback_desc_val)) else "Desc.: Não atingido",
    delta_color="off",
)
kpi5.metric(
    label="ROI Acumulado",
    value=pct(roi_val),
)

st.divider()

# ── Tabs de gráficos ──────────────────────────────────────────────────────────
aba_mensal, aba_acumulado, aba_vpl_desc, aba_motor = st.tabs(
    ["Fluxo Operacional Mensal", "Posição Acumulada", "Curva de VPL Descontado", "Auditoria Numérica (NR & Trapézios)"]
)

meses = list(range(len(fluxos)))
fluxos_operacionais = fluxos[1:]
meses_op = list(range(1, len(fluxos_operacionais) + 1))

# ── Aba 1: Fluxo Mensal ───────────────────────────────────────────────────────
with aba_mensal:
    cores_barras = [COLOR_POS if fc >= 0 else COLOR_NEG for fc in fluxos_operacionais]

    fig_mensal = go.Figure(
        go.Bar(
            x=meses_op,
            y=fluxos_operacionais,
            marker_color=cores_barras,
            hovertemplate="Período %{x}<br>Fluxo Líquido: R$ %{y:,.2f}<extra></extra>",
            name="Fluxo Mensal",
        )
    )
    apply_chart_style(fig_mensal, title="Fluxo de Caixa Operacional Líquido por Período", height=400, showlegend=False)
    fig_mensal.update_xaxes(title="Período (Meses)")
    fig_mensal.update_yaxes(title="Fluxo Líquido (R$)")
    st.plotly_chart(fig_mensal, use_container_width=True)

# ── Aba 2: Fluxo Acumulado ────────────────────────────────────────────────────
with aba_acumulado:
    fluxo_acumulado = []
    soma = 0.0
    for fc in fluxos:
        soma += fc
        fluxo_acumulado.append(soma)

    fig_acum = go.Figure()
    fig_acum.add_trace(
        go.Scatter(
            x=meses,
            y=fluxo_acumulado,
            mode="lines",
            name="Saldo Acumulado",
            line=dict(color=COLOR_GOLD, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(197, 160, 89, 0.10)",
            hovertemplate="Mês %{x}<br>Saldo Acumulado: R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig_acum.add_hline(
        y=0,
        line=dict(color="#334155", width=1.5, dash="dot"),
        annotation_text="Ponto de Payback Simples",
        annotation_font_color=COLOR_MUTED,
    )
    apply_chart_style(fig_acum, title="Evolução do Saldo de Caixa Acumulado (Não Descontado)", height=400, showlegend=False)
    fig_acum.update_xaxes(title="Período (Meses)")
    fig_acum.update_yaxes(title="Saldo Acumulado (R$)")
    st.plotly_chart(fig_acum, use_container_width=True)

# ── Aba 3: VPL Descontado ─────────────────────────────────────────────────────
with aba_vpl_desc:
    params = st.session_state.sim_params
    tma = params.get("tma_mensal", 0.01)

    vpl_acum = []
    soma_vpl = 0.0
    for t, fc in enumerate(fluxos):
        fc_desc = fc / (1 + tma) ** t
        soma_vpl += fc_desc
        vpl_acum.append(soma_vpl)

    cor_vpl = COLOR_POS if vpl_acum[-1] >= 0 else COLOR_NEG
    fig_vpl = go.Figure()
    fig_vpl.add_trace(
        go.Scatter(
            x=meses,
            y=vpl_acum,
            mode="lines",
            name="VPL Acumulado",
            line=dict(color=cor_vpl, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.10)" if vpl_acum[-1] >= 0 else "rgba(239, 68, 68, 0.10)",
            hovertemplate="Mês %{x}<br>VPL Acumulado: R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig_vpl.add_hline(
        y=0,
        line=dict(color="#334155", width=1.5, dash="dot"),
        annotation_text="VPL = 0 (Payback Descontado)",
        annotation_font_color=COLOR_MUTED,
    )
    apply_chart_style(fig_vpl, title="Curva de Valor Presente Líquido Acumulado", height=400, showlegend=False)
    fig_vpl.update_xaxes(title="Período (Meses)")
    fig_vpl.update_yaxes(title="VPL Acumulado (R$)")
    st.plotly_chart(fig_vpl, use_container_width=True)

# ── Aba 4: Motor Numérico (Newton-Raphson & Regra dos Trapézios) ─────────────
with aba_motor:
    col_nr, col_trap = st.columns(2)

    with col_nr:
        st.markdown('<p class="section-title">01. Convergência da TIR via Newton-Raphson</p>', unsafe_allow_html=True)
        hist_tir = ind.get("historico_tir", [])
        metodo_tir = ind.get("metodo_tir", "Newton-Raphson")
        st.caption(
            f"Solver ativo: **{metodo_tir}** — Convergência atingida em **{len(hist_tir)} iterações** "
            f"para a equação polinomial $VPL(r) = 0$."
        )
        if hist_tir:
            df_tir_hist = pd.DataFrame(hist_tir)
            st.dataframe(df_tir_hist, use_container_width=True, hide_index=True)
        else:
            st.warning("Não foi possível convergir para uma TIR válida com os fluxos informados.")

    with col_trap:
        st.markdown('<p class="section-title">02. Integração Contínua via Regra dos Trapézios</p>', unsafe_allow_html=True)
        st.caption(
            f"Quadratura numérica de $\\int_0^{{{len(fluxos)-1}}} FC(t) e^{{-\\delta t}} dt$ "
            f"com **{len(pts_trap)-1} subintervalos trapezoidais**."
        )
        if pts_trap:
            df_trap = pd.DataFrame(pts_trap)
            fig_t = go.Figure()
            fig_t.add_trace(
                go.Scatter(
                    x=df_trap["x"],
                    y=df_trap["y"],
                    mode="lines",
                    fill="tozeroy",
                    fillcolor="rgba(16, 185, 129, 0.14)",
                    line=dict(color=COLOR_POS, width=2),
                    name="FC(t)·e^(-δt)",
                )
            )
            apply_chart_style(
                fig_t,
                title=f"Valor Presente Operacional Contínuo = {brl(vpl_cont + st.session_state.sim_params['investimento'])}",
                height=310,
                showlegend=False,
            )
            fig_t.update_xaxes(title="Tempo t (Meses)")
            fig_t.update_yaxes(title="Fluxo Descontado (R$/mês)")
            st.plotly_chart(fig_t, use_container_width=True)

# ── Botão salvar simulação ────────────────────────────────────────────────────
st.divider()

if emp_selecionado is not None:
    if st.button("Arquivar Simulação no Dossiê do Ativo", type="primary"):
        def _clean(val):
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val

        sim_data = {
            "tipo": "Simulação de Locação",
            **st.session_state.sim_params,
            "vpl": _clean(ind["vpl"]),
            "vpl_continuo": _clean(vpl_cont),
            "tir_mensal": _clean(ind.get("tir_mensal")),
            "tir_anual": _clean(ind.get("tir_anual")),
            "payback_simples": _clean(ind["payback_simples"]),
            "payback_descontado": _clean(ind["payback_descontado"]),
            "roi": _clean(ind["roi"]),
        }
        salvar_simulacao(emp_selecionado["id"], sim_data)
        st.success(f"Simulação vinculada e arquivada para o ativo '{emp_selecionado['nome']}'.")
else:
    st.caption("Selecione um Ativo de Referência no painel lateral para arquivar esta simulação no relatório executivo.")
