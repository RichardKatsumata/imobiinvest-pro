"""
Cálculos financeiros e imobiliários de alto nível usados pelas páginas,
alimentados pelos métodos numéricos programados do zero em utils.numericos.
"""
from typing import List, Tuple
import math
from utils.numericos import (
    calcular_vpl,
    calcular_tir,
    calcular_tir_detalhado,
    calcular_vpl_continuo,
    calcular_payback,
    calcular_payback_descontado,
    bissecao,
    newton_raphson,
    trapezios,
)


# ── Locação ───────────────────────────────────────────────────────────────────

def fluxo_locacao(
    investimento: float,
    aluguel_mensal: float,
    taxa_vacancia: float,       # 0–1
    despesas_mensais: float,
    reajuste_anual: float,      # 0–1
    periodos: int,              # meses
    valor_residual: float = 0,
) -> List[float]:
    fluxos = [-investimento]
    for t in range(1, periodos + 1):
        anos = (t - 1) // 12
        aluguel_adj = aluguel_mensal * (1 + reajuste_anual) ** anos
        receita = aluguel_adj * (1 - taxa_vacancia)
        fc = receita - despesas_mensais
        if t == periodos:
            fc += valor_residual
        fluxos.append(fc)
    return fluxos


def indicadores_locacao(
    fluxos: List[float],
    tma_mensal: float,
) -> dict:
    investimento = -fluxos[0]
    vpl = calcular_vpl(fluxos, tma_mensal)
    tir, hist_tir, metodo_tir = calcular_tir_detalhado(fluxos)
    payback = calcular_payback(fluxos)
    payback_desc = calcular_payback_descontado(fluxos, tma_mensal)
    receita_liquida_total = sum(fluxos[1:])
    roi = (receita_liquida_total - investimento) / investimento * 100 if investimento else 0
    rent_anual = ((1 + tir) ** 12 - 1) * 100 if not math.isnan(tir) else float("nan")
    return {
        "vpl": vpl,
        "tir_mensal": tir * 100 if not math.isnan(tir) else float("nan"),
        "tir_anual": rent_anual,
        "payback_simples": payback,
        "payback_descontado": payback_desc,
        "roi": roi,
        "rentabilidade_anual": rent_anual,
        "historico_tir": hist_tir,
        "metodo_tir": metodo_tir,
    }


def vpl_continuo_locacao(
    investimento: float,
    aluguel_mensal: float,
    taxa_vacancia: float,
    despesas_mensais: float,
    reajuste_anual: float,
    periodos: int,
    tma_mensal: float,
    valor_residual: float = 0.0,
    n_trapezios: int = 240,
) -> Tuple[float, List[dict]]:
    """
    Calcula o VPL Contínuo da locação usando a Regra dos Trapézios Composta.
    Modela o fluxo operacional mensal com crescimento contínuo equivalente ao reajuste anual.
    """
    taxa_cresc_mensal = (1.0 + max(reajuste_anual, 0.0)) ** (1.0 / 12.0) - 1.0

    def fc_continuo(t: float) -> float:
        aluguel_t = aluguel_mensal * ((1.0 + taxa_cresc_mensal) ** t)
        receita_t = aluguel_t * (1.0 - taxa_vacancia)
        return receita_t - despesas_mensais

    return calcular_vpl_continuo(
        investimento=investimento,
        fluxo_continuo_fn=fc_continuo,
        taxa_mensal=tma_mensal,
        periodos=periodos,
        valor_residual=valor_residual,
        n_trapezios=n_trapezios,
    )


# ── Flip (Compra, Reforma e Revenda) ─────────────────────────────────────────

def resultado_flip(
    valor_compra: float,
    valor_reforma: float,
    outros_custos: float,
    valor_venda: float,
    corretagem_pct: float,      # 0–1
    imposto_pct: float,         # 0–1
) -> dict:
    custo_total = valor_compra + valor_reforma + outros_custos
    corretagem = valor_venda * corretagem_pct
    lucro_bruto = valor_venda - custo_total - corretagem
    imposto = max(lucro_bruto, 0) * imposto_pct
    lucro_liquido = lucro_bruto - imposto
    roi = lucro_liquido / custo_total * 100 if custo_total else 0
    return {
        "custo_total": custo_total,
        "corretagem": corretagem,
        "lucro_bruto": lucro_bruto,
        "imposto": imposto,
        "lucro_liquido": lucro_liquido,
        "roi": roi,
    }


def break_even_venda_detalhado(
    custo_total: float,
    corretagem_pct: float,
    imposto_pct: float,
) -> Tuple[float, List[dict]]:
    """
    Encontra o preço mínimo de venda para lucro líquido zero usando o
    Método da Bisseção programado do zero.
    """
    if custo_total <= 0:
        return 0.0, []
    if corretagem_pct >= 1.0 or imposto_pct >= 1.0:
        return float("inf"), []

    def lucro_liq_dado_venda(preco_venda: float) -> float:
        corretagem = preco_venda * corretagem_pct
        lucro_bruto = preco_venda - custo_total - corretagem
        imposto = max(lucro_bruto, 0.0) * imposto_pct
        return lucro_bruto - imposto

    a = 0.0
    b = max(custo_total * 3.0, 1000.0)
    while lucro_liq_dado_venda(b) < 0 and b < custo_total * 100:
        b *= 2.0

    try:
        raiz, hist = bissecao(lucro_liq_dado_venda, a, b, tol=1e-4, max_iter=200)
        return raiz, hist
    except Exception:
        return float("inf"), []


def break_even_venda(
    custo_total: float,
    corretagem_pct: float,
    imposto_pct: float,
) -> float:
    """Preço mínimo de venda para lucro zero via Método da Bisseção."""
    raiz, _ = break_even_venda_detalhado(custo_total, corretagem_pct, imposto_pct)
    return raiz


# ── Break-Even Locação ────────────────────────────────────────────────────────

def break_even_locacao(
    investimento: float,
    despesas_mensais: float,
    taxa_vacancia: float,
    reajuste_anual: float,
    periodos: int,
    tma_mensal: float,
    valor_residual: float = 0,
) -> dict:
    """
    Calcula os quatro pontos de equilíbrio usando o Método da Bisseção programado do zero.
    Retorna também os históricos de iteração para visualização.
    """
    # 1) Aluguel mínimo operacional (receita líquida inicial = 0 via bisseção)
    def saldo_operacional(aluguel: float) -> float:
        return aluguel * (1.0 - taxa_vacancia) - despesas_mensais

    if (1.0 - taxa_vacancia) > 0:
        b_op = max(despesas_mensais * 5.0, 1000.0)
        while saldo_operacional(b_op) < 0:
            b_op *= 2.0
        try:
            aluguel_operacional, hist_op = bissecao(saldo_operacional, 0.0, b_op, tol=1e-4, max_iter=200)
        except Exception:
            aluguel_operacional, hist_op = despesas_mensais / (1.0 - taxa_vacancia), []
    else:
        aluguel_operacional, hist_op = 0.0, []

    # 2) Aluguel mínimo financeiro (soma dos fluxos não-descontados no horizonte == 0,
    #    ou seja, Payback Simples ocorre exatamente no último mês do horizonte)
    def saldo_acumulado_horizonte(aluguel: float) -> float:
        fl = fluxo_locacao(investimento, aluguel, taxa_vacancia,
                           despesas_mensais, reajuste_anual, periodos, valor_residual)
        return sum(fl)

    b_fin = max(investimento, despesas_mensais * 5.0, 1000.0)
    while saldo_acumulado_horizonte(b_fin) < 0 and b_fin < investimento * 100:
        b_fin *= 2.0
    try:
        if saldo_acumulado_horizonte(0.0) >= 0:
            be_financeiro, hist_fin = 0.0, []
        else:
            be_financeiro, hist_fin = bissecao(
                saldo_acumulado_horizonte, 0.0, b_fin, tol=1e-3, max_iter=200
            )
    except Exception:
        be_financeiro, hist_fin = float("nan"), []

    # 3) Aluguel mínimo econômico (VPL = 0 na TMA informada via bisseção)
    def vpl_dado_aluguel(aluguel: float) -> float:
        fl = fluxo_locacao(investimento, aluguel, taxa_vacancia,
                           despesas_mensais, reajuste_anual, periodos, valor_residual)
        return calcular_vpl(fl, tma_mensal)

    b_eco = max(investimento, despesas_mensais * 5.0, 1000.0)
    while vpl_dado_aluguel(b_eco) < 0 and b_eco < investimento * 100:
        b_eco *= 2.0
    try:
        if vpl_dado_aluguel(0.0) >= 0:
            be_economico, hist_eco = 0.0, []
        else:
            be_economico, hist_eco = bissecao(
                vpl_dado_aluguel, 0.0, b_eco, tol=1e-3, max_iter=200
            )
    except Exception:
        be_economico, hist_eco = float("nan"), []

    # 4) Taxa mínima de ocupação para VPL >= 0 dado um aluguel de referência viável
    base_ref = be_economico if not math.isnan(be_economico) and be_economico > 0 else aluguel_operacional * 2
    aluguel_ref = max(base_ref * 1.25, aluguel_operacional * 2, despesas_mensais * 3, 1000.0)

    def vpl_dado_ocupacao(ocu: float) -> float:
        fl = fluxo_locacao(investimento, aluguel_ref, 1.0 - ocu,
                           despesas_mensais, reajuste_anual, periodos, valor_residual)
        return calcular_vpl(fl, tma_mensal)

    try:
        be_ocupacao, hist_ocu = bissecao(vpl_dado_ocupacao, 0.0001, 0.9999, tol=1e-5, max_iter=200)
    except Exception:
        be_ocupacao, hist_ocu = float("nan"), []

    return {
        "aluguel_operacional": aluguel_operacional,
        "aluguel_financeiro": be_financeiro,
        "aluguel_economico": be_economico,
        "taxa_ocupacao_minima": be_ocupacao,
        "aluguel_referencia_ocupacao": aluguel_ref,
        "historicos": {
            "Operacional": hist_op,
            "Financeiro": hist_fin,
            "Econômico": hist_eco,
            "Ocupação Mínima": hist_ocu,
        },
    }


# ── Financiamento ─────────────────────────────────────────────────────────────

def tabela_sac(
    principal: float,
    taxa_mensal: float,
    n_parcelas: int,
) -> List[dict]:
    amort = principal / n_parcelas if n_parcelas > 0 else 0.0
    saldo = principal
    tabela = []
    for t in range(1, n_parcelas + 1):
        juros = saldo * taxa_mensal
        parcela = amort + juros
        saldo -= amort
        tabela.append({
            "mes": t,
            "parcela": parcela,
            "amortizacao": amort,
            "juros": juros,
            "saldo_devedor": max(saldo, 0.0),
        })
    return tabela


def tabela_price(
    principal: float,
    taxa_mensal: float,
    n_parcelas: int,
) -> List[dict]:
    if n_parcelas <= 0:
        return []
    if taxa_mensal == 0:
        parcela = principal / n_parcelas
    else:
        parcela = principal * taxa_mensal / (1.0 - (1.0 + taxa_mensal) ** -n_parcelas)
    saldo = principal
    tabela = []
    for t in range(1, n_parcelas + 1):
        juros = saldo * taxa_mensal
        amort = parcela - juros
        saldo -= amort
        tabela.append({
            "mes": t,
            "parcela": parcela,
            "amortizacao": amort,
            "juros": juros,
            "saldo_devedor": max(saldo, 0.0),
        })
    return tabela


def calcular_cet_financiamento(
    valor_financiado: float,
    tabela: List[dict],
    custos_iniciais: float = 0.0,
    encargos_mensais: float = 0.0,
) -> Tuple[float, float, List[dict]]:
    """
    Calcula o Custo Efetivo Total (CET mensal e anual) de um financiamento
    usando o Método de Newton-Raphson sobre os fluxos de desembolso.
    Retorna (cet_mensal_pct, cet_anual_pct, historico_nr).
    """
    liquido_recebido = valor_financiado - custos_iniciais
    if liquido_recebido <= 0 or not tabela:
        return float("nan"), float("nan"), []
    fluxos = [liquido_recebido] + [-(row["parcela"] + encargos_mensais) for row in tabela]
    cet_m, hist, _ = calcular_tir_detalhado(fluxos)
    if math.isnan(cet_m):
        return float("nan"), float("nan"), []
    cet_a = ((1.0 + cet_m) ** 12 - 1.0) * 100.0
    return cet_m * 100.0, cet_a, hist


# ── Cenários ──────────────────────────────────────────────────────────────────

CENARIOS_FATORES = {
    "Pessimista":  {"aluguel": 0.85, "vacancia": 1.5,  "despesas": 1.2,  "tma": 1.3},
    "Realista":    {"aluguel": 1.00, "vacancia": 1.0,  "despesas": 1.0,  "tma": 1.0},
    "Otimista":    {"aluguel": 1.15, "vacancia": 0.5,  "despesas": 0.85, "tma": 0.8},
}


def analisar_cenarios(
    investimento: float,
    aluguel_base: float,
    vacancia_base: float,
    despesas_base: float,
    reajuste_anual: float,
    periodos: int,
    tma_base_mensal: float,
    valor_residual: float = 0,
    fatores: dict = None,
) -> dict:
    fatores = fatores or CENARIOS_FATORES
    resultado = {}
    for nome, f in fatores.items():
        aluguel = aluguel_base * f["aluguel"]
        vacancia = min(vacancia_base * f["vacancia"], 0.99)
        despesas = despesas_base * f["despesas"]
        tma = tma_base_mensal * f["tma"]
        fl = fluxo_locacao(investimento, aluguel, vacancia, despesas,
                           reajuste_anual, periodos, valor_residual)
        ind = indicadores_locacao(fl, tma)
        ind["fluxos"] = fl
        resultado[nome] = ind
    return resultado


# ── Sensibilidade ─────────────────────────────────────────────────────────────

def analise_sensibilidade(
    investimento: float,
    aluguel: float,
    vacancia: float,
    despesas: float,
    reajuste_anual: float,
    periodos: int,
    tma_mensal: float,
    valor_residual: float = 0,
    variacao_pct: float = 0.20,
    n_pontos: int = 11,
) -> dict:
    """
    Varia cada parâmetro isoladamente em ±variacao_pct e mede o VPL resultante.
    """
    base_fl = fluxo_locacao(investimento, aluguel, vacancia, despesas,
                            reajuste_anual, periodos, valor_residual)
    vpl_base = calcular_vpl(base_fl, tma_mensal)

    parametros = {
        "Investimento":    ("investimento",   investimento),
        "Aluguel":         ("aluguel",        aluguel),
        "Vacância":        ("vacancia",       vacancia),
        "Despesas":        ("despesas",       despesas),
        "TMA":             ("tma_mensal",     tma_mensal),
        "Valor Residual":  ("valor_residual", valor_residual),
        "Reajuste Anual":  ("reajuste_anual", reajuste_anual),
    }

    map_key = {
        "investimento": "investimento",
        "aluguel": "aluguel_mensal",
        "vacancia": "taxa_vacancia",
        "despesas": "despesas_mensais",
        "tma_mensal": "tma_mensal",
        "valor_residual": "valor_residual",
        "reajuste_anual": "reajuste_anual",
    }

    resultado = {}
    for label, (key, val_base) in parametros.items():
        deltas = []
        for i in range(n_pontos):
            fator = 1.0 - variacao_pct + i * (2.0 * variacao_pct / (n_pontos - 1))
            val = val_base * fator
            if key == "vacancia":
                val = min(max(val, 0.0), 0.99)
            kwargs = dict(
                investimento=investimento,
                aluguel_mensal=aluguel,
                taxa_vacancia=vacancia,
                despesas_mensais=despesas,
                reajuste_anual=reajuste_anual,
                periodos=periodos,
                tma_mensal=tma_mensal,
                valor_residual=valor_residual,
            )
            fl_key = map_key[key]
            kwargs[fl_key] = val
            fl = fluxo_locacao(
                kwargs["investimento"], kwargs["aluguel_mensal"],
                kwargs["taxa_vacancia"], kwargs["despesas_mensais"],
                kwargs["reajuste_anual"], kwargs["periodos"],
                kwargs["valor_residual"],
            )
            vpl_var = calcular_vpl(fl, kwargs["tma_mensal"])
            deltas.append({"fator": fator, "valor": val, "vpl": vpl_var})

        amplitude = max(d["vpl"] for d in deltas) - min(d["vpl"] for d in deltas)
        resultado[label] = {
            "pontos": deltas,
            "amplitude": amplitude,
            "vpl_base": vpl_base,
            "vpl_fator_min": deltas[0]["vpl"],
            "vpl_fator_max": deltas[-1]["vpl"],
        }

    return resultado
