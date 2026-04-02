"""
app.py — VMD Fortaleza Dashboard v2
"""

import pandas as pd
import streamlit as st

from data import load_data, detect_anomalies, mom_variation, compare_periods
from charts import (
    chart_top_vias, chart_serie_geral, chart_anual, chart_sazonalidade,
    chart_heatmap_vias, chart_comparacao, chart_scatter_comp,
    chart_anomalias, chart_mapa, chart_bairros,
)

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VMD Fortaleza",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* fundo escuro geral */
.stApp { background: #0f1117; }
section[data-testid="stSidebar"] { background: #13161f !important; border-right: 1px solid #2d3250; }

/* cards de métrica */
[data-testid="metric-container"] {
    background: #1a1e2e;
    border: 1px solid #2d3250;
    border-radius: 12px;
    padding: 1rem 1.25rem !important;
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #8892a4 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 600 !important;
    color: #e8eaf0 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #13161f;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid #2d3250;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    padding: 6px 18px !important;
    font-size: 13px !important;
    color: #8892a4 !important;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #2d3250 !important;
    color: #e8eaf0 !important;
}

/* inputs/selects */
.stSelectbox > div, .stTextInput > div, .stSlider {
    background: transparent !important;
}
div[data-baseweb="select"] > div {
    background: #1a1e2e !important;
    border-color: #2d3250 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
    font-size: 13px !important;
}
input[type="text"] {
    background: #1a1e2e !important;
    border-color: #2d3250 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}

/* botões */
.stButton > button {
    background: #2d3250 !important;
    border: 1px solid #3d4470 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 16px !important;
    transition: all .15s;
}
.stButton > button:hover {
    background: #3d4470 !important;
    border-color: #5a6090 !important;
}

/* download button */
.stDownloadButton > button {
    background: #1d3557 !important;
    border: 1px solid #457b9d !important;
    border-radius: 8px !important;
    color: #a8dadc !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* dataframe */
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #2d3250; }

/* divider */
hr { border-color: #2d3250 !important; }

/* cabeçalho da sidebar */
.sidebar-header {
    font-size: 11px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #8892a4;
    margin-bottom: .5rem;
    padding-bottom: .4rem;
    border-bottom: 1px solid #2d3250;
}

/* badge de status */
.badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 10px;
    border-radius: 99px;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
}
.badge-alto   { background: rgba(230,57,70,.18); color: #e63946; border: 1px solid rgba(230,57,70,.3); }
.badge-medio  { background: rgba(244,162,97,.18); color: #f4a261; border: 1px solid rgba(244,162,97,.3); }
.badge-baixo  { background: rgba(42,157,143,.18); color: #2a9d8f; border: 1px solid rgba(42,157,143,.3); }
.badge-anomalia { background: rgba(230,57,70,.25); color: #ff6b6b; border: 1px solid rgba(230,57,70,.4); }

/* hero header */
.hero {
    background: linear-gradient(135deg, #1a1e2e 0%, #0f1117 100%);
    border: 1px solid #2d3250;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.hero-title {
    font-size: 22px;
    font-weight: 600;
    color: #e8eaf0;
    margin: 0;
}
.hero-sub {
    font-size: 13px;
    color: #8892a4;
    margin: 2px 0 0;
}

/* alerta de anomalia */
.anomaly-card {
    background: rgba(230,57,70,.08);
    border: 1px solid rgba(230,57,70,.25);
    border-left: 3px solid #e63946;
    border-radius: 8px;
    padding: .75rem 1rem;
    margin-bottom: .5rem;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)


# ── Dados ─────────────────────────────────────────────────────────────────────
try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Erro ao baixar os dados: {e}")
    st.stop()

periodos = sorted(df["Data"].unique())
anos     = sorted(df["Ano"].unique())

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <span style="font-size:32px">🚦</span>
  <div>
    <p class="hero-title">Volume Médio Diário de Tráfego — Fortaleza</p>
    <p class="hero-sub">
      Portal de Dados Abertos · Prefeitura de Fortaleza &nbsp;|&nbsp;
      {len(df):,} registros · {df["Data"].nunique()} períodos · {df["ViaSentido"].nunique()} vias
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-header">Filtros globais</p>', unsafe_allow_html=True)

    periodo_sel = st.selectbox("📅 Período", ["Todos"] + periodos)
    via_busca   = st.text_input("🔍 Via (filtro parcial)", placeholder="ex: BEIRA MAR")
    bairro_sel  = st.selectbox(
        "🏘️ Bairro",
        ["Todos"] + sorted([b for b in df["Bairro"].unique() if b not in ("Outros", "Não identificado")]) + ["Outros"],
    )

    st.divider()
    st.markdown('<p class="sidebar-header">Comparação de períodos</p>', unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2)
    p1 = col_p1.selectbox("De", periodos, index=0, key="p1")
    p2 = col_p2.selectbox("Para", periodos, index=min(1, len(periodos)-1), key="p2")

    st.divider()
    st.markdown('<p class="sidebar-header">Anomalias</p>', unsafe_allow_html=True)
    z_thresh = st.slider("Z-score mínimo", 1.5, 4.0, 2.5, 0.1)

    st.divider()
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Filtragem ─────────────────────────────────────────────────────────────────
filt = df.copy()
if periodo_sel != "Todos":
    filt = filt[filt["Data"] == periodo_sel]
if via_busca:
    filt = filt[filt["ViaSentido"].str.upper().str.contains(via_busca.upper(), na=False)]
if bairro_sel != "Todos":
    filt = filt[filt["Bairro"] == bairro_sel]

# ── Métricas ──────────────────────────────────────────────────────────────────
vmd_medio_geral = int(df["VMD"].mean())
vmd_medio_filt  = int(filt["VMD"].mean()) if len(filt) else 0
delta_medio     = f"{((vmd_medio_filt - vmd_medio_geral) / vmd_medio_geral * 100):+.1f}% vs total" if len(filt) else None

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Registros filtrados",  f"{len(filt):,}")
m2.metric("VMD médio",            f"{vmd_medio_filt:,}", delta=delta_medio)
m3.metric("VMD máximo",           f"{int(filt['VMD'].max()):,}" if len(filt) else "—")
m4.metric("Vias monitoradas",     f"{filt['ViaSentido'].nunique():,}" if len(filt) else "—")
m5.metric("Bairros cobertos",     f"{filt[filt['Bairro'] != 'Não identificado']['Bairro'].nunique():,}" if len(filt) else "—")

st.write("")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📋 Dados",
    "📊 Ranking de vias",
    "📈 Série temporal",
    "📆 Estatísticas anuais",
    "🏘️ Por bairro",
    "🔀 Comparar períodos",
    "⚠️ Anomalias",
    "🗺️ Mapa",
])

# ── Tab 0: Dados ──────────────────────────────────────────────────────────────
with tabs[0]:
    def badge_html(v):
        if v >= 20_000: return '<span class="badge badge-alto">Alto</span>'
        if v >= 8_000:  return '<span class="badge badge-medio">Médio</span>'
        return '<span class="badge badge-baixo">Baixo</span>'

    col_sort = st.selectbox(
        "Ordenar por",
        ["VMD (maior)", "VMD (menor)", "Via A–Z", "Data (recente)"],
        key="sort_tab0",
    )
    sort_map = {
        "VMD (maior)":    ("VMD", False),
        "VMD (menor)":    ("VMD", True),
        "Via A–Z":        ("ViaSentido", True),
        "Data (recente)": ("Data", False),
    }
    c, a = sort_map[col_sort]
    exibir = filt.sort_values(c, ascending=a)[["Data","ViaSentido","VMD","Bairro","Sitio"]].reset_index(drop=True)

    st.dataframe(
        exibir,
        use_container_width=True,
        height=460,
        column_config={
            "VMD": st.column_config.NumberColumn("VMD", format="%d"),
            "Data": st.column_config.TextColumn("Período"),
        },
    )
    st.caption(f"{len(exibir):,} registros exibidos")

    csv_bytes = filt.to_csv(index=False).encode("utf-8")
    nome = f"vmd_fortaleza{'_'+periodo_sel if periodo_sel != 'Todos' else ''}.csv"
    st.download_button("⬇️ Baixar CSV filtrado", csv_bytes, nome, "text/csv")

# ── Tab 1: Ranking de vias ───────────────────────────────────────────────────
with tabs[1]:
    c1, c2 = st.columns([3, 1])
    n_top = c2.slider("Nº de vias", 10, 50, 20, key="ntop")
    c1.write("")

    st.plotly_chart(chart_top_vias(filt, n_top, periodo_sel if periodo_sel != "Todos" else ""), use_container_width=True)

    st.divider()
    st.subheader("Heatmap temporal")
    n_heat = st.slider("Nº de vias no heatmap", 10, 40, 20, key="nheat")
    st.plotly_chart(chart_heatmap_vias(filt if periodo_sel == "Todos" else df, n_heat), use_container_width=True)

# ── Tab 2: Série temporal ─────────────────────────────────────────────────────
with tabs[2]:
    serie_geral = mom_variation(df if periodo_sel == "Todos" else df)

    st.plotly_chart(chart_serie_geral(serie_geral), use_container_width=True)

    st.divider()
    st.subheader("Série de uma via específica")
    via_serie = st.text_input("Nome da via", placeholder="ex: AV. FRANCISCO SA", key="via_serie")
    if via_serie:
        sub = df[df["ViaSentido"].str.upper().str.contains(via_serie.upper(), na=False)]
        if sub.empty:
            st.warning("Nenhuma via encontrada.")
        else:
            import plotly.express as px
            serie_via = (
                sub.groupby(["Data","ViaSentido"])["VMD"]
                .mean().round().astype(int).reset_index().sort_values("Data")
            )
            from charts import apply_template, C_NEUTRO, C_ALTO, C_MEDIO, C_BAIXO, C_TEXT, C_MUTED, C_BORDER
            import plotly.express as px
            fig_via = px.line(
                serie_via, x="Data", y="VMD", color="ViaSentido",
                markers=True, labels={"Data": "Período"},
                title=f'Série temporal — "{via_serie}"',
            )
            fig_via.update_layout(xaxis_tickangle=-45, height=360)
            st.plotly_chart(apply_template(fig_via), use_container_width=True)
    else:
        st.info("Digite o nome de uma via acima para ver sua evolução ao longo do tempo.")

# ── Tab 3: Estatísticas anuais ────────────────────────────────────────────────
with tabs[3]:
    st.plotly_chart(chart_anual(df), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_sazonalidade(df), use_container_width=True)

    with c2:
        # tabela resumo anual
        resumo_anual = df.groupby("Ano").agg(
            VMD_medio=("VMD", lambda x: int(x.mean())),
            VMD_max=("VMD", "max"),
            VMD_min=("VMD", "min"),
            Registros=("VMD", "count"),
            Vias=("ViaSentido", "nunique"),
        ).reset_index()
        resumo_anual["Var_%"] = resumo_anual["VMD_medio"].pct_change().mul(100).round(1)
        st.subheader("Resumo por ano")
        st.dataframe(
            resumo_anual,
            use_container_width=True,
            height=340,
            column_config={
                "VMD_medio": st.column_config.NumberColumn("VMD médio", format="%d"),
                "VMD_max":   st.column_config.NumberColumn("VMD máx",   format="%d"),
                "VMD_min":   st.column_config.NumberColumn("VMD mín",   format="%d"),
                "Var_%":     st.column_config.NumberColumn("Var. %",    format="%.1f%%"),
            },
        )

# ── Tab 4: Por bairro ──────────────────────────────────────────────────────────
with tabs[4]:
    df_bairro = filt[filt["Bairro"].notna()]

    st.plotly_chart(chart_bairros(df_bairro), use_container_width=True)

    st.divider()
    # tabela bairro × ano (se houver múltiplos anos)
    if df_bairro["Ano"].nunique() > 1:
        pivot_bairro = (
            df_bairro[df_bairro["Bairro"] != "Não identificado"]
            .groupby(["Bairro", "Ano"])["VMD"]
            .mean().round().astype(int)
            .unstack("Ano")
            .fillna(0)
            .astype(int)
        )
        st.subheader("VMD médio por bairro × ano")
        st.dataframe(pivot_bairro, use_container_width=True, height=360)

# ── Tab 5: Comparar períodos ──────────────────────────────────────────────────
with tabs[5]:
    if p1 == p2:
        st.warning("Selecione dois períodos diferentes na sidebar.")
    else:
        comp = compare_periods(df, p1, p2)
        if comp.empty:
            st.warning("Nenhuma via em comum entre os dois períodos.")
        else:
            # métricas rápidas
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Vias comparadas", len(comp))
            mc2.metric("VMD médio — " + p1, f"{int(comp['VMD_P1'].mean()):,}")
            mc3.metric("VMD médio — " + p2, f"{int(comp['VMD_P2'].mean()):,}",
                       delta=f"{((comp['VMD_P2'].mean()-comp['VMD_P1'].mean())/comp['VMD_P1'].mean()*100):+.1f}%")
            mc4.metric("Vias com queda", int((comp["Variacao"] < 0).sum()))

            st.write("")
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(chart_comparacao(comp, p1, p2), use_container_width=True)
            with col_b:
                st.plotly_chart(chart_scatter_comp(comp, p1, p2), use_container_width=True)

            st.divider()
            st.subheader("Tabela detalhada")
            st.dataframe(
                comp.rename(columns={"VMD_P1": f"VMD {p1}", "VMD_P2": f"VMD {p2}", "Variacao": "Var. %"}),
                use_container_width=True,
                height=380,
                column_config={
                    f"VMD {p1}": st.column_config.NumberColumn(format="%d"),
                    f"VMD {p2}": st.column_config.NumberColumn(format="%d"),
                    "Var. %":    st.column_config.NumberColumn(format="%.1f%%"),
                },
            )

# ── Tab 6: Anomalias ──────────────────────────────────────────────────────────
with tabs[6]:
    anomalias = detect_anomalies(filt if len(filt) > 50 else df, threshold=z_thresh)

    if anomalias.empty:
        st.success("Nenhuma anomalia detectada com os filtros atuais.")
    else:
        a1, a2, a3 = st.columns(3)
        a1.metric("Anomalias encontradas", len(anomalias))
        a2.metric("Z-score máximo", f"{anomalias['Z'].max():.2f}")
        a3.metric("Vias afetadas", anomalias["ViaSentido"].nunique())

        st.write("")
        # cards das top anomalias
        st.subheader("Top anomalias")
        for _, row in anomalias.head(5).iterrows():
            desvio = row.get("DesvioPerc", 0)
            sinal = "📈" if desvio > 0 else "📉"
            st.markdown(f"""
            <div class="anomaly-card">
              <span class="badge badge-anomalia">Z = {row['Z']:.2f}</span>
              &nbsp; <strong>{row['ViaSentido']}</strong> &nbsp;·&nbsp; {row['Data']}
              &nbsp;&nbsp; {sinal} VMD: <strong>{int(row['VMD']):,}</strong>
              &nbsp;·&nbsp; {desvio:+.1f}% vs média da via
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.plotly_chart(chart_anomalias(anomalias), use_container_width=True)

        st.subheader("Todos os registros anômalos")
        st.dataframe(
            anomalias[["Data","ViaSentido","VMD","Z","Bairro"]].round({"Z": 2}),
            use_container_width=True,
            height=360,
            column_config={
                "VMD": st.column_config.NumberColumn(format="%d"),
                "Z":   st.column_config.NumberColumn("Z-score", format="%.2f"),
            },
        )

# ── Tab 7: Mapa ───────────────────────────────────────────────────────────────
with tabs[7]:
    fig_mapa = chart_mapa(filt)
    if fig_mapa is None:
        st.warning("Nenhum ponto com coordenadas válidas nos filtros atuais.")
    else:
        geo_count = len(filt.dropna(subset=["Lat","Lon"]))
        st.caption(f"{geo_count:,} pontos mapeados")
        st.plotly_chart(fig_mapa, use_container_width=True)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;font-size:12px;color:#8892a4'>"
    "Dados: <a href='https://dados.fortaleza.ce.gov.br' style='color:#457b9d'>Portal de Dados Abertos — Prefeitura de Fortaleza</a>"
    " &nbsp;·&nbsp; Cache renovado a cada 24h"
    "</p>",
    unsafe_allow_html=True,
)
