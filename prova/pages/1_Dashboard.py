"""
Dashboard Executivo — ImobiInvest Pro
Visão consolidada do portfólio de empreendimentos imobiliários.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database import listar_empreendimentos, custo_total, popular_dados_exemplo
from utils.formatters import brl
from utils.ui import (
    load_css,
    render_sidebar_brand,
    render_header,
    apply_chart_style,
    INSTITUTIONAL_PALETTE,
    COLOR_GOLD,
    COLOR_BLUE,
)

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Executivo | ImobiInvest Pro",
    layout="wide",
)

load_css()

with st.sidebar:
    render_sidebar_brand("Portfolio Intelligence")
    st.caption("Consolidação patrimonial, alocação setorial e curva de desembolso de capital (CAPEX).")

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Dashboard Executivo de Portfólio",
    subtitle="Monitoramento consolidado de alocação de capital, exposição por tipologia e evolução patrimonial.",
    category="PORTFOLIO INTELLIGENCE",
    code="MOD-01",
)

# ── Carregamento de dados ─────────────────────────────────────────────────────
empreendimentos = listar_empreendimentos()

if not empreendimentos:
    st.info(
        "Nenhum ativo registrado na base de dados. "
        "Acesse o módulo Empreendimentos para cadastrar novos ativos ou inicialize a carteira demonstrativa."
    )
    if st.button("Inicializar Carteira Demonstrativa", type="primary"):
        popular_dados_exemplo()
        st.rerun()
    st.stop()

for emp in empreendimentos:
    emp["custo_total_calc"] = custo_total(emp)

df = pd.DataFrame(empreendimentos)

# ── KPIs ──────────────────────────────────────────────────────────────────────
capital_total = df["custo_total_calc"].sum()
ticket_medio = df["custo_total_calc"].mean()
n_imoveis = len(df)
tipos_unicos = df["tipo"].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Capital Total Alocado (CAPEX)", value=brl(capital_total))
col2.metric(label="Ticket Médio por Ativo", value=brl(ticket_medio))
col3.metric(label="Ativos em Carteira", value=str(n_imoveis))
col4.metric(label="Segmentos Imobiliários", value=str(tipos_unicos))

st.divider()

# ── Tabs de gráficos ──────────────────────────────────────────────────────────
aba_resumo, aba_imovel, aba_evolucao = st.tabs([
    "Alocação por Tipologia",
    "Exposição por Ativo",
    "Evolução de Capital Alocado",
])

# ── Aba 1: Resumo — Rosca institucional ───────────────────────────────────────
with aba_resumo:
    col_p1, col_p2 = st.columns([3, 2])
    with col_p1:
        contagem_tipo = (
            df.groupby("tipo")
            .agg(quantidade=("id", "count"), volume=("custo_total_calc", "sum"))
            .reset_index()
            .sort_values("volume", ascending=False)
        )

        fig_pizza = px.pie(
            contagem_tipo,
            names="tipo",
            values="volume",
            color_discrete_sequence=INSTITUTIONAL_PALETTE,
            hole=0.52,
        )
        fig_pizza.update_traces(
            textfont=dict(color="#F8FAFC", size=11, family="JetBrains Mono, monospace"),
            textinfo="percent+label",
            marker=dict(line=dict(color="#0A0E17", width=2)),
            hovertemplate="<b>%{label}</b><br>Volume: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>",
        )
        apply_chart_style(fig_pizza, title="Distribuição Financeira por Tipologia de Ativo", height=400)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_p2:
        st.markdown('<p class="section-title">Quadro de Alocação Setorial</p>', unsafe_allow_html=True)
        df_setor = pd.DataFrame({
            "Tipologia": contagem_tipo["tipo"],
            "Ativos": contagem_tipo["quantidade"],
            "Capital Alocado": contagem_tipo["volume"].apply(brl),
            "Participação": (contagem_tipo["volume"] / capital_total * 100).apply(lambda v: f"{v:.1f}%"),
        })
        st.dataframe(df_setor, use_container_width=True, hide_index=True)

# ── Aba 2: Por Imóvel — Barras de valor ───────────────────────────────────────
with aba_imovel:
    df_sorted = df.sort_values("custo_total_calc", ascending=False)

    fig_barras = go.Figure(
        go.Bar(
            x=df_sorted["nome"],
            y=df_sorted["custo_total_calc"],
            marker=dict(
                color=COLOR_GOLD,
                line=dict(color="#D4B475", width=1),
            ),
            text=[brl(v) for v in df_sorted["custo_total_calc"]],
            textposition="outside",
            textfont=dict(color="#F8FAFC", size=11, family="JetBrains Mono, monospace"),
            hovertemplate="<b>%{x}</b><br>Custo Total: R$ %{y:,.2f}<extra></extra>",
        )
    )
    apply_chart_style(
        fig_barras,
        title="Exposição de Capital por Ativo Imobiliário (Ordem Decrescente)",
        height=420,
        showlegend=False,
    )
    fig_barras.update_xaxes(title="Ativo Imobiliário", tickangle=-20)
    fig_barras.update_yaxes(title="Capital Alocado (R$)")
    st.plotly_chart(fig_barras, use_container_width=True)

# ── Aba 3: Evolução — Linha cumulativa por mês ───────────────────────────────
with aba_evolucao:
    df_tempo = df[["data_aquisicao", "custo_total_calc"]].copy()
    df_tempo["data_aquisicao"] = pd.to_datetime(df_tempo["data_aquisicao"], errors="coerce")
    df_tempo = df_tempo.dropna(subset=["data_aquisicao"])

    if df_tempo.empty:
        st.warning(
            "Nenhum empreendimento possui data de aquisição registrada. "
            "Cadastre as datas para visualizar a curva de desembolso histórico."
        )
    else:
        df_tempo["mes"] = df_tempo["data_aquisicao"].dt.to_period("M").dt.to_timestamp()
        df_mensal = (
            df_tempo.groupby("mes")["custo_total_calc"]
            .sum()
            .reset_index()
            .sort_values("mes")
        )
        df_mensal["capital_acumulado"] = df_mensal["custo_total_calc"].cumsum()

        fig_linha = go.Figure()
        fig_linha.add_trace(
            go.Scatter(
                x=df_mensal["mes"],
                y=df_mensal["capital_acumulado"],
                mode="lines+markers",
                name="Capital Acumulado",
                line=dict(color=COLOR_GOLD, width=2.5),
                marker=dict(color=COLOR_GOLD, size=7, line=dict(color="#0A0E17", width=1.5)),
                fill="tozeroy",
                fillcolor="rgba(197, 160, 89, 0.10)",
                hovertemplate="<b>%{x|%b/%Y}</b><br>Capital Acumulado: R$ %{y:,.2f}<extra></extra>",
            )
        )
        apply_chart_style(
            fig_linha,
            title="Evolução Histórica do Capital Alocado (CAPEX Acumulado)",
            height=420,
            showlegend=False,
        )
        fig_linha.update_xaxes(title="Competência", tickformat="%b/%Y")
        fig_linha.update_yaxes(title="Capital Acumulado (R$)")
        st.plotly_chart(fig_linha, use_container_width=True)
