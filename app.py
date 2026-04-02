import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Engenharia de Tráfego - UFC", layout="wide")

st.title("🚦 Dashboard de Mobilidade Urbana (AMC Fortaleza)")

URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_base_completa():
    # Lendo a base completa
    df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Tratamento de dados para Geoestatística (convertendo vírgula para ponto em lat/long)
    for col in ['latitude', 'longitude', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    
    return df.dropna(subset=['local']) # Remove linhas sem identificação de local

try:
    df_completo = carregar_base_completa()

    # --- ESTILO POWER BI (INDICADORES) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Registros", f"{len(df_completo):,}")
    
    if 'volume' in df_completo.columns:
        vmd_medio = df_completo['volume'].mean()
        col2.metric("Volume Médio (VMD)", f"{vmd_medio:.2f}")
        col3.metric("Ponto de Maior Fluxo", df_completo.loc[df_completo['volume'].idxmax(), 'local'])

    # --- FILTRO DINÂMICO ---
    busca = st.text_input("🔍 Filtrar via específica (ex: Bezerra de Menezes):")
    
    if busca:
        df_final = df_completo[df_completo['local'].str.contains(busca, case=False, na=False)]
    else:
        df_final = df_completo # AQUI AGORA PEGA TUDO!

    # --- VISUALIZAÇÃO DE DADOS ---
    tab1, tab2, tab3 = st.tabs(["📋 Tabela Completa", "🗺️ Mapa Geoestatístico", "📊 Gráficos de Análise"])

    with tab1:
        st.subheader("Dados Extraídos")
        st.dataframe(df_final, use_container_width=True)

    with tab2:
        st.subheader("Distribuição Espacial do Tráfego")
        # Se o CSV tiver lat/lon, o streamlit plota o mapa na hora
        if 'latitude' in df_final.columns and 'longitude' in df_final.columns:
            mapa_data = df_final[['latitude', 'longitude']].dropna()
            st.map(mapa_data)
        else:
            st.warning("Colunas de Latitude/Longitude não encontradas para gerar o mapa.")

    with tab3:
        st.subheader("Análise de Volume")
        if 'volume' in df_final.columns:
            st.bar_chart(data=df_final.head(30), x='local', y='volume')

except Exception as e:
    st.error(f"Erro ao processar base completa: {e}")
