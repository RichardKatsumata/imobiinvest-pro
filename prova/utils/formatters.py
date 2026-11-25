import math


def brl(valor: float) -> str:
    """Formata float como R$ 1.234.567,89"""
    if valor is None or (isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor))):
        return "R$ 0,00"
    neg = valor < 0
    s = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {s}" if neg else f"R$ {s}"


def pct(valor: float, casas: int = 2) -> str:
    if valor is None or (isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor))):
        return "—"
    return f"{valor:.{casas}f}%"


def num(valor: float, casas: int = 2) -> str:
    if valor is None or (isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor))):
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
