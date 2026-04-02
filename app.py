import streamlit as st
import pandas as pd

st.set_page_config(page_title="Engenharia de Tráfego - Fortaleza", layout="wide")

st.title("🚦 Dashboard de Tráfego (VMD) - Fortaleza")

# Link do CSV da Prefeitura
URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_dados():
    # Carrega os dados com o encoding correto para português
    df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
    
    # Limpa espaços vazios nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # Converte as colunas numéricas conforme a imagem (VMD, Lon, Lat)
    # Substituímos vírgula por ponto para o Python entender como número decimal
    for col in ['VMD', 'Lon', 'Lat']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    return df

try:
    df = carregar_dados()

    # --- INDICADORES (ESTILO POWER BI) ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Registros", len(df))
    
    if 'VMD' in df.columns:
        c2.metric("VMD Médio (Geral)", f"{df['VMD'].mean():.0f}")
        ponto_critico = df.loc[df['VMD'].idxmax(), 'ViaSentido']
        c3.metric("Maior Fluxo Detectado", f"{ponto_critico[:25]}...")

    # --- FILTRO ---
    busca = st.text_input("🔍 Pesquisar por Via (Ex: Francisco Sa ou Gen. Osorio):")
    if busca:
        df_exibir = df[df['ViaSentido'].str.contains(busca, case=False, na=False)]
    else:
        df_exibir = df

    # --- ABAS ---
    tab1, tab2 = st.tabs(["📊 Análise de Dados", "🗺️ Mapa de Calor (Geoestatística)"])

    with tab1:
        st.subheader("Tabela de Dados Filtrada")
        st.dataframe(df_exibir, use_container_width=True)
        
        if 'VMD' in df_exibir.columns:
            st.subheader("Ranking de Volume por Via")
            # Mostra as 30 vias com maior VMD no filtro atual
            top_vias = df_exibir.sort_values('VMD', ascending=False).head(30)
            st.bar_chart(data=top_vias, x='ViaSentido', y='VMD')

    with tab2:
        st.subheader("Distribuição Geográfica dos Sensores")
        # O Streamlit precisa que as colunas se chamem 'lat' e 'lon' (minúsculo)
        if 'Lat' in df_exibir.columns and 'Lon' in df_exibir.columns:
            mapa_df = df_exibir[['Lat', 'Lon']].dropna()
            mapa_df.columns = ['lat', 'lon'] # Renomeando para o padrão do mapa
            st.map(mapa_df)
        else:
            st.warning("Coordenadas (Lat/Lon) não encontradas ou inválidas.")

except Exception as e:
    st.error(f"Erro ao processar: {e}")
