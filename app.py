import streamlit as st
import pandas as pd

# 1. Configuração inicial - Desativar temporariamente o mapa se o erro persistir
st.set_page_config(page_title="Engenharia de Tráfego UFC", layout="wide")

st.title("🚦 Monitor de Tráfego Fortaleza (AMC)")

URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_e_limpar():
    try:
        # Lendo o CSV com tratamento de erro de parsing
        df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
        df.columns = [c.strip() for c in df.columns]
        
        # Garantindo que VMD, Lat e Lon sejam numéricos e removendo sujeira
        for col in ['VMD', 'Lat', 'Lon']:
            if col in df.columns:
                # Remove qualquer caractere que não seja número, ponto, menos ou vírgula
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove linhas onde VMD ou Coordenadas são nulas para evitar erro de 'Infinity' no gráfico
        df = df.dropna(subset=['VMD', 'Lat', 'Lon'])
        return df
    except Exception as e:
        st.error(f"Erro na leitura do arquivo: {e}")
        return pd.DataFrame()

df = carregar_e_limpar()

if not df.empty:
    # --- BUSCA ---
    busca = st.text_input("🔍 Filtrar via (ex: Francisco Sa):", "")
    if busca:
        df_filtrado = df[df['ViaSentido'].str.contains(busca, case=False, na=False)].copy()
    else:
        df_filtrado = df.copy()

    # --- MÉTRICAS ---
    c1, c2 = st.columns(2)
    c1.metric("Registros", len(df_filtrado))
    c2.metric("VMD Médio", f"{df_filtrado['VMD'].mean():.0f}")

    # --- ABAS ---
    tab1, tab2 = st.tabs(["📊 Dados e Gráfico", "🗺️ Mapa Geográfico"])

    with tab1:
        st.subheader("Tabela de Dados")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfico simples apenas se houver dados
        if len(df_filtrado) > 0:
            st.subheader("Top 15 Volumes")
            top_15 = df_filtrado.sort_values('VMD', ascending=False).head(15)
            # Usando st.area_chart ou st.bar_chart
            st.bar_chart(data=top_15, x='ViaSentido', y='VMD')

    with tab2:
        st.subheader("Mapa de Sensores")
        # O erro de 'luma' geralmente acontece quando o st.map falha no navegador.
        # Vamos tentar filtrar coordenadas extremas (fora de Fortaleza)
        mapa_df = df_filtrado[(df_filtrado['Lat'] < 0) & (df_filtrado['Lon'] < 0)].copy()
        mapa_df = mapa_df[['Lat', 'Lon']].rename(columns={'Lat': 'lat', 'Lon': 'lon'})
        
        if not mapa_df.empty:
            try:
                st.map(mapa_df)
            except Exception as map_err:
                st.warning("O componente de mapa teve um problema técnico de renderização no seu navegador.")
                st.info("Tente recarregar a página ou usar outro navegador (Chrome/Edge).")
else:
    st.warning("Aguardando carregamento de dados da Prefeitura...")
