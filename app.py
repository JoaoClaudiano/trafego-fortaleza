import streamlit as st
import pandas as pd

st.set_page_config(page_title="Engenharia de Tráfego - Fortaleza", layout="wide")

st.title("🚦 Monitor de Fluxo Veicular (AMC)")

# Link que você forneceu
URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_base():
    # Lendo o CSV. Como você viu que a coluna é 'ViaSentido', 
    # vamos manter o case original ou tratar depois.
    df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
    
    # Limpeza básica: remove espaços em branco dos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # Converter colunas numéricas (Volume, Lat, Long) se existirem
    # O 'errors=coerce' transforma o que não for número em NaN (vazio)
    cols_numericas = ['Volume', 'Latitude', 'Longitude', 'VolumeMedio']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    return df

try:
    df_completo = carregar_base()

    # Mapeando o nome da coluna de localização
    # Se 'ViaSentido' existe, usamos ela, senão pegamos a primeira coluna disponível
    col_via = 'ViaSentido' if 'ViaSentido' in df_completo.columns else df_completo.columns[0]

    # --- INDICADORES TIPO POWER BI ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Registros", f"{len(df_completo):,}")
    
    if 'Volume' in df_completo.columns:
        c2.metric("Média de Volume", f"{df_completo['Volume'].mean():.2f}")
        maior_fluxo = df_completo.loc[df_completo['Volume'].idxmax(), col_via]
        c3.metric("Ponto mais Movimentado", str(maior_fluxo)[:20] + "...")

    # --- BUSCA ---
    busca = st.text_input(f"🔍 Pesquisar na coluna {col_via} (ex: Santos Dumont):")

    if busca:
        # Filtro que ignora maiúsculas/minúsculas
        df_exibir = df_completo[df_completo[col_via].str.contains(busca, case=False, na=False)]
    else:
        df_exibir = df_completo

    # --- ABAS DE VISUALIZAÇÃO ---
    aba1, aba2 = st.tabs(["📊 Dados e Gráficos", "🗺️ Mapa Geoestatístico"])

    with aba1:
        st.subheader("Tabela de Dados Extraída")
        st.dataframe(df_exibir, use_container_width=True)
        
        if 'Volume' in df_exibir.columns:
            st.subheader("Gráfico de Volume por Ponto")
            # Mostrando os 40 maiores volumes do filtro atual
            top_40 = df_exibir.sort_values('Volume', ascending=False).head(40)
            st.bar_chart(data=top_40, x=col_via, y='Volume')

    with aba2:
        st.subheader("Visualização Espacial")
        # Para o mapa funcionar, o Streamlit precisa de colunas chamadas exatamente 'latitude' e 'longitude'
        if 'Latitude' in df_exibir.columns and 'Longitude' in df_exibir.columns:
            mapa_df = df_exibir[['Latitude', 'Longitude']].dropna()
            mapa_df.columns = ['lat', 'lon'] # Renomeando para o padrão do st.map
            st.map(mapa_df)
        else:
            st.info("As colunas de coordenadas não foram detectadas ou estão vazias.")

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
    st.write("Colunas detectadas no seu CSV:", list(df_completo.columns) if 'df_completo' in locals() else "Não carregou.")
