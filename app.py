import streamlit as st
import pandas as pd

st.set_page_config(page_title="Engenharia de Tráfego - Fortaleza", layout="wide")

st.title("🚦 Dashboard de Tráfego (VMD) - Fortaleza")

URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_dados():
    # Carrega os dados
    df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
    df.columns = [c.strip() for c in df.columns]
    
    # LIMPEZA PESADA: 
    # 1. Converte para string, troca vírgula por ponto, remove espaços
    # 2. Transforma em número. Se falhar, vira NaN.
    # 3. Preenche NaNs com 0 (para não quebrar o gráfico)
    for col in ['VMD', 'Lon', 'Lat']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

try:
    df = carregar_dados()

    # Filtro de Busca
    busca = st.text_input("🔍 Pesquisar por Via:", "")
    if busca:
        df_exibir = df[df['ViaSentido'].str.contains(busca, case=False, na=False)].copy()
    else:
        df_exibir = df.copy()

    # --- INDICADORES ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros Encontrados", len(df_exibir))
    
    # Só calcula média se houver valores maiores que zero
    vmd_valido = df_exibir[df_exibir['VMD'] > 0]['VMD']
    if not vmd_valido.empty:
        c2.metric("VMD Médio", f"{vmd_valido.mean():.0f}")
        c3.metric("Maior VMD", f"{vmd_valido.max():.0f}")

    # --- ABAS ---
    tab1, tab2 = st.tabs(["📊 Dados e Gráficos", "🗺️ Mapa Geográfico"])

    with tab1:
        st.subheader("Tabela de Dados")
        st.dataframe(df_exibir, use_container_width=True)
        
        # Só tenta desenhar o gráfico se houver dados numéricos reais
        if not vmd_valido.empty:
            st.subheader("Top 20 Vias por Volume")
            # Ordenamos para garantir que o gráfico não receba valores infinitos
            graf_df = df_exibir.sort_values('VMD', ascending=False).head(20)
            # Usando st.bar_chart mas garantindo que o X e Y existam
            st.bar_chart(data=graf_df, x='ViaSentido', y='VMD')

    with tab2:
        st.subheader("Localização dos Sensores")
        # Filtrando apenas quem tem coordenadas reais (diferentes de 0)
        mapa_df = df_exibir[(df_exibir['Lat'] != 0) & (df_exibir['Lon'] != 0)].copy()
        
        if not mapa_df.empty:
            mapa_df = mapa_df[['Lat', 'Lon']]
            mapa_df.columns = ['lat', 'lon']
            st.map(mapa_df)
        else:
            st.info("Nenhuma coordenada válida encontrada para este filtro.")

except Exception as e:
    st.error(f"Erro Crítico: {e}")
