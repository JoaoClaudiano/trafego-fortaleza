"""
VMD Fortaleza — Dashboard Streamlit
Fonte: Portal de Dados Abertos da Prefeitura de Fortaleza
"""

import io
import httpx
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="VMD Fortaleza",
    page_icon="🚦",
    layout="wide",
)

CSV_URL = (
    "https://dados.fortaleza.ce.gov.br/dataset/"
    "94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/"
    "fcccc36d-50ee-488a-a814-e7e7e27f9872/download/"
    "dadosabertos_volumetrafegomensal.csv"
)

# ── Carregamento com cache ──────────────────────────────────────────────────
@st.cache_data(show_spinner="Baixando dados da Prefeitura de Fortaleza…", ttl=86400)
def load_data() -> pd.DataFrame:
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        r = client.get(CSV_URL)
        r.raise_for_status()

    df = pd.read_csv(
        io.BytesIO(r.content),
        sep=None,
        engine="python",
        encoding="utf-8",
        on_bad_lines="skip",
    )
    df.columns = [c.strip() for c in df.columns]

    rename = {}
    for c in df.columns:
        cl = c.lower().replace(" ", "")
        if "sitio" in cl or "sítio" in cl:  rename[c] = "Sitio"
        elif cl == "data":                   rename[c] = "Data"
        elif "viasentido" in cl:            rename[c] = "ViaSentido"
        elif cl == "vmd":                   rename[c] = "VMD"
        elif "lon" in cl:                   rename[c] = "Lon"
        elif "lat" in cl:                   rename[c] = "Lat"
    df = df.rename(columns=rename)

    df["VMD"] = pd.to_numeric(df["VMD"], errors="coerce")
    df = df.dropna(subset=["VMD"])
    df["VMD"] = df["VMD"].astype(int)
    df["Data"] = df["Data"].astype(str).str.strip()
    df["ViaSentido"] = df["ViaSentido"].astype(str).str.strip()
    df["Lon"] = pd.to_numeric(df.get("Lon", pd.Series(dtype=float)), errors="coerce")
    df["Lat"] = pd.to_numeric(df.get("Lat", pd.Series(dtype=float)), errors="coerce")
    return df


def intensidade(v: int) -> str:
    if v >= 20_000: return "🔴 Alto"
    if v >= 8_000:  return "🟡 Médio"
    return "🟢 Baixo"


# ── Layout ──────────────────────────────────────────────────────────────────
st.title("🚦 Volume Médio Diário de Tráfego — Fortaleza")
st.caption("Fonte: [Portal de Dados Abertos da Prefeitura de Fortaleza](https://dados.fortaleza.ce.gov.br)")

# carrega dados
try:
    df = load_data()
except Exception as e:
    st.error(f"Erro ao baixar os dados: {e}")
    st.stop()

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    periodos = sorted(df["Data"].unique())
    periodo_sel = st.selectbox("Período", ["Todos"] + periodos)

    via_busca = st.text_input("Filtrar por via", placeholder="Ex: BEIRA MAR")

    ordenar = st.selectbox(
        "Ordenar por",
        ["VMD (maior)", "VMD (menor)", "Via A–Z", "Data (recente)"],
    )

    st.divider()
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Total bruto: {len(df):,} registros")

# ── Filtragem ────────────────────────────────────────────────────────────────
filt = df.copy()
if periodo_sel != "Todos":
    filt = filt[filt["Data"] == periodo_sel]
if via_busca:
    filt = filt[filt["ViaSentido"].str.upper().str.contains(via_busca.upper(), na=False)]

sort_map = {
    "VMD (maior)":    ("VMD", False),
    "VMD (menor)":    ("VMD", True),
    "Via A–Z":        ("ViaSentido", True),
    "Data (recente)": ("Data", False),
}
col_sort, asc_sort = sort_map[ordenar]
filt = filt.sort_values(col_sort, ascending=asc_sort).reset_index(drop=True)

# ── Métricas ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros filtrados", f"{len(filt):,}")
c2.metric("VMD médio", f"{int(filt['VMD'].mean()):,}" if len(filt) else "—")
c3.metric("VMD máximo", f"{int(filt['VMD'].max()):,}" if len(filt) else "—")
c4.metric("Vias monitoradas", f"{filt['ViaSentido'].nunique():,}" if len(filt) else "—")

st.divider()

# ── Abas ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 Tabela", "📊 Top vias", "📈 Série temporal", "🗺️ Mapa"])

# ── Tab 1: Tabela ─────────────────────────────────────────────────────────────
with tab1:
    exibir = filt[["Data", "ViaSentido", "VMD", "Sitio"]].copy()
    exibir["Intensidade"] = exibir["VMD"].apply(intensidade)

    st.dataframe(
        exibir,
        use_container_width=True,
        height=480,
        column_config={
            "VMD": st.column_config.NumberColumn("VMD", format="%d"),
        },
    )

    csv_bytes = filt.to_csv(index=False).encode("utf-8")
    nome = f"vmd_fortaleza{'_'+periodo_sel if periodo_sel != 'Todos' else ''}.csv"
    st.download_button("⬇️ Baixar CSV filtrado", csv_bytes, nome, "text/csv")

# ── Tab 2: Top vias ────────────────────────────────────────────────────────────
with tab2:
    n_top = st.slider("Número de vias", 5, 50, 20)
    top = (
        filt.groupby("ViaSentido")["VMD"]
        .mean()
        .round()
        .astype(int)
        .sort_values(ascending=False)
        .head(n_top)
        .reset_index()
    )
    top["Intensidade"] = top["VMD"].apply(intensidade)
    color_map = {"🔴 Alto": "#dc2626", "🟡 Médio": "#d97706", "🟢 Baixo": "#059669"}

    fig = px.bar(
        top,
        x="VMD",
        y="ViaSentido",
        orientation="h",
        color="Intensidade",
        color_discrete_map=color_map,
        text="VMD",
        labels={"ViaSentido": "", "VMD": "VMD médio"},
        title=f"Top {n_top} vias por VMD médio" + (f" — {periodo_sel}" if periodo_sel != "Todos" else ""),
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(400, n_top * 28))
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: Série temporal ──────────────────────────────────────────────────────
with tab3:
    via_serie = st.text_input("Nome da via (parcial)", placeholder="Ex: AV. FRANCISCO SA", key="serie_via")

    if via_serie:
        sub = df[df["ViaSentido"].str.upper().str.contains(via_serie.upper(), na=False)]
        if sub.empty:
            st.warning("Nenhuma via encontrada com esse nome.")
        else:
            serie = (
                sub.groupby(["Data", "ViaSentido"])["VMD"]
                .mean()
                .round()
                .astype(int)
                .reset_index()
                .sort_values("Data")
            )
            fig2 = px.line(
                serie,
                x="Data",
                y="VMD",
                color="ViaSentido",
                markers=True,
                labels={"Data": "Período", "VMD": "VMD médio"},
                title=f"Série temporal — \"{via_serie}\"",
            )
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(serie, use_container_width=True, height=300)
    else:
        st.info("Digite o nome de uma via para ver sua evolução ao longo do tempo.")

# ── Tab 4: Mapa ────────────────────────────────────────────────────────────────
with tab4:
    geo = filt.dropna(subset=["Lat", "Lon"])
    geo = geo[geo["Lat"].between(-4.2, -3.5) & geo["Lon"].between(-39.0, -38.3)]

    if geo.empty:
        st.warning("Nenhum registro com coordenadas válidas para os filtros atuais.")
    else:
        st.caption(f"{len(geo):,} pontos com coordenadas válidas")
        fig3 = px.scatter_mapbox(
            geo,
            lat="Lat",
            lon="Lon",
            color="VMD",
            size="VMD",
            size_max=18,
            hover_name="ViaSentido",
            hover_data={"Data": True, "VMD": True, "Lat": False, "Lon": False},
            color_continuous_scale="RdYlGn_r",
            zoom=11,
            mapbox_style="carto-positron",
            title="Distribuição geográfica do VMD",
        )
        fig3.update_layout(height=560, margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig3, use_container_width=True)
