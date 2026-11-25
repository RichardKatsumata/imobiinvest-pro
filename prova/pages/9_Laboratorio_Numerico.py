"""
Engine Quantitativa e Laboratório Numérico — ImobiInvest Pro
Validação formal dos três métodos numéricos proprietários utilizados pela plataforma.
"""
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from utils.numericos import bissecao, newton_raphson, trapezios
from utils.ui import (
    load_css,
    render_sidebar_brand,
    render_header,
    apply_chart_style,
    COLOR_GOLD,
    COLOR_POS,
    COLOR_NEG,
    COLOR_BLUE,
)

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Engine Quantitativa | ImobiInvest Pro",
    layout="wide",
)

load_css()

with st.sidebar:
    render_sidebar_brand("Quantitative Engine")
    st.caption("Ambiente de auditoria matemática e validação de convergência dos algoritmos numéricos proprietários.")

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
render_header(
    title="Laboratório de Métodos Numéricos e Auditoria Algorítmica",
    subtitle="Inspeção de convergência, estabilidade e erro de truncamento dos motores de Bisseção, Newton-Raphson e Trapézios.",
    category="QUANTITATIVE ENGINE AUDIT",
    code="MOD-09",
)

st.markdown(
    r"""
    | Algoritmo Proprietário | Ordem de Convergência | Aplicação Direta no ImobiInvest Pro |
    |---|---|---|
    | **01. Método da Bisseção** | Linear — $|e_n| \le (b_0 - a_0)/2^n$ | Fronteiras de Break-Even de locação, ocupação crítica e preço mínimo de saída (Flip) |
    | **02. Método de Newton-Raphson** | Quadrática — $|e_{n+1}| \approx C \cdot |e_n|^2$ | Cálculo da Taxa Interna de Retorno (TIR) e Custo Efetivo Total (CET) de financiamentos |
    | **03. Regra dos Trapézios Composta** | $O(h^2) = O(1/n^2)$ | Integração numérica de fluxos de caixa contínuos descontados ($\int_0^T FC(t)e^{-\delta t}dt$) |
    """
)

st.divider()

# ── Funções auxiliares de avaliação segura ────────────────────────────────────
_SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_MATH.update({
    "sin": math.sin, "cos": math.cos, "exp": math.exp,
    "log": math.log, "sqrt": math.sqrt, "pi": math.pi, "e": math.e, "abs": abs,
})


def _eval_func(expr: str, x: float) -> float:
    """Avalia expressão matemática de forma segura."""
    return float(eval(expr, {"__builtins__": {}}, {**_SAFE_MATH, "x": x}))


# ── TABS ──────────────────────────────────────────────────────────────────────
tab_bis, tab_nr, tab_trap = st.tabs([
    "01 · Método da Bisseção",
    "02 · Método de Newton-Raphson",
    "03 · Regra dos Trapézios Composta",
])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — BISSEÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_bis:
    with st.expander("Fundamentação Matemática — Método da Bisseção", expanded=False):
        st.markdown(
            r"""
            ### Método da Bisseção

            Baseado no **Teorema do Valor Intermediário**: sendo $f(x)$ contínua em $[a, b]$ com $f(a)\cdot f(b) < 0$,
            existe ao menos uma raiz real no intervalo. A cada iteração, o intervalo é particionado no ponto médio $m = (a+b)/2$,
            reduzindo o limite superior do erro absoluto exatamente pela metade:

            $$|e_n| \leq \frac{b_0 - a_0}{2^n}$$
            """
        )

    st.subheader("Parâmetros de Execução — Bisseção")
    col1, col2 = st.columns([1, 1])

    with col1:
        func_bis = st.radio(
            "Função Objetivo f(x):",
            ["x³ - x - 2", "x² - 4", "cos(x) - x", "Personalizada"],
            horizontal=True,
            key="func_bis",
        )
        if func_bis == "Personalizada":
            expr_bis = st.text_input(
                "Expressão analítica f(x) (variável x):",
                value="x**3 - x - 2",
                key="expr_bis",
            )
        else:
            expr_bis = {
                "x³ - x - 2": "x**3 - x - 2",
                "x² - 4":     "x**2 - 4",
                "cos(x) - x": "cos(x) - x",
            }[func_bis]

        raiz_conhecida = {
            "x**3 - x - 2": 1.52137971,
            "x**2 - 4":     2.00000000,
            "cos(x) - x":   0.73908513,
        }.get(expr_bis)

        if raiz_conhecida:
            st.caption(f"Raiz de referência: {raiz_conhecida:.8f}")

    with col2:
        a_bis = st.number_input("Limite Inferior (a):", value=-2.0, step=0.5, key="a_bis")
        b_bis = st.number_input("Limite Superior (b):", value=3.0,  step=0.5, key="b_bis")
        tol_bis = st.select_slider(
            "Critério de Tolerância (ε):",
            options=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
            value=1e-6,
            format_func=lambda v: f"{v:.0e}",
            key="tol_bis",
        )

    if st.button("Executar Solver de Bisseção", type="primary", key="btn_bis"):
        try:
            f_bis = lambda x: _eval_func(expr_bis, x)

            fa, fb = f_bis(a_bis), f_bis(b_bis)
            if fa * fb > 0:
                st.error(
                    f"Condição de Bolzano violada: f(a) = {fa:.4f} e f(b) = {fb:.4f} possuem o mesmo sinal. "
                    "Redefina o intervalo [a, b]."
                )
            else:
                raiz, hist = bissecao(f_bis, a_bis, b_bis, tol=tol_bis)
                df_hist = pd.DataFrame(hist)

                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Raiz Convergida (x*)", f"{raiz:.8f}")
                m2.metric("Iterações Executadas", len(hist))
                m3.metric("Cota de Erro Final", f"{hist[-1]['erro']:.2e}")

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_conv = go.Figure()
                    fig_conv.add_trace(go.Scatter(
                        x=df_hist["iter"],
                        y=[max(abs(v), 1e-16) for v in df_hist["f(m)"]],
                        mode="lines+markers",
                        name="|f(m)|",
                        line=dict(color=COLOR_GOLD, width=2),
                        marker=dict(size=5),
                    ))
                    apply_chart_style(fig_conv, title="Decaimento do Resíduo |f(m)| por Iteração", height=360, showlegend=False)
                    fig_conv.update_xaxes(title="Iteração (n)")
                    fig_conv.update_yaxes(title="Resíduo |f(m)| (Escala Log)", type="log")
                    st.plotly_chart(fig_conv, use_container_width=True)

                with col_g2:
                    fig_int = go.Figure()
                    for i, row in df_hist.iterrows():
                        fig_int.add_trace(go.Scatter(
                            x=[row["a"], row["b"]],
                            y=[row["iter"], row["iter"]],
                            mode="lines",
                            line=dict(
                                color=f"rgba(197, 160, 89, {max(0.15, 1 - i / len(df_hist))})",
                                width=4,
                            ),
                            showlegend=False,
                        ))
                    fig_int.add_trace(go.Scatter(
                        x=[raiz],
                        y=[len(hist)],
                        mode="markers",
                        name="Raiz",
                        marker=dict(color=COLOR_POS, size=10, symbol="diamond"),
                    ))
                    apply_chart_style(fig_int, title="Contração Sucessiva do Intervalo [a, b]", height=360, showlegend=False)
                    fig_int.update_xaxes(title="Domínio x")
                    fig_int.update_yaxes(title="Iteração (n)")
                    st.plotly_chart(fig_int, use_container_width=True)

                st.subheader("Registro Analítico de Iterações")
                st.dataframe(
                    df_hist.style.format({
                        "a": "{:.6f}", "b": "{:.6f}", "m": "{:.6f}",
                        "f(m)": "{:.2e}", "erro": "{:.2e}",
                    }),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error(f"Falha na execução numérica: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — NEWTON-RAPHSON
# ═══════════════════════════════════════════════════════════════════════════════
with tab_nr:
    with st.expander("Fundamentação Matemática — Método de Newton-Raphson", expanded=False):
        st.markdown(
            r"""
            ### Método de Newton-Raphson

            Utiliza a aproximação linear de Taylor de primeira ordem (reta tangente) em torno da estimativa atual $x_n$:

            $$x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$$

            Apresenta **convergência quadrática** na vizinhança de raízes simples ($|e_{n+1}| \approx C \cdot |e_n|^2$),
            dobrando o número de algarismos significativos corretos a cada passo.
            """
        )

    st.subheader("Parâmetros de Execução — Newton-Raphson")
    col1, col2 = st.columns([1, 1])

    with col1:
        func_nr = st.radio(
            "Função Objetivo f(x):",
            ["x³ - x - 2", "x² - 4", "sin(x)", "Personalizada"],
            horizontal=True,
            key="func_nr",
        )

        if func_nr == "Personalizada":
            expr_nr  = st.text_input("Expressão f(x):",  value="x**3 - x - 2", key="expr_nr")
            expr_dnr = st.text_input("Derivada Analítica f'(x):", value="3*x**2 - 1", key="expr_dnr")
        else:
            presets_nr = {
                "x³ - x - 2": ("x**3 - x - 2",  "3*x**2 - 1"),
                "x² - 4":     ("x**2 - 4",       "2*x"),
                "sin(x)":     ("sin(x)",          "cos(x)"),
            }
            expr_nr, expr_dnr = presets_nr[func_nr]

            raiz_nr = {"x**3 - x - 2": 1.52137971, "x**2 - 4": 2.00000000, "sin(x)": 0.0}.get(expr_nr)
            if raiz_nr is not None:
                st.caption(f"Raiz de referência: {raiz_nr:.8f}  |  Derivada f'(x) = {expr_dnr}")

    with col2:
        x0_nr  = st.number_input("Estimativa Inicial (x₀):", value=1.0, step=0.5, key="x0_nr")
        tol_nr = st.select_slider(
            "Critério de Tolerância (ε):",
            options=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
            value=1e-6,
            format_func=lambda v: f"{v:.0e}",
            key="tol_nr",
        )

    if st.button("Executar Solver de Newton-Raphson", type="primary", key="btn_nr"):
        try:
            f_nr  = lambda x: _eval_func(expr_nr,  x)
            df_nr = lambda x: _eval_func(expr_dnr, x)

            raiz_nr_res, hist_nr = newton_raphson(f_nr, df_nr, x0_nr, tol=tol_nr)
            df_hist_nr = pd.DataFrame(hist_nr)

            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Raiz Convergida (x*)", f"{raiz_nr_res:.8f}")
            m2.metric("Iterações Executadas", len(hist_nr))
            m3.metric("Deslocamento Final |Δx|", f"{hist_nr[-1]['erro']:.2e}")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                x_min = min(x0_nr, raiz_nr_res) - 2
                x_max = max(x0_nr, raiz_nr_res) + 2
                xs_plot = [x_min + i * (x_max - x_min) / 399 for i in range(400)]
                ys_plot = [f_nr(x) for x in xs_plot]

                fig_tan = go.Figure()
                fig_tan.add_trace(go.Scatter(
                    x=xs_plot, y=ys_plot,
                    mode="lines",
                    name="f(x)",
                    line=dict(color=COLOR_BLUE, width=2.2),
                ))
                fig_tan.add_hline(y=0, line_color="#334155", line_dash="dot")

                cores_tan = [COLOR_GOLD, COLOR_POS, COLOR_NEG, "#94A3B8", "#60A5FA"]
                for i, row in df_hist_nr.iterrows():
                    xi, fxi, dfxi = row["x"], row["f(x)"], row["f'(x)"]
                    x_tan = [xi - 1.5, xi + 1.5]
                    y_tan = [fxi + dfxi * (xt - xi) for xt in x_tan]
                    cor = cores_tan[i % len(cores_tan)]
                    fig_tan.add_trace(go.Scatter(
                        x=x_tan, y=y_tan,
                        mode="lines",
                        name=f"Tangente {i+1}",
                        line=dict(color=cor, width=1, dash="dash"),
                        opacity=0.75,
                    ))
                    fig_tan.add_trace(go.Scatter(
                        x=[xi], y=[fxi],
                        mode="markers",
                        showlegend=False,
                        marker=dict(color=cor, size=6),
                    ))

                fig_tan.add_trace(go.Scatter(
                    x=[raiz_nr_res], y=[0],
                    mode="markers",
                    name="Raiz",
                    marker=dict(color=COLOR_POS, size=11, symbol="diamond"),
                ))

                apply_chart_style(fig_tan, title="Aproximações Sucessivas por Retas Tangentes", height=380)
                fig_tan.update_xaxes(title="x")
                fig_tan.update_yaxes(title="f(x)", range=[max(min(ys_plot), -20), min(max(ys_plot), 20)])
                st.plotly_chart(fig_tan, use_container_width=True)

            with col_g2:
                try:
                    _a, _b = raiz_nr_res - 1.7, raiz_nr_res + 2.3
                    for delta in [1.5, 3.0, 5.0, 10.0]:
                        _a, _b = raiz_nr_res - delta * 0.8, raiz_nr_res + delta * 1.3
                        if f_nr(_a) * f_nr(_b) < 0:
                            break

                    _, hist_bis_comp = bissecao(f_nr, _a, _b, tol=tol_nr)
                    df_bis_comp = pd.DataFrame(hist_bis_comp)

                    fig_cmp = go.Figure()
                    fig_cmp.add_trace(go.Scatter(
                        x=df_hist_nr["iter"],
                        y=[max(abs(v), 1e-16) for v in df_hist_nr["f(x)"]],
                        mode="lines+markers",
                        name="Newton-Raphson (Quadrática)",
                        line=dict(color=COLOR_GOLD, width=2.2),
                        marker=dict(size=6),
                    ))
                    fig_cmp.add_trace(go.Scatter(
                        x=df_bis_comp["iter"],
                        y=[max(abs(v), 1e-16) for v in df_bis_comp["f(m)"]],
                        mode="lines+markers",
                        name="Bisseção (Linear)",
                        line=dict(color=COLOR_BLUE, width=2, dash="dash"),
                        marker=dict(size=5),
                    ))
                    apply_chart_style(fig_cmp, title="Benchmarking de Convergência: Newton-Raphson vs. Bisseção", height=380)
                    fig_cmp.update_xaxes(title="Iteração (n)")
                    fig_cmp.update_yaxes(title="Resíduo |f(x)| (Escala Log)", type="log")
                    st.plotly_chart(fig_cmp, use_container_width=True)
                except Exception:
                    st.info("Comparativo com bisseção indisponível para o intervalo atual.")

            st.subheader("Registro Analítico de Iterações")
            st.dataframe(
                df_hist_nr.style.format({
                    "x": "{:.8f}", "f(x)": "{:.2e}",
                    "f'(x)": "{:.6f}", "x_new": "{:.8f}", "erro": "{:.2e}",
                }),
                use_container_width=True,
            )

        except Exception as exc:
            st.error(f"Falha na execução de Newton-Raphson: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — TRAPÉZIOS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_trap:
    with st.expander("Fundamentação Matemática — Regra dos Trapézios Composta", expanded=False):
        st.markdown(
            r"""
            ### Regra dos Trapézios Composta

            Aproxima a integral definida substituindo $f(x)$ por polinômios interpoladores lineares por partes em $n$ subintervalos de amplitude $h = (b-a)/n$:

            $$\int_a^b f(x)\,dx \approx \frac{h}{2}\left[f(x_0) + 2\sum_{i=1}^{n-1}f(x_i) + f(x_n)\right]$$

            O erro global de truncamento decai quadraticamente com o refinamento da malha ($O(h^2) = O(1/n^2)$).
            """
        )

    st.subheader("Parâmetros de Execução — Quadratura Trapezoidal")
    col1, col2 = st.columns([1, 1])

    _TRAP_PRESETS = {
        "x²":             ("x**2",   1.0, 4.0,     lambda a, b: (b**3 - a**3) / 3),
        "sin(x)":         ("sin(x)", 0.0, math.pi, lambda a, b: -math.cos(b) + math.cos(a)),
        "e^x":            ("exp(x)", 0.0, 2.0,     lambda a, b: math.exp(b) - math.exp(a)),
        "1/x (de 1 a 5)": ("1/x",    1.0, 5.0,     lambda a, b: math.log(b) - math.log(a)),
        "Personalizada":  (None,     0.0, 1.0,     None),
    }

    with col1:
        func_trap = st.radio(
            "Integrando f(x):",
            list(_TRAP_PRESETS.keys()),
            horizontal=False,
            key="func_trap",
        )
        preset = _TRAP_PRESETS[func_trap]
        a_trap_def, b_trap_def = preset[1], preset[2]

        if func_trap == "Personalizada":
            expr_trap = st.text_input(
                "Expressão analítica f(x):",
                value="x**2",
                key="expr_trap",
            )
            exato_trap = None
        else:
            expr_trap = preset[0]
            exato_trap = preset[3]
            st.caption(f"Expressão selecionada: `{expr_trap}`")

    with col2:
        a_trap = st.number_input("Limite Inferior de Integração (a):", value=float(a_trap_def), step=0.5, key="a_trap")
        b_trap = st.number_input("Limite Superior de Integração (b):", value=float(b_trap_def), step=0.5, key="b_trap")
        n_trap = st.slider("Subdivisões da Malha (n):", min_value=2, max_value=500, value=24, key="n_trap")

    if st.button("Executar Quadratura Trapezoidal", type="primary", key="btn_trap"):
        try:
            if a_trap >= b_trap:
                st.error("O limite inferior 'a' deve ser estritamente menor que o limite superior 'b'.")
            else:
                f_trap = lambda x: _eval_func(expr_trap, x)

                integral, pontos = trapezios(f_trap, a_trap, b_trap, n=n_trap)
                df_pts = pd.DataFrame(pontos)

                if exato_trap is not None:
                    try:
                        valor_exato = exato_trap(a_trap, b_trap)
                        erro_abs = abs(integral - valor_exato)
                    except Exception:
                        valor_exato, erro_abs = None, None
                else:
                    valor_exato, erro_abs = None, None

                st.divider()
                cols_m = st.columns(4 if valor_exato is not None else 2)
                cols_m[0].metric("Integral Numérica Aproximada", f"{integral:.8f}")
                cols_m[1].metric("Subintervalos (n)", n_trap)
                if valor_exato is not None:
                    cols_m[2].metric("Integral Analítica Exata", f"{valor_exato:.8f}")
                    cols_m[3].metric("Erro Absoluto de Truncamento", f"{erro_abs:.2e}")

                xs_smooth = [a_trap + i * (b_trap - a_trap) / 499 for i in range(500)]
                ys_smooth = [f_trap(x) for x in xs_smooth]

                fig_trap = go.Figure()

                n_show = min(n_trap, 60)
                step_show = max(1, n_trap // n_show)
                xs_trap = df_pts["x"].tolist()
                ys_trap = df_pts["y"].tolist()

                for i in range(0, n_trap, step_show):
                    x0_t, x1_t = xs_trap[i], xs_trap[i + 1]
                    y0_t, y1_t = ys_trap[i], ys_trap[i + 1]
                    fig_trap.add_trace(go.Scatter(
                        x=[x0_t, x0_t, x1_t, x1_t, x0_t],
                        y=[0, y0_t, y1_t, 0, 0],
                        fill="toself",
                        fillcolor="rgba(197, 160, 89, 0.14)",
                        line=dict(color="rgba(197, 160, 89, 0.45)", width=1),
                        showlegend=(i == 0),
                        name="Partições Trapezoidais",
                        mode="lines",
                    ))

                fig_trap.add_trace(go.Scatter(
                    x=[a_trap] + xs_smooth + [b_trap],
                    y=[0.0] + ys_smooth + [0.0],
                    fill="toself",
                    fillcolor="rgba(16, 185, 129, 0.08)",
                    line=dict(color=COLOR_POS, width=2.2),
                    name=f"f(x) = {expr_trap}",
                    mode="lines",
                ))

                apply_chart_style(
                    fig_trap,
                    title=f"Discretização Trapezoidal (n = {n_trap})  —  Integral = {integral:.6f}",
                    height=400,
                )
                fig_trap.update_xaxes(title="x")
                fig_trap.update_yaxes(title="f(x)")
                st.plotly_chart(fig_trap, use_container_width=True)

                if valor_exato is not None:
                    ns = list(range(2, 201, 2))
                    erros_ns = []
                    for _n in ns:
                        _int, _ = trapezios(f_trap, a_trap, b_trap, n=_n)
                        erros_ns.append(max(abs(_int - valor_exato), 1e-16))

                    fig_err = go.Figure()
                    fig_err.add_trace(go.Scatter(
                        x=ns, y=erros_ns,
                        mode="lines",
                        name="Erro Empírico |E(n)|",
                        line=dict(color=COLOR_NEG, width=2.2),
                    ))
                    err_ref = [erros_ns[0] * (2 / _n) ** 2 for _n in ns]
                    fig_err.add_trace(go.Scatter(
                        x=ns, y=err_ref,
                        mode="lines",
                        name="Declínio Teórico O(1/n²)",
                        line=dict(color=COLOR_GOLD, width=1.5, dash="dash"),
                    ))
                    apply_chart_style(fig_err, title="Curva Assintótica do Erro de Truncamento vs. Malha (n)", height=360)
                    fig_err.update_xaxes(title="Número de Subintervalos (n)")
                    fig_err.update_yaxes(title="Erro Absoluto (Escala Log)", type="log")
                    st.plotly_chart(fig_err, use_container_width=True)

        except Exception as exc:
            st.error(f"Falha na quadratura numérica: {exc}")
