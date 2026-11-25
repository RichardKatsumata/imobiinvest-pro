"""
Relatórios Executivos e Dossiê de Investimento — ImobiInvest Pro
Geração e exportação de memorandos institucionais em HTML para ativos do portfólio.
"""
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

from database import listar_empreendimentos, buscar_empreendimento, custo_total
from utils.ui import load_css, render_sidebar_brand, render_header

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Relatórios Executivos | ImobiInvest Pro",
    layout="wide",
)

load_css()

with st.sidebar:
    render_sidebar_brand("Institutional Reporting")
    st.caption("Emissão de memorandos executivos e dossiês de auditoria financeira em formato HTML.")

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Emissão de Dossiê e Relatório Executivo (Investment Memorandum)",
    subtitle="Consolidação cadastral, estrutura de CAPEX e histórico de modelagens financeiras para comitê de investimentos.",
    category="INSTITUTIONAL REPORTING",
    code="MOD-10",
)


# ── Helpers de formatação ─────────────────────────────────────────────────────
def _brl(v) -> str:
    try:
        v = float(v or 0)
        neg = v < 0
        s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"-R$ {s}" if neg else f"R$ {s}"
    except Exception:
        return "R$ 0,00"


def _fmt_date(d: str) -> str:
    if not d:
        return "—"
    try:
        return datetime.fromisoformat(d).strftime("%d/%m/%Y")
    except Exception:
        return d


def _safe_json(text) -> list:
    try:
        data = json.loads(text or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


# ── Carrega lista de empreendimentos ──────────────────────────────────────────
try:
    lista = listar_empreendimentos()
except Exception as exc:
    st.error(f"Erro ao acessar o banco de dados: {exc}")
    st.stop()

if not lista:
    st.info("Nenhum ativo registrado na base de dados. Cadastre um empreendimento antes de emitir relatórios.")
    st.stop()

opcoes = {f"ID #{e['id']:02d} — {e['nome']} ({e['cidade'] or 'Praça não informada'})": e["id"] for e in lista}

escolha = st.selectbox(
    "Selecione o ativo imobiliário para emissão do dossiê:",
    options=[""] + list(opcoes.keys()),
    index=0,
    key="sel_emp_relatorio",
)

if not escolha:
    st.info("Selecione um ativo no seletor acima para inspecionar o dossiê pré-emissão.")
    st.stop()

eid = opcoes[escolha]

try:
    emp = buscar_empreendimento(eid)
except Exception as exc:
    st.error(f"Erro ao carregar ativo: {exc}")
    st.stop()

if not emp:
    st.error("Ativo não localizado.")
    st.stop()

total = custo_total(emp)
simulacoes = _safe_json(emp.get("simulacoes"))

# ═══════════════════════════════════════════════════════════════════════════════
#  PRÉ-VISUALIZAÇÃO DO RELATÓRIO
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader(f"Dossiê Executivo: {emp['nome']}")

col_info, col_custos = st.columns(2)

with col_info:
    st.markdown('<p class="section-title">01. Ficha Cadastral do Ativo</p>', unsafe_allow_html=True)
    info_data = {
        "Atributo": ["Identificação", "Tipologia", "Praça / Localização", "Área Privativa (m²)", "Data de Aquisição", "Memorando Técnico"],
        "Especificação": [
            emp.get("nome", "—"),
            emp.get("tipo", "—"),
            emp.get("cidade") or "—",
            f"{emp.get('area_m2') or 0:.2f} m²",
            _fmt_date(emp.get("data_aquisicao")),
            emp.get("notas") or "—",
        ],
    }
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)

with col_custos:
    st.markdown('<p class="section-title">02. Estrutura de Capital Alocado (CAPEX)</p>', unsafe_allow_html=True)
    custos_data = {
        "Rubrica": [
            "Valor de Aquisição",
            "Reforma / Retrofit",
            "Documentação e Registro",
            "ITBI",
            "Assessoria / Corretagem",
            "Custos Acessórios",
            "CAPEX TOTAL ALOCADO",
        ],
        "Montante (R$)": [
            _brl(emp.get("valor_aquisicao")),
            _brl(emp.get("valor_reforma")),
            _brl(emp.get("valor_documentacao")),
            _brl(emp.get("valor_itbi")),
            _brl(emp.get("valor_corretagem")),
            _brl(emp.get("outros_custos")),
            _brl(total),
        ],
    }
    st.dataframe(pd.DataFrame(custos_data), use_container_width=True, hide_index=True)

if simulacoes:
    st.markdown(f'<p class="section-title" style="margin-top: 1rem;">03. Modelagens Financeiras Arquivadas ({len(simulacoes)})</p>', unsafe_allow_html=True)
    for i, sim in enumerate(simulacoes, 1):
        with st.expander(f"Simulação #{i:02d} — {sim.get('tipo', 'Modelagem Financeira')} ({_fmt_date(sim.get('salvo_em', ''))})"):
            sim_disp = {k: v for k, v in sim.items() if k != "fluxos"}
            st.json(sim_disp)
else:
    st.info("Nenhuma modelagem financeira arquivada para este ativo até o momento.")

st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
#  GERAÇÃO DO HTML INSTITUCIONAL
# ═══════════════════════════════════════════════════════════════════════════════

def _sim_card_html(sim: dict, idx: int) -> str:
    tipo  = sim.get("tipo", f"Modelagem #{idx:02d}")
    salvo = _fmt_date(sim.get("salvo_em", ""))
    linhas = ""
    skip = {"salvo_em", "fluxos", "tipo"}
    labels = {
        "investimento":        "Investimento Inicial (CAPEX)",
        "aluguel_mensal":      "Receita Locatícia Mensal",
        "taxa_vacancia":       "Taxa de Vacância Projetada",
        "despesas_mensais":    "Despesas Operacionais (OPEX)",
        "reajuste_anual":      "Indexador de Reajuste Anual",
        "periodos":            "Horizonte de Projeção",
        "tma_mensal":          "Custo de Capital (TMA Mensal)",
        "valor_residual":      "Valor Residual de Saída",
        "vpl":                 "Valor Presente Líquido (VPL Discreto)",
        "vpl_continuo":        "VPL Contínuo (Regra dos Trapézios)",
        "tir_mensal":          "TIR Mensal (Newton-Raphson)",
        "tir_anual":           "TIR Anual Efetiva (Newton-Raphson)",
        "payback_simples":     "Payback Nominal",
        "payback_descontado":  "Payback Descontado",
        "roi":                 "Retorno Sobre Capital (ROI)",
        "rentabilidade_anual": "Rentabilidade Anualizada",
        "valor_compra":        "Valor de Aquisição",
        "valor_reforma":       "Orçamento de Retrofit",
        "outros_custos":       "Custos Transacionais",
        "valor_venda":         "Valor Alvo de Venda",
        "corretagem_pct":      "Comissão de Corretagem",
        "imposto_pct":         "Alíquota sobre Ganho de Capital",
        "lucro_liquido":       "Resultado Líquido (Pós-IR)",
        "lucro_bruto":         "Resultado Bruto",
        "custo_total":         "Custo Total Alocado",
        "corretagem":          "Corretagem (R$)",
        "imposto":             "Imposto Apurado (R$)",
        "break_even_venda":    "Preço Mínimo de Saída (Bisseção)",
    }
    monetarios = {
        "investimento", "aluguel_mensal", "despesas_mensais", "valor_residual",
        "vpl", "vpl_continuo", "lucro_liquido", "lucro_bruto", "custo_total",
        "corretagem", "imposto", "valor_compra", "valor_reforma", "outros_custos",
        "valor_venda", "break_even_venda",
    }
    percentuais = {"tir_mensal", "tir_anual", "roi", "rentabilidade_anual"}
    decimais_pct = {"taxa_vacancia", "reajuste_anual", "tma_mensal", "corretagem_pct", "imposto_pct"}

    for k, v in sim.items():
        if k in skip:
            continue
        label = labels.get(k, k.replace("_", " ").title())
        try:
            if v is None:
                display = "Não atingido / —"
            else:
                vf = float(v)
                if k in monetarios:
                    display = _brl(vf)
                elif k in percentuais:
                    display = f"{vf:.2f}%"
                elif k in decimais_pct:
                    display = f"{vf * 100:.2f}%"
                elif k in {"periodos", "payback_simples", "payback_descontado"}:
                    display = f"{int(vf)} meses"
                elif isinstance(v, float):
                    display = f"{vf:.4f}"
                else:
                    display = str(v)
        except (TypeError, ValueError):
            display = str(v) if v is not None else "—"

        linhas += f"""
            <tr>
                <td style="padding:8px 16px;color:#94A3B8;border-bottom:1px solid #1E293B;font-size:13px;">{label}</td>
                <td style="padding:8px 16px;text-align:right;font-weight:600;font-family:'JetBrains Mono',monospace;
                           color:#F8FAFC;border-bottom:1px solid #1E293B;font-size:13px;">{display}</td>
            </tr>"""

    return f"""
    <div style="background:#0F1623;border:1px solid #1E293B;border-radius:4px;
                margin-bottom:20px;overflow:hidden;">
        <div style="background:#131C2E;padding:12px 16px;display:flex;
                    justify-content:space-between;align-items:center;border-bottom:1px solid #1E293B;">
            <span style="color:#C5A059;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;">
                {idx:02d} &nbsp;·&nbsp; {tipo}
            </span>
            <span style="color:#64748B;font-size:11px;font-family:'JetBrains Mono',monospace;">DATA DE ARQUIVAMENTO: {salvo}</span>
        </div>
        <table style="width:100%;border-collapse:collapse;">
            {linhas}
        </table>
    </div>"""


def gerar_html_relatorio(emp: dict, simulacoes: list) -> str:
    total_val = custo_total(emp)
    data_geracao = datetime.now().strftime("%d/%m/%Y · %H:%M")

    sims_html = ""
    if simulacoes:
        for i, sim in enumerate(simulacoes, 1):
            sims_html += _sim_card_html(sim, i)
    else:
        sims_html = """
        <p style="color:#64748B;font-size:13px;text-align:center;padding:24px;border:1px solid #1E293B;background:#0F1623;">
            Nenhuma simulação financeira arquivada para este ativo até a presente data.
        </p>"""

    custos_itens = [
        ("Valor de Aquisição",      emp.get("valor_aquisicao")),
        ("Reforma / Retrofit",      emp.get("valor_reforma")),
        ("Documentação e Registro", emp.get("valor_documentacao")),
        ("ITBI",                    emp.get("valor_itbi")),
        ("Assessoria / Corretagem", emp.get("valor_corretagem")),
        ("Custos Acessórios",       emp.get("outros_custos")),
    ]
    custos_rows = ""
    for label, val in custos_itens:
        v = float(val or 0)
        pct_val = (v / total_val * 100) if total_val else 0
        custos_rows += f"""
        <tr>
            <td style="padding:10px 16px;border-bottom:1px solid #1E293B;color:#F8FAFC;font-size:13px;">
                {label}
            </td>
            <td style="padding:10px 16px;text-align:right;border-bottom:1px solid #1E293B;
                       color:#F8FAFC;font-weight:500;font-family:'JetBrains Mono',monospace;font-size:13px;">
                {_brl(v)}
            </td>
            <td style="padding:10px 16px;text-align:right;border-bottom:1px solid #1E293B;
                       color:#94A3B8;font-family:'JetBrains Mono',monospace;font-size:12px;">
                {pct_val:.1f}%
            </td>
        </tr>"""

    info_rows = ""
    info_itens = [
        ("Identificação do Ativo", emp.get("nome", "—")),
        ("Tipologia",              emp.get("tipo", "—")),
        ("Praça / Localização",    emp.get("cidade") or "—"),
        ("Área Privativa",         f"{emp.get('area_m2') or 0:.2f} m²"),
        ("Data de Aquisição",      _fmt_date(emp.get("data_aquisicao"))),
        ("Registro Cadastral",     _fmt_date(emp.get("criado_em"))),
        ("Última Atualização",     _fmt_date(emp.get("atualizado_em"))),
    ]
    for label, valor in info_itens:
        info_rows += f"""
        <tr>
            <td style="padding:10px 16px;border-bottom:1px solid #1E293B;
                       color:#94A3B8;width:240px;font-weight:500;font-size:13px;">
                {label}
            </td>
            <td style="padding:10px 16px;border-bottom:1px solid #1E293B;color:#F8FAFC;font-size:13px;">
                {valor}
            </td>
        </tr>"""

    notas = emp.get("notas") or "Nenhuma observação técnica registrada."

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Memorandum — {emp['nome']} | ImobiInvest Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0A0E17;
            color: #F8FAFC;
            line-height: 1.6;
        }}
        .header {{
            background: #0F1623;
            border-bottom: 2px solid #C5A059;
            padding: 32px 48px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .logo {{
            font-size: 20px;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}
        .logo span {{ color: #C5A059; }}
        .header-meta {{
            text-align: right;
            color: #94A3B8;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .header-meta strong {{
            color: #C5A059;
            display: block;
            font-size: 13px;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 48px; }}
        .section-header {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: #C5A059;
            margin: 34px 0 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #1E293B;
        }}
        .card {{
            background: #0F1623;
            border: 1px solid #1E293B;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .total-row td {{
            background: #131C2E;
            padding: 14px 16px;
            font-size: 14px;
            font-weight: 600;
            color: #C5A059;
            font-family: 'JetBrains Mono', monospace;
        }}
        .total-row td:last-child {{ text-align: right; }}
        .notas-box {{
            background: #0F1623;
            border: 1px solid #1E293B;
            border-left: 3px solid #C5A059;
            border-radius: 3px;
            padding: 16px 20px;
            color: #CBD5E1;
            font-size: 13px;
        }}
        .footer {{
            margin-top: 60px;
            padding: 24px 48px;
            background: #080B12;
            border-top: 1px solid #1E293B;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #64748B;
            font-family: 'JetBrains Mono', monospace;
        }}
        .footer strong {{ color: #C5A059; }}
        .badge {{
            display: inline-block;
            background: #131C2E;
            border: 1px solid #C5A059;
            color: #C5A059;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 2px;
            letter-spacing: 0.08em;
            margin-top: 6px;
        }}
    </style>
</head>
<body>

<div class="header">
    <div>
        <div class="logo">IMOBIINVEST <span>PRO</span></div>
        <div style="color:#94A3B8;font-size:12px;margin-top:6px;letter-spacing:0.06em;text-transform:uppercase;">
            Institutional Real Estate Analytics &amp; Quantitative Modelling
        </div>
    </div>
    <div class="header-meta">
        <strong>Investment Memorandum</strong>
        EMISSÃO: {data_geracao}<br>
        <span class="badge">ASSET ID #{emp['id']:02d}</span>
    </div>
</div>

<div class="container">

    <div class="section-header">01 &nbsp;·&nbsp; Especificação Cadastral do Ativo</div>
    <div class="card">
        <table>{info_rows}</table>
    </div>

    <div class="section-header">02 &nbsp;·&nbsp; Memorando Técnico</div>
    <div class="notas-box">{notas}</div>

    <div class="section-header">03 &nbsp;·&nbsp; Estrutura de Capital Alocado (CAPEX)</div>
    <div class="card">
        <table>
            <thead>
                <tr style="background:#131C2E;">
                    <th style="padding:10px 16px;text-align:left;color:#94A3B8;
                               font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">
                        Rubrica de Custo
                    </th>
                    <th style="padding:10px 16px;text-align:right;color:#94A3B8;
                               font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">
                        Montante (R$)
                    </th>
                    <th style="padding:10px 16px;text-align:right;color:#94A3B8;
                               font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">
                        Participação
                    </th>
                </tr>
            </thead>
            <tbody>
                {custos_rows}
                <tr class="total-row">
                    <td colspan="2">CAPEX TOTAL ALOCADO</td>
                    <td style="text-align:right;">{_brl(total_val)}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section-header">04 &nbsp;·&nbsp; Dossiê de Simulações Financeiras ({len(simulacoes)})</div>
    {sims_html}

</div>

<div class="footer">
    <div>
        <strong>IMOBIINVEST PRO</strong> — QUANTITATIVE REAL ESTATE ANALYTICS
    </div>
    <div>
        GERADO EM {data_geracao} &nbsp;·&nbsp; USO ESTRITAMENTE INSTITUCIONAL
    </div>
</div>

</body>
</html>"""


# ── Botão de geração ──────────────────────────────────────────────────────────
col_btn, col_info2 = st.columns([1, 2])

with col_btn:
    gerar = st.button("Compilar Dossiê Executivo (HTML)", type="primary", key="btn_gerar_relatorio", use_container_width=True)

with col_info2:
    st.caption(
        f"O documento consolidará **{len(simulacoes)} simulação(ões)** arquivada(s) "
        f"e o quadro completo de CAPEX do ativo **{emp['nome']}**."
    )

if gerar:
    try:
        html_content = gerar_html_relatorio(emp, simulacoes)
        nome_arquivo = (
            f"dossie_executivo_{emp['nome'].lower().replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M}.html"
        )

        st.success("Dossiê executivo compilado com sucesso.")

        st.download_button(
            label="Exportar Documento HTML",
            data=html_content.encode("utf-8"),
            file_name=nome_arquivo,
            mime="text/html",
            key="download_relatorio",
        )

        st.subheader("Inspeção do Documento Compilado")
        components.html(html_content, height=620, scrolling=True)

    except Exception as exc:
        st.error(f"Erro ao compilar relatório: {exc}")
