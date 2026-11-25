"""
Página 6 — Estruturação de Financiamento e Alavancagem
Compara os sistemas SAC e PRICE e calcula o Custo Efetivo Total (CET) via Newton-Raphson.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.calculos import calcular_cet_financiamento, tabela_price, tabela_sac
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
    page_title="Estruturação de Financiamento | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Estado de sessão ──────────────────────────────────────────────────────────
if "fin_ativo" not in st.session_state:
    st.session_state.fin_ativo = False

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Estruturação de Dívida e Sistemas de Amortização (SAC / PRICE)",
    subtitle="Cronograma de serviço da dívida, exposição de saldo devedor e Custo Efetivo Total (CET) via Método de Newton-Raphson.",
    category="DEBT STRUCTURING & LEVERAGE",
    code="MOD-06",
)

# ── Sidebar — entradas ────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand("Debt Structuring")
    st.markdown('<div class="sidebar-section-label">Condições de Crédito</div>', unsafe_allow_html=True)

    valor_imovel = st.number_input(
        "Valor de Avaliação do Ativo (R$)",
        min_value=0.0,
        value=500_000.0,
        step=5_000.0,
        format="%.2f",
    )

    entrada_pct = st.slider(
        "Recursos Próprios / Equity (%)",
        min_value=0,
        max_value=80,
        value=20,
        step=1,
    )

    entrada_valor = valor_imovel * entrada_pct / 100.0
    valor_financiado = valor_imovel - entrada_valor
    st.caption(f"Principal Financiado (LTV {100 - entrada_pct}%): **{brl(valor_financiado)}**")

    taxa_anual_pct = st.number_input(
        "Taxa Nominal de Juros (% a.a.)",
        min_value=0.0,
        value=10.5,
        step=0.1,
        format="%.2f",
    )

    prazo_anos = st.slider(
        "Prazo de Amortização (anos)",
        min_value=1,
        max_value=35,
        value=20,
        step=1,
    )

    with st.expander("Encargos Acessórios para Cálculo do CET", expanded=False):
        custos_iniciais = st.number_input(
            "Tarifa de Estruturação / Avaliação (R$)",
            min_value=0.0,
            value=3_500.0,
            step=500.0,
            format="%.2f",
        )
        encargos_mensais = st.number_input(
            "Seguros Obrigatórios (MIP/DFI) + Taxa Admin (R$/mês)",
            min_value=0.0,
            value=145.0,
            step=10.0,
            format="%.2f",
        )

    sistema = st.radio(
        "Modalidade de Amortização",
        options=["SAC", "PRICE", "Comparar Ambos"],
        index=0,
    )

    st.divider()
    if st.button("Estruturar Operação", type="primary", use_container_width=True):
        st.session_state.fin_ativo = True

# ── Simulação ─────────────────────────────────────────────────────────────────
if st.session_state.fin_ativo:
    taxa_mensal = (1.0 + taxa_anual_pct / 100.0) ** (1.0 / 12.0) - 1.0
    n_parcelas  = prazo_anos * 12

    with st.spinner("Calculando cronogramas de amortização e CET via Newton-Raphson..."):
        tab_sac   = tabela_sac(valor_financiado, taxa_mensal, n_parcelas)
        tab_price = tabela_price(valor_financiado, taxa_mensal, n_parcelas)
        cet_m_sac, cet_a_sac, hist_cet_sac = calcular_cet_financiamento(
            valor_financiado, tab_sac, custos_iniciais, encargos_mensais
        )
        cet_m_price, cet_a_price, hist_cet_price = calcular_cet_financiamento(
            valor_financiado, tab_price, custos_iniciais, encargos_mensais
        )

    df_sac   = pd.DataFrame(tab_sac)
    df_price = pd.DataFrame(tab_price)

    total_pago_sac   = df_sac["parcela"].sum()
    total_pago_price = df_price["parcela"].sum()
    juros_sac        = df_sac["juros"].sum()
    juros_price      = df_price["juros"].sum()

    # ── Comparação de ambos os sistemas ───────────────────────────────────────
    if sistema == "Comparar Ambos":
        st.subheader("Análise Comparativa: SAC vs. PRICE")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("1ª Prestação SAC", brl(df_sac.iloc[0]["parcela"]), delta=f"CET: {pct(cet_a_sac)} a.a.", delta_color="off")
        with c2:
            st.metric("Prestação Fixa PRICE", brl(df_price.iloc[0]["parcela"]), delta=f"CET: {pct(cet_a_price)} a.a.", delta_color="off")
        with c3:
            st.metric("Custo Total de Juros (SAC)", brl(juros_sac),
                      delta=brl(juros_sac - juros_price),
                      delta_color="inverse")
        with c4:
            st.metric("Custo Total de Juros (PRICE)", brl(juros_price))

        st.divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_parcela = go.Figure()
            fig_parcela.add_trace(go.Scatter(
                x=df_sac["mes"],
                y=df_sac["parcela"],
                mode="lines",
                name="SAC",
                line=dict(color=COLOR_GOLD, width=2),
            ))
            fig_parcela.add_trace(go.Scatter(
                x=df_price["mes"],
                y=df_price["parcela"],
                mode="lines",
                name="PRICE",
                line=dict(color=COLOR_POS, width=2),
            ))
            apply_chart_style(fig_parcela, title="Trajetória das Prestações Mensais", height=380)
            fig_parcela.update_xaxes(title="Mês")
            fig_parcela.update_yaxes(title="Prestação (R$)")
            st.plotly_chart(fig_parcela, use_container_width=True)

        with col_g2:
            fig_saldo = go.Figure()
            fig_saldo.add_trace(go.Scatter(
                x=df_sac["mes"],
                y=df_sac["saldo_devedor"],
                mode="lines",
                name="SAC",
                line=dict(color=COLOR_GOLD, width=2),
                fill="tozeroy",
                fillcolor="rgba(197, 160, 89, 0.07)",
            ))
            fig_saldo.add_trace(go.Scatter(
                x=df_price["mes"],
                y=df_price["saldo_devedor"],
                mode="lines",
                name="PRICE",
                line=dict(color=COLOR_POS, width=2),
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.07)",
            ))
            apply_chart_style(fig_saldo, title="Curva de Desalavancagem (Saldo Devedor)", height=380)
            fig_saldo.update_xaxes(title="Mês")
            fig_saldo.update_yaxes(title="Saldo Devedor (R$)")
            st.plotly_chart(fig_saldo, use_container_width=True)

        fig_bar = go.Figure()
        categorias = ["Juros Acumulados", "Desembolso Total"]
        fig_bar.add_trace(go.Bar(
            name="SAC",
            x=categorias,
            y=[juros_sac, total_pago_sac],
            marker_color=COLOR_GOLD,
            text=[brl(juros_sac), brl(total_pago_sac)],
            textposition="outside",
            textfont=dict(color="#F8FAFC", size=11, family="JetBrains Mono, monospace"),
        ))
        fig_bar.add_trace(go.Bar(
            name="PRICE",
            x=categorias,
            y=[juros_price, total_pago_price],
            marker_color=COLOR_POS,
            text=[brl(juros_price), brl(total_pago_price)],
            textposition="outside",
            textfont=dict(color="#F8FAFC", size=11, family="JetBrains Mono, monospace"),
        ))
        apply_chart_style(fig_bar, title="Comparativo de Juros e Desembolso Total", height=380)
        fig_bar.update_layout(barmode="group")
        fig_bar.update_yaxes(title="Montante (R$)")
        st.plotly_chart(fig_bar, use_container_width=True)

        economia = juros_price - juros_sac
        if economia > 0:
            st.markdown(
                f'<div class="alert-box alert-success"><strong>Eficiência Financeira:</strong> A estrutura <strong>SAC</strong> '
                f'proporciona economia nominal de <strong>{brl(economia)}</strong> em encargos financeiros frente à Tabela PRICE.</div>',
                unsafe_allow_html=True,
            )

    # ── Sistema único (SAC ou PRICE) ─────────────────────────────────────────
    else:
        df      = df_sac   if sistema == "SAC"   else df_price
        total   = total_pago_sac   if sistema == "SAC" else total_pago_price
        juros   = juros_sac        if sistema == "SAC" else juros_price
        cet_a   = cet_a_sac        if sistema == "SAC" else cet_a_price
        cet_m   = cet_m_sac        if sistema == "SAC" else cet_m_price
        hist_c  = hist_cet_sac     if sistema == "SAC" else hist_cet_price
        titulo  = "SAC — Sistema de Amortização Constante" if sistema == "SAC" \
                  else "PRICE — Sistema Francês de Amortização"

        st.subheader(titulo)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("1ª Prestação", brl(df.iloc[0]["parcela"]))
        with c2:
            if sistema == "SAC":
                st.metric("Última Prestação", brl(df.iloc[-1]["parcela"]))
            else:
                st.metric("Prestação Constante", brl(df.iloc[0]["parcela"]))
        with c3:
            st.metric("Desembolso Total", brl(total))
        with c4:
            st.metric("Juros Totais", brl(juros))
        with c5:
            st.metric("CET Anual (Newton-Raphson)", pct(cet_a), delta=f"{pct(cet_m)} a.m.", delta_color="off")

        st.divider()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["mes"],
            y=df["saldo_devedor"],
            mode="lines",
            name="Saldo Devedor",
            line=dict(color=COLOR_MUTED, width=1.8, dash="dot"),
            yaxis="y2",
            fill="tozeroy",
            fillcolor="rgba(148, 163, 184, 0.06)",
        ))
        fig.add_trace(go.Bar(
            x=df["mes"],
            y=df["amortizacao"],
            name="Quota de Amortização",
            marker_color=COLOR_POS,
            opacity=0.85,
        ))
        fig.add_trace(go.Bar(
            x=df["mes"],
            y=df["juros"],
            name="Encargos de Juros",
            marker_color=COLOR_NEG,
            opacity=0.85,
        ))
        apply_chart_style(fig, title="Decomposição das Prestações e Evolução do Saldo Devedor", height=420)
        fig.update_layout(
            barmode="stack",
            yaxis2=dict(
                title="Saldo Devedor (R$)",
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(color=COLOR_MUTED, family="JetBrains Mono, monospace"),
            ),
            margin=dict(l=55, r=65, t=55, b=45),
        )
        fig.update_xaxes(title="Mês")
        fig.update_yaxes(title="Prestação (R$)")
        st.plotly_chart(fig, use_container_width=True)

        if hist_c:
            with st.expander(f"Auditoria Numérica — Cálculo do CET via Newton-Raphson ({len(hist_c)} iterações)"):
                st.caption("O Custo Efetivo Total (CET) corresponde à Taxa Interna de Retorno do fluxo líquido de desembolso da operação de crédito:")
                st.dataframe(pd.DataFrame(hist_c), use_container_width=True, hide_index=True)

        st.divider()

        # ── Tabela de amortização (paginada — 24 linhas por vez) ──────────────
        st.subheader("Cronograma Analítico de Amortização")

        total_paginas = max((len(df) - 1) // 24 + 1, 1)
        pagina = st.number_input(
            f"Página do Cronograma (1 a {total_paginas})",
            min_value=1,
            max_value=total_paginas,
            value=1,
            step=1,
        )

        inicio = (pagina - 1) * 24
        fim    = inicio + 24
        df_pag = df.iloc[inicio:fim].copy()

        df_pag["parcela"]       = df_pag["parcela"].apply(brl)
        df_pag["amortizacao"]   = df_pag["amortizacao"].apply(brl)
        df_pag["juros"]         = df_pag["juros"].apply(brl)
        df_pag["saldo_devedor"] = df_pag["saldo_devedor"].apply(brl)
        df_pag = df_pag.rename(columns={
            "mes":          "Competência (Mês)",
            "parcela":      "Prestação Total",
            "amortizacao":  "Amortização Principal",
            "juros":        "Juros Contratuais",
            "saldo_devedor":"Saldo Devedor Remanescente",
        })

        st.dataframe(df_pag, use_container_width=True, hide_index=True)
        st.caption(f"Exibindo registros {inicio + 1} a {min(fim, len(df))} de {len(df)} competências — Página {pagina} de {total_paginas}.")

else:
    st.info("Configure as condições de crédito na barra lateral e acione Estruturar Operação.")
    st.markdown(
        """
        ### Comparativo Técnico das Modalidades de Amortização

        | Parâmetro Estrutural | SAC (Amortização Constante) | Tabela PRICE (Sistema Francês) |
        |---|---|---|
        | **Quota de Amortização** | Constante ao longo do contrato | Crescente (exponencial) |
        | **Serviço Mensal (Prestação)** | Linearmente decrescente | Constante (fixa) |
        | **Custo Total de Juros** | Inferior (desalavancagem acelerada) | Superior (amortização inicial lenta) |
        | **Exposição Inicial de Caixa** | Mais elevada nas primeiras competências | Mais suave no início da operação |
        """
    )
