"""
ImobiInvest Pro — Plataforma Institucional de Análise de Investimentos Imobiliários
Arquivo principal (entrypoint) da aplicação Streamlit multipáginas.
Execute com: streamlit run app.py
"""
import streamlit as st

from database import listar_empreendimentos, custo_total, popular_dados_exemplo
from utils.formatters import brl, pct
from utils.calculos import fluxo_locacao, indicadores_locacao, vpl_continuo_locacao, break_even_locacao
from utils.ui import load_css, render_sidebar_brand, render_header

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="ImobiInvest Pro | Institutional Real Estate Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand("Institutional Real Estate")
    st.markdown('<div class="sidebar-section-label">Arquitetura Quantitativa</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.65;">
            <div><strong style="color: #F8FAFC;">01. Newton-Raphson</strong><br>Cálculo de TIR e CET Efetivo</div>
            <div style="margin-top: 8px;"><strong style="color: #F8FAFC;">02. Método da Bisseção</strong><br>Break-Even e Ocupação Mínima</div>
            <div style="margin-top: 8px;"><strong style="color: #F8FAFC;">03. Regra dos Trapézios</strong><br>Integração de Fluxo Contínuo</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    emps_sidebar = listar_empreendimentos()
    if not emps_sidebar:
        if st.button("Carregar Portfólio Institucional", type="primary", use_container_width=True):
            popular_dados_exemplo()
            st.rerun()

# ── Cabeçalho Executivo ───────────────────────────────────────────────────────
render_header(
    title="Terminal Executivo de Viabilidade Imobiliária",
    subtitle="Análise quantitativa de portfólio, modelagem de fluxo de caixa descontado e métodos numéricos proprietários.",
    category="EXECUTIVE OVERVIEW",
    code="SYS-CORE",
)

# ── KPIs do Portfólio ─────────────────────────────────────────────────────────
empreendimentos = listar_empreendimentos()
capital_total = sum(custo_total(e) for e in empreendimentos)
n_imoveis = len(empreendimentos)
ticket_medio = capital_total / n_imoveis if n_imoveis > 0 else 0.0
area_total = sum(float(e.get("area_m2") or 0) for e in empreendimentos)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ativos Sob Gestão (AUM)", str(n_imoveis))
c2.metric("Capital Total Alocado", brl(capital_total))
c3.metric("Ticket Médio por Ativo", brl(ticket_medio))
c4.metric("Área Bruta Locável (ABL)", f"{area_total:,.1f} m²".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

# ── Demonstração da Engine Matemática ─────────────────────────────────────────
st.subheader("Arquitetura do Motor Matemático Proprietário")

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown(
        """
        <div class="inst-card" style="min-height: 215px;">
            <div class="inst-card-header">
                <span class="inst-card-title">01. Método de Newton-Raphson</span>
                <span class="inst-card-tag">Convergência Quadrática</span>
            </div>
            <p style="font-size: 0.83rem; color: #94A3B8; line-height: 1.6;">
                Resolve polinômios não-lineares de fluxo de caixa descontado de até 360 períodos:<br>
                <code style="color: #C5A059;">VPL(r) = ∑ FC_t / (1 + r)^t = 0</code><br><br>
                Emprega a derivada analítica exata <code style="color: #F8FAFC;">VPL'(r)</code> para determinar a
                <strong>Taxa Interna de Retorno (TIR)</strong> e o <strong>Custo Efetivo Total (CET)</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        """
        <div class="inst-card" style="min-height: 215px;">
            <div class="inst-card-header">
                <span class="inst-card-title">02. Método da Bisseção</span>
                <span class="inst-card-tag">Convergência Garantida</span>
            </div>
            <p style="font-size: 0.83rem; color: #94A3B8; line-height: 1.6;">
                Determina fronteiras de viabilidade pelo Teorema do Valor Intermediário:<br>
                • <strong>Aluguel Mínimo Econômico</strong> (<code style="color: #C5A059;">VPL(A) = 0</code>)<br>
                • <strong>Aluguel Mínimo Financeiro</strong> (Payback no horizonte)<br>
                • <strong>Taxa Mínima de Ocupação</strong> e <strong>Break-Even de Desinvestimento</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m3:
    st.markdown(
        """
        <div class="inst-card" style="min-height: 215px;">
            <div class="inst-card-header">
                <span class="inst-card-title">03. Regra dos Trapézios Composta</span>
                <span class="inst-card-tag">Erro O(h²)</span>
            </div>
            <p style="font-size: 0.83rem; color: #94A3B8; line-height: 1.6;">
                Integra numericamente o fluxo de caixa contínuo descontado:<br>
                <code style="color: #C5A059;">VPL_cont = -I₀ + ∫₀ᵀ FC(t)·e^(-δt) dt</code><br><br>
                Permite confrontar a modelagem discreta mensal com o <strong>regime contínuo de capitalização</strong>
                em horizontes institucionais de longo prazo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Simulação Instantânea na Home ─────────────────────────────────────────────
with st.expander("Simulador Executivo Instantâneo — Validação da Engine Numérica em Tempo Real", expanded=True):
    st.caption("Ajuste as premissas macroeconômicas e operacionais abaixo para executar simultaneamente os três métodos numéricos:")
    q1, q2, q3, q4 = st.columns(4)
    inv_q = q1.number_input("CAPEX / Investimento (R$)", min_value=50000.0, value=330000.0, step=10000.0)
    alug_q = q2.number_input("Receita Locatícia Mensal (R$)", min_value=500.0, value=2800.0, step=100.0)
    prazo_q = q3.slider("Horizonte de Análise (meses)", 24, 240, 120, 12)
    tma_q = q4.slider("Custo de Capital / TMA (% a.m.)", 0.3, 2.0, 0.8, 0.1) / 100.0

    fl_q = fluxo_locacao(inv_q, alug_q, 0.05, 250.0, 0.06, prazo_q, inv_q * 1.2)
    ind_q = indicadores_locacao(fl_q, tma_q)
    vpl_cont_q, _ = vpl_continuo_locacao(inv_q, alug_q, 0.05, 250.0, 0.06, prazo_q, tma_q, inv_q * 1.2)
    be_q = break_even_locacao(inv_q, 250.0, 0.05, 0.06, prazo_q, tma_q, inv_q * 1.2)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric(
        "TIR Anual (Newton-Raphson)",
        pct(ind_q["tir_anual"]),
        delta=f"{len(ind_q['historico_tir'])} iter. ({ind_q['metodo_tir']})",
        delta_color="off",
    )
    r2.metric(
        "Aluguel Break-Even (Bisseção)",
        brl(be_q["aluguel_economico"]),
        delta=f"{len(be_q['historicos']['Econômico'])} iterações",
        delta_color="off",
    )
    r3.metric(
        "VPL Discreto",
        brl(ind_q["vpl"]),
        delta="Acima da TMA" if ind_q["vpl"] >= 0 else "Abaixo da TMA",
        delta_color="normal" if ind_q["vpl"] >= 0 else "inverse",
    )
    r4.metric(
        "VPL Contínuo (Trapézios)",
        brl(vpl_cont_q),
        delta=f"Spread {brl(vpl_cont_q - ind_q['vpl'])}",
        delta_color="off",
    )

st.divider()

# ── Mapa de Módulos da Plataforma ─────────────────────────────────────────────
st.subheader("Diretório de Módulos Analíticos")

nav1, nav2, nav3, nav4, nav5 = st.columns(5)
with nav1:
    st.page_link("pages/1_Dashboard.py", label="01 · Dashboard", use_container_width=True)
    st.page_link("pages/6_Financiamento.py", label="06 · Financiamento", use_container_width=True)
with nav2:
    st.page_link("pages/2_Empreendimentos.py", label="02 · Portfólio de Ativos", use_container_width=True)
    st.page_link("pages/7_Cenarios.py", label="07 · Cenários Macro", use_container_width=True)
with nav3:
    st.page_link("pages/3_Simulador_Locacao.py", label="03 · Renda Locatícia", use_container_width=True)
    st.page_link("pages/8_Sensibilidade.py", label="08 · Sensibilidade", use_container_width=True)
with nav4:
    st.page_link("pages/4_Compra_Reforma_Revenda.py", label="04 · Desinvestimento / Flip", use_container_width=True)
    st.page_link("pages/9_Laboratorio_Numerico.py", label="09 · Engine Numérica", use_container_width=True)
with nav5:
    st.page_link("pages/5_Break_Even.py", label="05 · Análise Break-Even", use_container_width=True)
    st.page_link("pages/10_Relatorios.py", label="10 · Relatórios Executivos", use_container_width=True)
