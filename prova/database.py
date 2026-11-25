import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "imobiinvest.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db_novo = not DB_PATH.exists()
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS empreendimentos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nome            TEXT    NOT NULL,
            tipo            TEXT    NOT NULL,
            cidade          TEXT,
            area_m2         REAL,
            data_aquisicao  TEXT,
            valor_aquisicao REAL    DEFAULT 0,
            valor_reforma   REAL    DEFAULT 0,
            valor_documentacao REAL DEFAULT 0,
            valor_itbi      REAL    DEFAULT 0,
            valor_corretagem REAL   DEFAULT 0,
            outros_custos   REAL    DEFAULT 0,
            notas           TEXT,
            simulacoes      TEXT    DEFAULT '[]',
            criado_em       TEXT    DEFAULT (datetime('now')),
            atualizado_em   TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM empreendimentos").fetchone()[0]
    conn.close()
    if db_novo and count == 0:
        popular_dados_exemplo()


# ── CRUD ──────────────────────────────────────────────────────────────────────

def listar_empreendimentos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM empreendimentos ORDER BY criado_em DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_empreendimento(eid: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM empreendimentos WHERE id = ?", (eid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def inserir_empreendimento(dados: dict) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO empreendimentos
            (nome, tipo, cidade, area_m2, data_aquisicao,
             valor_aquisicao, valor_reforma, valor_documentacao,
             valor_itbi, valor_corretagem, outros_custos, notas)
        VALUES (:nome, :tipo, :cidade, :area_m2, :data_aquisicao,
                :valor_aquisicao, :valor_reforma, :valor_documentacao,
                :valor_itbi, :valor_corretagem, :outros_custos, :notas)
    """, dados)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def atualizar_empreendimento(eid: int, dados: dict):
    dados["id"] = eid
    dados["atualizado_em"] = datetime.now().isoformat()
    conn = get_conn()
    conn.execute("""
        UPDATE empreendimentos SET
            nome=:nome, tipo=:tipo, cidade=:cidade, area_m2=:area_m2,
            data_aquisicao=:data_aquisicao, valor_aquisicao=:valor_aquisicao,
            valor_reforma=:valor_reforma, valor_documentacao=:valor_documentacao,
            valor_itbi=:valor_itbi, valor_corretagem=:valor_corretagem,
            outros_custos=:outros_custos, notas=:notas,
            atualizado_em=:atualizado_em
        WHERE id=:id
    """, dados)
    conn.commit()
    conn.close()


def deletar_empreendimento(eid: int):
    conn = get_conn()
    conn.execute("DELETE FROM empreendimentos WHERE id = ?", (eid,))
    conn.commit()
    conn.close()


def duplicar_empreendimento(eid: int) -> int:
    orig = buscar_empreendimento(eid)
    if not orig:
        return -1
    orig.pop("id")
    orig.pop("criado_em")
    orig.pop("atualizado_em")
    orig.pop("simulacoes")
    orig["nome"] = orig["nome"] + " (cópia)"
    return inserir_empreendimento(orig)


def salvar_simulacao(eid: int, simulacao: dict):
    emp = buscar_empreendimento(eid)
    if not emp:
        return
    sims = json.loads(emp.get("simulacoes") or "[]")
    simulacao["salvo_em"] = datetime.now().isoformat()
    sims.append(simulacao)
    conn = get_conn()
    conn.execute(
        "UPDATE empreendimentos SET simulacoes=? WHERE id=?",
        (json.dumps(sims, ensure_ascii=False), eid)
    )
    conn.commit()
    conn.close()


def custo_total(emp: dict) -> float:
    campos = [
        "valor_aquisicao", "valor_reforma", "valor_documentacao",
        "valor_itbi", "valor_corretagem", "outros_custos"
    ]
    return sum(emp.get(c) or 0 for c in campos)


def popular_dados_exemplo():
    """Insere empreendimentos de demonstração no portfólio caso desejado."""
    exemplos = [
        {
            "nome": "Studio Vila Mariana",
            "tipo": "Studio",
            "cidade": "São Paulo - SP",
            "area_m2": 32.0,
            "data_aquisicao": "2025-03-15",
            "valor_aquisicao": 290000.0,
            "valor_reforma": 25000.0,
            "valor_documentacao": 4500.0,
            "valor_itbi": 8700.0,
            "valor_corretagem": 0.0,
            "outros_custos": 1800.0,
            "notas": "Próximo ao metrô Ana Rosa. Alta demanda de locação estudantil e executiva.",
        },
        {
            "nome": "Apto 2 Dorms Batel",
            "tipo": "Apartamento",
            "cidade": "Curitiba - PR",
            "area_m2": 68.0,
            "data_aquisicao": "2025-07-10",
            "valor_aquisicao": 480000.0,
            "valor_reforma": 42000.0,
            "valor_documentacao": 6200.0,
            "valor_itbi": 13920.0,
            "valor_corretagem": 0.0,
            "outros_custos": 2880.0,
            "notas": "Imóvel reformado para locação de longo prazo ou revenda (flip).",
        },
        {
            "nome": "Sala Comercial Savassi",
            "tipo": "Comercial",
            "cidade": "Belo Horizonte - MG",
            "area_m2": 45.0,
            "data_aquisicao": "2025-11-20",
            "valor_aquisicao": 340000.0,
            "valor_reforma": 18000.0,
            "valor_documentacao": 5000.0,
            "valor_itbi": 10200.0,
            "valor_corretagem": 0.0,
            "outros_custos": 1800.0,
            "notas": "Contrato corporativo em edifício com portaria 24h.",
        },
        {
            "nome": "Casa Condomínio Alphaville",
            "tipo": "Casa",
            "cidade": "Barueri - SP",
            "area_m2": 210.0,
            "data_aquisicao": "2026-02-05",
            "valor_aquisicao": 920000.0,
            "valor_reforma": 110000.0,
            "valor_documentacao": 12000.0,
            "valor_itbi": 27600.0,
            "valor_corretagem": 0.0,
            "outros_custos": 5400.0,
            "notas": "Operação de Compra, Reforma e Revenda (House Flipping).",
        },
    ]
    for item in exemplos:
        eid = inserir_empreendimento(item)
        if item["nome"] == "Studio Vila Mariana":
            salvar_simulacao(eid, {
                "tipo": "Simulação de Locação",
                "investimento": 330000.0,
                "aluguel_mensal": 2800.0,
                "taxa_vacancia": 0.05,
                "despesas_mensais": 250.0,
                "reajuste_anual": 0.06,
                "periodos": 120,
                "tma_mensal": 0.008,
                "valor_residual": 420000.0,
                "vpl": 134512.48,
                "tir_mensal": 1.18,
                "tir_anual": 15.12,
                "payback_simples": 98,
                "payback_descontado": 120,
                "roi": 162.45,
            })


init_db()
