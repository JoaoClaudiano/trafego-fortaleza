"""
charts.py — funções de visualização Plotly para o VMD Fortaleza
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Paleta principal
C_ALTO   = "#e63946"
C_MEDIO  = "#f4a261"
C_BAIXO  = "#2a9d8f"
C_NEUTRO = "#457b9d"
C_BG     = "#0f1117"
C_SURFACE = "#1a1e2e"
C_BORDER  = "#2d3250"
C_TEXT    = "#e8eaf0"
C_MUTED   = "#8892a4"

TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'DM Sans', sans-serif", color=C_TEXT, size=12),
        colorway=[C_NEUTRO, C_ALTO, C_BAIXO, C_MEDIO, "#a8dadc"],
        xaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER, zerolinecolor=C_BORDER),
        yaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER, zerolinecolor=C_BORDER),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER, borderwidth=1),
    )
)


def apply_template(fig):
    fig.update_layout(**TEMPLATE["layout"])
    return fig


# ── Top vias ──────────────────────────────────────────────────────────────────
def chart_top_vias(df: pd.DataFrame, n: int = 20, periodo: str = "") -> go.Figure:
    top = (
        df.groupby("ViaSentido")["VMD"]
        .mean().round().astype(int)
        .sort_values(ascending=False)
        .head(n).reset_index()
    )
    top["Cor"] = top["VMD"].apply(
        lambda v: C_ALTO if v >= 20_000 else C_MEDIO if v >= 8_000 else C_BAIXO
    )
    top["Label"] = top["VMD"].apply(lambda v: f"{v:,}".replace(",", "."))

    fig = go.Figure(go.Bar(
        x=top["VMD"],
        y=top["ViaSentido"],
        orientation="h",
        marker=dict(color=top["Cor"], line=dict(width=0)),
        text=top["Label"],
        textposition="outside",
        textfont=dict(size=11, color=C_MUTED),
        hovertemplate="<b>%{y}</b><br>VMD: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Top {n} vias por VMD médio" + (f" — {periodo}" if periodo else ""), font=dict(size=14)),
        yaxis=dict(categoryorder="total ascending", tickfont=dict(size=10)),
        height=max(420, n * 26),
        xaxis_title="VMD médio (veículos/dia)",
    )
    return apply_template(fig)


# ── Série temporal geral ──────────────────────────────────────────────────────
def chart_serie_geral(serie: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.06,
    )

    # linha VMD médio
    fig.add_trace(go.Scatter(
        x=serie["Data"], y=serie["VMD"],
        mode="lines+markers",
        line=dict(color=C_NEUTRO, width=2.5),
        marker=dict(size=5, color=C_NEUTRO),
        name="VMD médio",
        hovertemplate="%{x}<br>VMD: %{y:,.0f}<extra></extra>",
    ), row=1, col=1)

    # banda de média móvel 3 meses
    if len(serie) >= 3:
        mm = serie["VMD"].rolling(3, center=True).mean()
        fig.add_trace(go.Scatter(
            x=pd.concat([serie["Data"], serie["Data"][::-1]]),
            y=pd.concat([mm + mm * 0.05, (mm - mm * 0.05)[::-1]]),
            fill="toself",
            fillcolor="rgba(69,123,157,0.12)",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=serie["Data"], y=mm,
            mode="lines",
            line=dict(color=C_NEUTRO, width=1, dash="dot"),
            name="Média móvel 3m",
            hovertemplate="%{x}<br>MM3: %{y:,.0f}<extra></extra>",
        ), row=1, col=1)

    # barras de variação percentual
    colors_var = [C_ALTO if v < 0 else C_BAIXO for v in serie["VarPerc"].fillna(0)]
    fig.add_trace(go.Bar(
        x=serie["Data"], y=serie["VarPerc"],
        marker_color=colors_var,
        name="Var. % m/m",
        hovertemplate="%{x}<br>Variação: %{y:.1f}%<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=0, line_dash="dot", line_color=C_BORDER, row=2, col=1)

    fig.update_layout(
        height=480,
        title=dict(text="Evolução mensal do VMD médio geral", font=dict(size=14)),
        xaxis2_title="",
        yaxis_title="VMD médio",
        yaxis2_title="Var. %",
    )
    return apply_template(fig)


# ── Estatísticas anuais ───────────────────────────────────────────────────────
def chart_anual(df: pd.DataFrame) -> go.Figure:
    anual = df.groupby("Ano").agg(
        VMD_medio=("VMD", "mean"),
        VMD_max=("VMD", "max"),
        VMD_min=("VMD", "min"),
        Registros=("VMD", "count"),
    ).reset_index()
    anual["VMD_medio"] = anual["VMD_medio"].round().astype(int)

    fig = go.Figure()
    # faixa min-max
    fig.add_trace(go.Scatter(
        x=pd.concat([anual["Ano"], anual["Ano"][::-1]]),
        y=pd.concat([anual["VMD_max"], anual["VMD_min"][::-1]]),
        fill="toself",
        fillcolor="rgba(69,123,157,0.15)",
        line=dict(width=0),
        name="Faixa min–max",
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=anual["Ano"], y=anual["VMD_max"],
        mode="lines+markers", line=dict(color=C_ALTO, width=1.5, dash="dot"),
        marker=dict(size=5), name="Máximo anual",
    ))
    fig.add_trace(go.Scatter(
        x=anual["Ano"], y=anual["VMD_medio"],
        mode="lines+markers+text", line=dict(color=C_NEUTRO, width=3),
        marker=dict(size=8, symbol="diamond"), name="Média anual",
        text=anual["VMD_medio"].apply(lambda v: f"{v:,}".replace(",", ".")),
        textposition="top center",
        textfont=dict(size=10, color=C_TEXT),
    ))
    fig.add_trace(go.Scatter(
        x=anual["Ano"], y=anual["VMD_min"],
        mode="lines+markers", line=dict(color=C_BAIXO, width=1.5, dash="dot"),
        marker=dict(size=5), name="Mínimo anual",
    ))

    fig.update_layout(
        title=dict(text="Estatísticas anuais de VMD", font=dict(size=14)),
        xaxis_title="Ano", yaxis_title="VMD",
        height=380,
    )
    return apply_template(fig)


# ── Boxplot por mês (sazonalidade) ─────────────────────────────────────────────
def chart_sazonalidade(df: pd.DataFrame) -> go.Figure:
    meses_label = {
        "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
        "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
    }
    df2 = df.copy()
    df2["MesLabel"] = df2["Mes"].map(meses_label)

    fig = go.Figure()
    for m_num, m_label in meses_label.items():
        vals = df2[df2["Mes"] == m_num]["VMD"]
        if vals.empty:
            continue
        fig.add_trace(go.Box(
            y=vals,
            name=m_label,
            marker_color=C_NEUTRO,
            line_color=C_NEUTRO,
            fillcolor="rgba(69,123,157,0.25)",
            boxmean=True,
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(text="Sazonalidade — distribuição do VMD por mês", font=dict(size=14)),
        xaxis_title="Mês", yaxis_title="VMD",
        height=360,
    )
    return apply_template(fig)


# ── Heatmap via × mês ─────────────────────────────────────────────────────────
def chart_heatmap_vias(df: pd.DataFrame, n: int = 25) -> go.Figure:
    top_vias = (
        df.groupby("ViaSentido")["VMD"].mean()
        .sort_values(ascending=False).head(n).index.tolist()
    )
    pivot = (
        df[df["ViaSentido"].isin(top_vias)]
        .groupby(["ViaSentido", "Data"])["VMD"]
        .mean().round().astype(int)
        .unstack("Data")
        .fillna(0)
    )
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#1a1e2e"], [0.3, C_BAIXO], [0.7, C_MEDIO], [1, C_ALTO]],
        hovertemplate="<b>%{y}</b><br>%{x}<br>VMD: %{z:,}<extra></extra>",
        colorbar=dict(title="VMD", tickfont=dict(color=C_TEXT)),
    ))
    fig.update_layout(
        title=dict(text=f"Heatmap — VMD das top {n} vias ao longo do tempo", font=dict(size=14)),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
        height=max(400, n * 22),
    )
    return apply_template(fig)


# ── Comparação entre períodos ─────────────────────────────────────────────────
def chart_comparacao(comp: pd.DataFrame, p1: str, p2: str) -> go.Figure:
    top = comp.head(20)
    colors = [C_ALTO if v < 0 else C_BAIXO for v in top["Variacao"]]

    fig = go.Figure(go.Bar(
        x=top["Variacao"],
        y=top["ViaSentido"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=top["Variacao"].apply(lambda v: f"{v:+.1f}%"),
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Variação: %{x:.1f}%<br><extra></extra>",
    ))
    fig.add_vline(x=0, line_color=C_MUTED, line_dash="dot")
    fig.update_layout(
        title=dict(text=f"Variação do VMD: {p1} → {p2}", font=dict(size=14)),
        xaxis_title="Variação (%)",
        yaxis=dict(categoryorder="total ascending"),
        height=520,
    )
    return apply_template(fig)


# ── Scatter comparação ────────────────────────────────────────────────────────
def chart_scatter_comp(comp: pd.DataFrame, p1: str, p2: str) -> go.Figure:
    lim = max(comp["VMD_P1"].max(), comp["VMD_P2"].max()) * 1.05
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, lim], y=[0, lim],
        mode="lines", line=dict(color=C_BORDER, dash="dot", width=1),
        showlegend=False, hoverinfo="skip",
    ))
    colors = [C_ALTO if v < -5 else C_BAIXO if v > 5 else C_MUTED for v in comp["Variacao"]]
    fig.add_trace(go.Scatter(
        x=comp["VMD_P1"], y=comp["VMD_P2"],
        mode="markers",
        marker=dict(color=colors, size=9, opacity=0.8, line=dict(width=0.5, color=C_BORDER)),
        text=comp["ViaSentido"],
        # Substitua a linha 284 em charts.py por esta:
        hovertemplate = f"<b>%{{text}}</b><br>{p1}: %{{x:,}}<br>{p2}: %{{y:,}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"VMD {p1} vs {p2} por via", font=dict(size=14)),
        xaxis_title=f"VMD {p1}", yaxis_title=f"VMD {p2}",
        height=420,
    )
    return apply_template(fig)


# ── Anomalias ────────────────────────────────────────────────────────────────
def chart_anomalias(anomalias: pd.DataFrame) -> go.Figure:
    top = anomalias.head(30)
    fig = go.Figure(go.Bar(
        x=top["Z"],
        y=top["ViaSentido"] + " (" + top["Data"] + ")",
        orientation="h",
        marker=dict(
            color=top["Z"],
            colorscale=[[0, C_MEDIO], [1, C_ALTO]],
            showscale=True,
            colorbar=dict(title="Z-score", tickfont=dict(color=C_TEXT)),
            line=dict(width=0),
        ),
        text=top["VMD"].apply(lambda v: f"{v:,}".replace(",", ".")),
        textposition="outside",
        textfont=dict(size=10, color=C_MUTED),
        hovertemplate="<b>%{y}</b><br>Z-score: %{x:.2f}<br>VMD: %{text}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Anomalias detectadas (Z-score ≥ 2.5)", font=dict(size=14)),
        xaxis_title="Z-score",
        yaxis=dict(categoryorder="total ascending", tickfont=dict(size=9)),
        height=max(400, len(top) * 24),
    )
    return apply_template(fig)


# ── Mapa ─────────────────────────────────────────────────────────────────────
def chart_mapa(df: pd.DataFrame) -> go.Figure:
    geo = df.dropna(subset=["Lat", "Lon"])
    geo = geo[geo["Lat"].between(-4.2, -3.5) & geo["Lon"].between(-39.0, -38.3)]
    if geo.empty:
        return None

    fig = px.scatter_mapbox(
        geo,
        lat="Lat", lon="Lon",
        color="VMD",
        size="VMD",
        size_max=18,
        hover_name="ViaSentido",
        hover_data={"Data": True, "VMD": True, "Bairro": True, "Lat": False, "Lon": False},
        color_continuous_scale=[[0, C_BAIXO], [0.5, C_MEDIO], [1, C_ALTO]],
        zoom=11,
        mapbox_style="carto-darkmatter",
        opacity=0.8,
    )
    fig.update_layout(
        height=540,
        margin=dict(r=0, t=0, l=0, b=0),
        coloraxis_colorbar=dict(title="VMD", tickfont=dict(color=C_TEXT)),
    )
    return fig


# ── Bairros ───────────────────────────────────────────────────────────────────
def chart_bairros(df: pd.DataFrame) -> go.Figure:
    bairro_df = (
        df[df["Bairro"] != "Não identificado"]
        .groupby("Bairro")["VMD"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "VMD_medio", "count": "Registros"})
        .reset_index()
        .sort_values("VMD_medio", ascending=False)
    )
    bairro_df["VMD_medio"] = bairro_df["VMD_medio"].round().astype(int)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bairro_df["Bairro"],
        y=bairro_df["VMD_medio"],
        marker=dict(
            color=bairro_df["VMD_medio"],
            colorscale=[[0, C_BAIXO], [0.5, C_MEDIO], [1, C_ALTO]],
            showscale=False,
            line=dict(width=0),
        ),
        text=bairro_df["VMD_medio"].apply(lambda v: f"{v:,}".replace(",", ".")),
        textposition="outside",
        textfont=dict(size=10, color=C_MUTED),
        hovertemplate="<b>%{x}</b><br>VMD médio: %{y:,}<br>Registros: %{customdata}<extra></extra>",
        customdata=bairro_df["Registros"],
    ))
    fig.update_layout(
        title=dict(text="VMD médio por bairro", font=dict(size=14)),
        xaxis_title="", yaxis_title="VMD médio",
        xaxis=dict(tickangle=-35),
        height=400,
    )
    return apply_template(fig)
