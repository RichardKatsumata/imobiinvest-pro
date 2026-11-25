"""
Módulo de Identidade Visual Institucional — ImobiInvest Pro
Padroniza cabeçalhos executivos, branding de sidebar e temas de gráficos Plotly.
"""
from pathlib import Path
import streamlit as st

# ── Paleta Corporativa Institucional ──────────────────────────────────────────
COLOR_NAVY_BG = "#0A0E17"
COLOR_SURFACE = "#0F1623"
COLOR_BORDER  = "#1E293B"
COLOR_TEXT    = "#F8FAFC"
COLOR_MUTED   = "#94A3B8"
COLOR_GOLD    = "#C5A059"
COLOR_BLUE    = "#3B82F6"
COLOR_POS     = "#10B981"
COLOR_NEG     = "#EF4444"
COLOR_SLATE   = "#64748B"

INSTITUTIONAL_PALETTE = [
    "#C5A059",  # Champagne Gold
    "#3B82F6",  # Institutional Blue
    "#10B981",  # Emerald
    "#64748B",  # Slate
    "#94A3B8",  # Light Slate
    "#1E40AF",  # Deep Navy Blue
]

PLOTLY_TEMA = dict(
    template="plotly_dark",
    paper_bgcolor=COLOR_NAVY_BG,
    plot_bgcolor=COLOR_SURFACE,
    font=dict(
        family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        color=COLOR_TEXT,
        size=12,
    ),
    hoverlabel=dict(
        bgcolor="#0F1623",
        bordercolor=COLOR_GOLD,
        font=dict(family="JetBrains Mono, monospace", size=12, color=COLOR_TEXT),
    ),
)


def load_css():
    """Carrega a folha de estilos corporativa."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_sidebar_brand(subtitle: str = "Quantitative Real Estate"):
    """Renderiza a assinatura institucional no topo da barra lateral."""
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">IMOBIINVEST <span>PRO</span></div>
            <div class="sidebar-brand-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str, category: str = "PORTFOLIO ANALYTICS", code: str = "MOD-00"):
    """Renderiza o cabeçalho executivo institucional no topo da página."""
    st.markdown(
        f"""
        <div class="inst-header">
            <div>
                <div class="inst-header-meta">IMOBIINVEST PRO &nbsp;/&nbsp; {category}</div>
                <h1 class="inst-header-title">{title}</h1>
                <div class="inst-header-subtitle">{subtitle}</div>
            </div>
            <div class="inst-header-badge">{code} &nbsp;·&nbsp; ENGINE NUMERICO ATIVO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_style(fig, title: str = None, height: int = 400, showlegend: bool = True):
    """Aplica o acabamento visual de plataforma financeira internacional a uma figura Plotly."""
    layout_kwargs = dict(
        **PLOTLY_TEMA,
        height=height,
        showlegend=showlegend,
        margin=dict(t=55 if title else 30, b=45, l=55, r=25),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLOR_MUTED, size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
        ),
    )
    if title:
        layout_kwargs["title"] = dict(
            text=title.upper(),
            font=dict(size=12, color=COLOR_GOLD, family="Inter, sans-serif"),
            x=0.0,
            xanchor="left",
        )
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.08)",
        zerolinecolor="#1E293B",
        tickfont=dict(color=COLOR_MUTED, size=11),
        title_font=dict(color=COLOR_MUTED, size=11),
    )
    fig.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.08)",
        zerolinecolor="#1E293B",
        tickfont=dict(color=COLOR_MUTED, size=11, family="JetBrains Mono, monospace"),
        title_font=dict(color=COLOR_MUTED, size=11),
    )
    return fig
