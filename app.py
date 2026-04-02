import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Tráfego - Fortaleza", layout="wide")

st.title("📊 Extração de Dados de Tráfego (AMC)")
st.markdown("Esta ferramenta acessa o Portal de Dados abertos da Prefeitura para analisar o volume veicular.")

# Link do CSV (Volume de Tráfego 2023 - Portal de Dados Abertos)
URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

# Função para carregar os dados (com cache para ficar rápido)
@st.cache_data
def carregar_dados():
    # Lendo o CSV da prefeitura
    df = pd.read_csv(URL_CSV, sep=";", encoding="utf-8")
    # Limpando nomes de colunas (removendo espaços extras se houver)
    df.columns = df.columns.str.strip()
    return df

try:
    with st.spinner('Acessando base de dados da Prefeitura...'):
        dados = carregar_dados()

    # --- INTERFACE DE FILTROS ---
    st.sidebar.header("Filtros de Pesquisa")
    
    # Filtro por nome da rua/logradouro
    busca_rua = st.sidebar.text_input("Digite o nome da via (ex: Washington Soares):")
    
    # Aplicando o filtro se o usuário digitar algo
    if busca_rua:
        dados_exibir = dados[dados['local'].str.contains(busca_rua, case=False, na=False)]
    else:
        dados_exibir = dados.head(100) # Mostra os primeiros 100 por padrão

    # --- EXIBIÇÃO DOS RESULTADOS ---
    col1, col2 = st.columns(2)
    col1.metric("Registros Encontrados", len(dados_exibir))
    
    st.subheader("Tabela de Dados")
    st.dataframe(dados_exibir, use_container_width=True)

    # Exemplo de gráfico se houver dados numéricos de volume
    if not dados_exibir.empty and 'volume' in dados_exibir.columns:
        st.subheader("Volume por Ponto de Coleta")
        st.bar_chart(data=dados_exibir, x='local', y='volume')

except Exception as e:
    st.error(f"Erro ao conectar com o site da prefeitura: {e}")
