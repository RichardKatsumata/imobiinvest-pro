"""
Implementações do zero (sem bibliotecas prontas de cálculo) dos três métodos
numéricos usados como motor matemático da plataforma ImobiInvest Pro:
1. Método da Bisseção
2. Método de Newton-Raphson
3. Regra dos Trapézios Composta
"""
import math
from typing import Callable, List, Tuple


# ── 1. Método da Bisseção ─────────────────────────────────────────────────────

def bissecao(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-8,
    max_iter: int = 200,
) -> Tuple[float, List[dict]]:
    """
    Encontra raiz de f em [a, b] pelo Método da Bisseção programado do zero.
    Retorna (raiz, historico).
    """
    historico: List[dict] = []
    fa = f(a)
    fb = f(b)

    if abs(fa) < tol:
        historico.append({"iter": 1, "a": a, "b": b, "m": a, "f(m)": fa, "erro": 0.0})
        return a, historico
    if abs(fb) < tol:
        historico.append({"iter": 1, "a": a, "b": b, "m": b, "f(m)": fb, "erro": 0.0})
        return b, historico

    if fa * fb > 0:
        raise ValueError("f(a) e f(b) devem ter sinais opostos no intervalo [a, b].")

    for i in range(max_iter):
        m = (a + b) / 2.0
        fm = f(m)
        erro = abs(b - a) / 2.0
        historico.append({
            "iter": i + 1,
            "a": a,
            "b": b,
            "m": m,
            "f(m)": fm,
            "erro": erro,
        })
        if abs(fm) < tol or erro < tol:
            return m, historico
        if fa * fm < 0:
            b = m
            fb = fm
        else:
            a = m
            fa = fm

    return (a + b) / 2.0, historico


# ── 2. Método de Newton-Raphson ───────────────────────────────────────────────

def newton_raphson(
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    tol: float = 1e-8,
    max_iter: int = 200,
) -> Tuple[float, List[dict]]:
    """
    Encontra raiz de f a partir de x0 pelo Método de Newton-Raphson programado do zero.
    df é a derivada analítica de f.
    Retorna (raiz, historico).
    """
    historico: List[dict] = []
    x = float(x0)

    for i in range(max_iter):
        fx = f(x)
        dfx = df(x)
        if abs(dfx) < 1e-15:
            raise ValueError("Derivada próxima de zero — o método de Newton-Raphson divergiu.")

        x_new = x - fx / dfx
        erro = abs(x_new - x)
        historico.append({
            "iter": i + 1,
            "x": x,
            "f(x)": fx,
            "f'(x)": dfx,
            "x_new": x_new,
            "erro": erro,
        })
        if erro < tol or abs(fx) < tol:
            return x_new, historico
        x = x_new

    return x, historico


# ── 3. Regra dos Trapézios Composta ───────────────────────────────────────────

def trapezios(
    f: Callable[[float], float],
    a: float,
    b: float,
    n: int = 1000,
) -> Tuple[float, List[dict]]:
    """
    Integra f em [a, b] pela Regra dos Trapézios Composta com n subintervalos,
    programada do zero.
    Retorna (integral, pontos para visualização).
    """
    if n < 1:
        raise ValueError("O número de subintervalos n deve ser pelo menos 1.")
    h = (b - a) / float(n)
    xs = [a + i * h for i in range(n + 1)]
    ys = [f(x) for x in xs]

    soma_interna = 0.0
    for i in range(1, n):
        soma_interna += ys[i]

    integral = h * (0.5 * ys[0] + soma_interna + 0.5 * ys[-1])
    pontos = [{"x": xs[i], "y": ys[i], "trapezio": i} for i in range(n + 1)]
    return integral, pontos


# ── VPL (Valor Presente Líquido) ──────────────────────────────────────────────

def calcular_vpl(fluxos: List[float], taxa: float) -> float:
    """
    Calcula o VPL de uma série de fluxos de caixa:
    VPL(r) = sum_{t=0}^{n} FC_t / (1 + r)^t
    """
    if taxa <= -1.0:
        return float("nan")
    soma = 0.0
    base = 1.0 + taxa
    fator = 1.0
    for t, fc in enumerate(fluxos):
        if t > 0:
            fator *= base
            if fator == 0.0 or math.isinf(fator):
                break
        soma += fc / fator
    return soma


def calcular_dvpl(fluxos: List[float], taxa: float) -> float:
    """
    Derivada analítica do VPL em relação à taxa r:
    VPL'(r) = sum_{t=1}^{n} -t * FC_t / (1 + r)^(t + 1)
    """
    if taxa <= -1.0:
        return float("nan")
    soma = 0.0
    base = 1.0 + taxa
    fator = base  # (1 + r)^1
    for t, fc in enumerate(fluxos):
        if t == 0:
            continue
        fator *= base  # (1 + r)^(t + 1)
        if fator == 0.0 or math.isinf(fator):
            break
        soma += (-t * fc) / fator
    return soma


# ── TIR via Newton-Raphson (com fallback em Bisseção) ─────────────────────────

def calcular_tir_detalhado(
    fluxos: List[float],
    tol: float = 1e-8,
    max_iter: int = 200,
) -> Tuple[float, List[dict], str]:
    """
    Calcula a TIR (Taxa Interna de Retorno) resolvendo VPL(r) = 0 pelo
    Método de Newton-Raphson (com Bisseção para localização de intervalo se necessário).
    Retorna (tir, historico_iteracoes, metodo_usado).
    """
    if not fluxos or len(fluxos) < 2:
        return float("nan"), [], "Inválido"

    # Verifica se há pelo menos uma mudança de sinal nos fluxos
    tem_pos = any(fc > 0 for fc in fluxos)
    tem_neg = any(fc < 0 for fc in fluxos)
    if not (tem_pos and tem_neg):
        return float("nan"), [], "Sem mudança de sinal"

    def vpl(r: float) -> float:
        # Limita r para evitar divisão por zero ou underflow em horizontes longos
        r_safe = max(r, -0.90)
        return calcular_vpl(fluxos, r_safe)

    def dvpl(r: float) -> float:
        r_safe = max(r, -0.90)
        return calcular_dvpl(fluxos, r_safe)

    # 1) Tenta Newton-Raphson diretamente com chute inicial x0 = 0.01 (1% a.m.)
    try:
        tir_nr, hist_nr = newton_raphson(vpl, dvpl, x0=0.01, tol=tol, max_iter=max_iter)
        if -0.85 < tir_nr < 10.0 and abs(vpl(tir_nr)) < 1e-4:
            return tir_nr, hist_nr, "Newton-Raphson"
    except Exception:
        pass

    # 2) Se x0=0.01 não convergiu direto, localiza intervalo via varredura e aplica Bisseção + Newton-Raphson
    grade = [-0.50, -0.25, -0.10, -0.05, -0.01, 0.0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 5.0]
    a_brk, b_brk = None, None
    for i in range(len(grade) - 1):
        va = vpl(grade[i])
        vb = vpl(grade[i + 1])
        if not (math.isnan(va) or math.isnan(vb)) and va * vb <= 0:
            a_brk, b_brk = grade[i], grade[i + 1]
            break

    if a_brk is not None and b_brk is not None:
        try:
            # Pré-aproxima com 5 passos de bisseção e refina com Newton-Raphson
            chute, hist_bis = bissecao(vpl, a_brk, b_brk, tol=1e-3, max_iter=15)
            try:
                tir_nr, hist_nr = newton_raphson(vpl, dvpl, x0=chute, tol=tol, max_iter=max_iter)
                if a_brk - 0.1 <= tir_nr <= b_brk + 0.1 and abs(vpl(tir_nr)) < 1e-4:
                    return tir_nr, hist_nr, "Newton-Raphson (híbrido com Bisseção)"
            except Exception:
                pass
            tir_bis, hist_bis_full = bissecao(vpl, a_brk, b_brk, tol=tol, max_iter=max_iter)
            return tir_bis, hist_bis_full, "Bisseção"
        except Exception:
            pass

    return float("nan"), [], "Não convergiu"


def calcular_tir(fluxos: List[float], tol: float = 1e-8, max_iter: int = 200) -> float:
    """
    Calcula a TIR de uma série de fluxos de caixa.
    fluxos[0] é o investimento inicial (negativo).
    """
    tir, _, _ = calcular_tir_detalhado(fluxos, tol=tol, max_iter=max_iter)
    return tir


# ── VPL Contínuo via Regra dos Trapézios ──────────────────────────────────────

def calcular_vpl_continuo(
    investimento: float,
    fluxo_continuo_fn: Callable[[float], float],
    taxa_mensal: float,
    periodos: int,
    valor_residual: float = 0.0,
    n_trapezios: int = 240,
) -> Tuple[float, List[dict]]:
    """
    Calcula o VPL considerando fluxo de caixa contínuo ao longo de [0, periodos]
    integrado numericamente pela Regra dos Trapézios Composta:
        VPL_cont = -Investimento + ∫_0^T FC(t) * e^(-δ * t) dt + VR * e^(-δ * T)
    onde δ = ln(1 + taxa_mensal) é a taxa instantânea de desconto.
    """
    delta = math.log(1.0 + max(taxa_mensal, 0.0))

    def integrando(t: float) -> float:
        return fluxo_continuo_fn(t) * math.exp(-delta * t)

    vp_fluxos, pontos = trapezios(integrando, 0.0, float(periodos), n=n_trapezios)
    vp_residual = valor_residual * math.exp(-delta * periodos)
    vpl_cont = -investimento + vp_fluxos + vp_residual
    return vpl_cont, pontos


# ── Payback ───────────────────────────────────────────────────────────────────

def calcular_payback(fluxos: List[float]) -> float:
    """Payback simples em períodos (meses). fluxos[0] negativo."""
    acum = 0.0
    for t, fc in enumerate(fluxos):
        acum += fc
        if acum >= 0 and t > 0:
            return t
    return float("inf")


def calcular_payback_descontado(fluxos: List[float], taxa: float) -> float:
    """Payback descontado em períodos (meses)."""
    acum = 0.0
    base = 1.0 + taxa
    fator = 1.0
    for t, fc in enumerate(fluxos):
        if t > 0:
            fator *= base
        acum += fc / fator
        if acum >= 0 and t > 0:
            return t
    return float("inf")
