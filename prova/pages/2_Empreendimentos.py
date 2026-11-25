"""
Gestão de Portfólio de Empreendimentos — ImobiInvest Pro
CRUD completo de ativos imobiliários na carteira institucional.
"""

import streamlit as st
import pandas as pd
from datetime import date

from database import (
    listar_empreendimentos,
    buscar_empreendimento,
    inserir_empreendimento,
    atualizar_empreendimento,
    deletar_empreendimento,
    duplicar_empreendimento,
    custo_total,
)
from utils.formatters import brl
from utils.ui import load_css, render_sidebar_brand, render_header

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfólio de Ativos | ImobiInvest Pro",
    layout="wide",
)

load_css()

# ── Estado de sessão ──────────────────────────────────────────────────────────
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Gestão de Portfólio e Cadastro de Ativos",
    subtitle="Administração cadastral, estrutura de custos de aquisição (CAPEX) e governança documental do portfólio.",
    category="ASSET MANAGEMENT",
    code="MOD-02",
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Formulário de novo empreendimento
# ─────────────────────────────────────────────────────────────────────────────
TIPOS = ["Apartamento", "Casa", "Comercial", "Terreno", "Galpão", "Studio", "Outro"]

with st.sidebar:
    render_sidebar_brand("Asset Management")
    st.markdown('<div class="sidebar-section-label">Registro de Novo Ativo</div>', unsafe_allow_html=True)
    with st.form("form_novo_empreendimento", clear_on_submit=True):
        nome = st.text_input("Identificação do Ativo *", placeholder="Ex.: Edifício Corporate Faria Lima")
        tipo = st.selectbox("Tipologia", TIPOS)

        col_cid, col_area = st.columns(2)
        cidade = col_cid.text_input("Praça / Cidade", placeholder="São Paulo - SP")
        area_m2 = col_area.number_input("Área Privativa (m²)", min_value=0.0, step=0.5, format="%.2f")

        data_aquisicao = st.date_input("Data de Aquisição", value=date.today())

        st.markdown('<div class="sidebar-section-label">Estrutura de CAPEX (R$)</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        valor_aquisicao = col_a.number_input("Valor de Aquisição", min_value=0.0, step=1000.0, format="%.2f")
        valor_reforma = col_b.number_input("Reforma / Retrofit", min_value=0.0, step=500.0, format="%.2f")

        col_c, col_d = st.columns(2)
        valor_documentacao = col_c.number_input("Escritura / Registro", min_value=0.0, step=100.0, format="%.2f")
        valor_itbi = col_d.number_input("ITBI", min_value=0.0, step=100.0, format="%.2f")

        col_e, col_f = st.columns(2)
        valor_corretagem = col_e.number_input("Assessoria / Corretagem", min_value=0.0, step=100.0, format="%.2f")
        outros_custos = col_f.number_input("Custos Acessórios", min_value=0.0, step=100.0, format="%.2f")

        notas = st.text_area("Memorando / Observações Técnicas", placeholder="Tese de investimento, locatário, matrícula...")

        submitted = st.form_submit_button("Registrar Ativo", type="primary", use_container_width=True)

    if submitted:
        if not nome.strip():
            st.sidebar.error("O campo Identificação do Ativo é obrigatório.")
        else:
            dados = {
                "nome": nome.strip(),
                "tipo": tipo,
                "cidade": cidade.strip() or None,
                "area_m2": area_m2,
                "data_aquisicao": data_aquisicao.isoformat(),
                "valor_aquisicao": valor_aquisicao,
                "valor_reforma": valor_reforma,
                "valor_documentacao": valor_documentacao,
                "valor_itbi": valor_itbi,
                "valor_corretagem": valor_corretagem,
                "outros_custos": outros_custos,
                "notas": notas.strip() or None,
            }
            inserir_empreendimento(dados)
            st.sidebar.success(f"Ativo '{nome}' registrado com sucesso.")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MODO EDIÇÃO — Painel no topo da área principal
# ─────────────────────────────────────────────────────────────────────────────
def _form_edicao(eid: int):
    emp = buscar_empreendimento(eid)
    if not emp:
        st.error("Ativo não localizado na base de dados.")
        st.session_state.edit_id = None
        return

    st.subheader(f"Edição Cadastral: {emp['nome']}")

    with st.form("form_edicao"):
        col_n, col_t = st.columns([2, 1])
        nome_e = col_n.text_input("Identificação do Ativo *", value=emp["nome"])
        tipo_e = col_t.selectbox(
            "Tipologia", TIPOS,
            index=TIPOS.index(emp["tipo"]) if emp["tipo"] in TIPOS else 0,
        )

        col_cid_e, col_area_e, col_dt_e = st.columns(3)
        cidade_e = col_cid_e.text_input("Praça / Cidade", value=emp.get("cidade") or "")
        area_e = col_area_e.number_input(
            "Área Privativa (m²)", min_value=0.0, step=0.5, format="%.2f",
            value=float(emp.get("area_m2") or 0),
        )

        data_str = emp.get("data_aquisicao") or date.today().isoformat()
        try:
            data_val = date.fromisoformat(data_str[:10])
        except ValueError:
            data_val = date.today()
        data_e = col_dt_e.date_input("Data de Aquisição", value=data_val)

        st.markdown('<p class="section-title">Composição de Custos de Capital (CAPEX)</p>', unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        v_aquis = col_a.number_input(
            "Aquisição (R$)", min_value=0.0, step=1000.0, format="%.2f",
            value=float(emp.get("valor_aquisicao") or 0),
        )
        v_ref = col_b.number_input(
            "Reforma / Retrofit (R$)", min_value=0.0, step=500.0, format="%.2f",
            value=float(emp.get("valor_reforma") or 0),
        )
        v_doc = col_c.number_input(
            "Documentação (R$)", min_value=0.0, step=100.0, format="%.2f",
            value=float(emp.get("valor_documentacao") or 0),
        )

        col_d, col_e, col_f = st.columns(3)
        v_itbi = col_d.number_input(
            "ITBI (R$)", min_value=0.0, step=100.0, format="%.2f",
            value=float(emp.get("valor_itbi") or 0),
        )
        v_corr = col_e.number_input(
            "Corretagem (R$)", min_value=0.0, step=100.0, format="%.2f",
            value=float(emp.get("valor_corretagem") or 0),
        )
        v_out = col_f.number_input(
            "Custos Acessórios (R$)", min_value=0.0, step=100.0, format="%.2f",
            value=float(emp.get("outros_custos") or 0),
        )

        notas_e = st.text_area("Memorando / Observações Técnicas", value=emp.get("notas") or "")

        col_salvar, col_cancelar = st.columns([1, 1])
        salvar = col_salvar.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
        cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)

    if salvar:
        if not nome_e.strip():
            st.error("O campo Identificação do Ativo é obrigatório.")
        else:
            dados_atualizados = {
                "nome": nome_e.strip(),
                "tipo": tipo_e,
                "cidade": cidade_e.strip() or None,
                "area_m2": area_e,
                "data_aquisicao": data_e.isoformat(),
                "valor_aquisicao": v_aquis,
                "valor_reforma": v_ref,
                "valor_documentacao": v_doc,
                "valor_itbi": v_itbi,
                "valor_corretagem": v_corr,
                "outros_custos": v_out,
                "notas": notas_e.strip() or None,
            }
            atualizar_empreendimento(eid, dados_atualizados)
            st.success(f"Ativo '{nome_e}' atualizado com sucesso.")
            st.session_state.edit_id = None
            st.rerun()

    if cancelar:
        st.session_state.edit_id = None
        st.rerun()


if st.session_state.edit_id is not None:
    _form_edicao(st.session_state.edit_id)
    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# LISTAGEM DE EMPREENDIMENTOS
# ─────────────────────────────────────────────────────────────────────────────
empreendimentos = listar_empreendimentos()

if not empreendimentos:
    st.info("Nenhum ativo registrado na carteira. Utilize o painel lateral para cadastrar o primeiro imóvel.")
    st.stop()

st.markdown(
    f'<p class="section-title">Carteira Ativa — {len(empreendimentos)} Ativo(s) Sob Gestão</p>',
    unsafe_allow_html=True,
)

CAMPOS_CUSTO = {
    "Valor de Aquisição": "valor_aquisicao",
    "Reforma / Retrofit": "valor_reforma",
    "Documentação e Registro": "valor_documentacao",
    "ITBI": "valor_itbi",
    "Assessoria / Corretagem": "valor_corretagem",
    "Custos Acessórios": "outros_custos",
}

for emp in empreendimentos:
    ct = custo_total(emp)
    expander_label = f"ID #{emp['id']:02d}  |  {emp['nome']}  —  {emp['tipo'].upper()}  —  CAPEX: {brl(ct)}"

    with st.expander(expander_label, expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Localização / Praça", emp.get("cidade") or "—")
        m2.metric("Área Privativa", f"{emp.get('area_m2') or 0:.1f} m²")
        m3.metric(
            "Data de Aquisição",
            emp.get("data_aquisicao", "—")[:10] if emp.get("data_aquisicao") else "—",
        )
        m4.metric("Custo Total Alocado", brl(ct))

        st.markdown('<p class="section-title" style="margin-top: 1rem;">Demonstrativo de Composição de CAPEX</p>', unsafe_allow_html=True)
        breakdown = {
            "Rubrica de Custo": list(CAMPOS_CUSTO.keys()),
            "Montante (R$)": [brl(emp.get(v) or 0) for v in CAMPOS_CUSTO.values()],
            "Participação (%)": [
                f"{(emp.get(v) or 0) / ct * 100:.1f}%" if ct > 0 else "—"
                for v in CAMPOS_CUSTO.values()
            ],
        }
        df_breakdown = pd.DataFrame(breakdown)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

        if emp.get("notas"):
            st.markdown(
                f'<div class="alert-box alert-warning"><strong>Memorando Técnico:</strong> {emp["notas"]}</div>',
                unsafe_allow_html=True,
            )

        btn1, btn2, btn3 = st.columns([1, 1, 1])

        if btn1.button("Editar Registro", key=f"editar_{emp['id']}", use_container_width=True):
            st.session_state.edit_id = emp["id"]
            st.rerun()

        if btn2.button("Duplicar Ativo", key=f"duplicar_{emp['id']}", use_container_width=True):
            novo_id = duplicar_empreendimento(emp["id"])
            if novo_id > 0:
                st.success("Ativo duplicado com sucesso.")
            else:
                st.error("Erro ao duplicar o registro.")
            st.rerun()

        with btn3.popover("Excluir Ativo", use_container_width=True):
            st.warning(f"Confirma a exclusão permanente do ativo **{emp['nome']}**?")
            if st.button(
                "Confirmar Exclusão Permanente",
                key=f"confirmar_excluir_{emp['id']}",
                type="primary",
            ):
                deletar_empreendimento(emp["id"])
                st.rerun()
