"""
data.py — carregamento, limpeza e enriquecimento dos dados VMD Fortaleza
"""

import io
import httpx
import numpy as np
import pandas as pd
import streamlit as st

CSV_URL = (
    "https://dados.fortaleza.ce.gov.br/dataset/"
    "94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/"
    "fcccc36d-50ee-488a-a814-e7e7e27f9872/download/"
    "dadosabertos_volumetrafegomensal.csv"
)

# ── Mapeamento aproximado de bairros por bbox de coordenadas ─────────────────
# (lon_min, lon_max, lat_min, lat_max) → bairro
BAIRROS = [
    ("Centro",           -38.545, -38.510, -3.740, -3.710),
    ("Meireles",         -38.510, -38.480, -3.730, -3.710),
    ("Aldeota",          -38.510, -38.480, -3.750, -3.730),
    ("Cocó",             -38.490, -38.460, -3.760, -3.730),
    ("Água Fria",        -38.560, -38.530, -3.790, -3.760),
    ("Messejana",        -38.510, -38.470, -3.820, -3.790),
    ("Parangaba",        -38.570, -38.540, -3.780, -3.750),
    ("Barra do Ceará",   -38.600, -38.565, -3.720, -3.690),
    ("Mondubim",         -38.600, -38.565, -3.800, -3.770),
    ("Maraponga",        -38.590, -38.560, -3.790, -3.760),
    ("Conjunto Ceará",   -38.630, -38.600, -3.800, -3.770),
    ("Jangurussu",       -38.520, -38.490, -3.840, -3.810),
    ("Passaré",          -38.540, -38.510, -3.830, -3.800),
    ("Aeroporto",        -38.545, -38.515, -3.785, -3.755),
    ("Praia de Iracema", -38.530, -38.505, -3.725, -3.705),
    ("Varjota",          -38.500, -38.475, -3.740, -3.720),
    ("Fátima",           -38.545, -38.520, -3.760, -3.740),
    ("Joaquim Távora",   -38.525, -38.500, -3.760, -3.740),
    ("Benfica",          -38.550, -38.525, -3.745, -3.725),
    ("Damas",            -38.555, -38.530, -3.765, -3.745),
]


def assign_bairro(lon: float, lat: float) -> str:
    if pd.isna(lon) or pd.isna(lat):
        return "Não identificado"
    for nome, lon_min, lon_max, lat_min, lat_max in BAIRROS:
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return nome
    return "Outros"


@st.cache_data(show_spinner="⏳ Baixando dados da Prefeitura de Fortaleza…", ttl=86_400)
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
        if "sitio" in cl or "sítio" in cl: rename[c] = "Sitio"
        elif cl == "data":                  rename[c] = "Data"
        elif "viasentido" in cl:           rename[c] = "ViaSentido"
        elif cl == "vmd":                  rename[c] = "VMD"
        elif "lon" in cl:                  rename[c] = "Lon"
        elif "lat" in cl:                  rename[c] = "Lat"
    df = df.rename(columns=rename)

    df["VMD"] = pd.to_numeric(df["VMD"], errors="coerce")
    df = df.dropna(subset=["VMD"])
    df["VMD"] = df["VMD"].astype(int)
    df["Data"] = df["Data"].astype(str).str.strip()
    df["Lon"] = pd.to_numeric(df.get("Lon", pd.Series(dtype=float)), errors="coerce")
    df["Lat"] = pd.to_numeric(df.get("Lat", pd.Series(dtype=float)), errors="coerce")

    # campos derivados
    df["Ano"]  = df["Data"].str[:4]
    df["Mes"]  = df["Data"].str[5:7]
    df["Bairro"] = df.apply(lambda r: assign_bairro(r["Lon"], r["Lat"]), axis=1)
    df["Intensidade"] = pd.cut(
        df["VMD"],
        bins=[0, 8_000, 20_000, 10_000_000],
        labels=["Baixo", "Médio", "Alto"],
    )

    return df.sort_values("Data").reset_index(drop=True)


# ── Detecção de anomalias (Z-score por via) ──────────────────────────────────
def detect_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> pd.DataFrame:
    """Retorna registros com Z-score > threshold dentro de cada via."""
    df = df.copy()
    df["Z"] = df.groupby("ViaSentido")["VMD"].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
    )
    df["Z"] = df["Z"].fillna(0).abs()
    anomalias = df[df["Z"] >= threshold].copy()
    anomalias["DesvioPerc"] = (
        df.groupby("ViaSentido")["VMD"].transform(lambda x: (x - x.mean()) / x.mean() * 100)
    ).reindex(anomalias.index)
    return anomalias.sort_values("Z", ascending=False)


# ── Variação mês a mês por via ───────────────────────────────────────────────
def mom_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna variação percentual mês a mês agregada por Data."""
    serie = (
        df.groupby("Data")["VMD"]
        .mean()
        .reset_index()
        .sort_values("Data")
    )
    serie["VarPerc"] = serie["VMD"].pct_change() * 100
    return serie


# ── Comparação entre dois períodos ───────────────────────────────────────────
def compare_periods(df: pd.DataFrame, p1: str, p2: str) -> pd.DataFrame:
    d1 = df[df["Data"] == p1].groupby("ViaSentido")["VMD"].mean().rename("VMD_P1")
    d2 = df[df["Data"] == p2].groupby("ViaSentido")["VMD"].mean().rename("VMD_P2")
    comp = pd.concat([d1, d2], axis=1).dropna()
    comp["Variacao"] = ((comp["VMD_P2"] - comp["VMD_P1"]) / comp["VMD_P1"] * 100).round(1)
    comp["VMD_P1"] = comp["VMD_P1"].round().astype(int)
    comp["VMD_P2"] = comp["VMD_P2"].round().astype(int)
    comp = comp.reset_index().sort_values("Variacao", ascending=False)
    return comp
