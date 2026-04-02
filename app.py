import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Tráfego AMC", layout="wide")

st.title("📊 Extração de Dados de Tráfego de Fortaleza")
st.markdown("Utilizando o link fixo do Portal de Dados Abertos da AMC.")

# O link que você encontrou (Link Fixo)
URL_CSV = "https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176/resource/fcccc36d-50ee-488a-a814-e7e7e27f9872/download/dadosabertos_volumetrafegomensal.csv"

@st.cache_data
def carregar_dados():
    # Adicionamos 'sep' e 'encoding' para evitar erros de leitura
    # O 'on_bad_lines' pula linhas que possam estar corrompidas no servidor
    df = pd.read_csv(URL_CSV, sep=",", encoding="latin1", on_bad_lines='skip')
    
    # Padronizando os nomes das colunas para minúsculo para facilitar a busca
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

try:
    with st.spinner('Lendo dados da AMC...'):
        dados = carregar_dados()

    # Filtros na Barra Lateral
    st.sidebar.header("Configurações")
    
    # Identificando as colunas disponíveis para busca (ajustado para o novo CSV)
    coluna_local = 'local' if 'local' in dados.columns else dados.columns[0]
    
    busca = st.sidebar.text_input(f"Pesquisar por via (ex: Santos Dumont):")

    if busca:
        dados_filtrados = dados[dados[coluna_local].str.contains(busca, case=False, na=False)]
    else:
        dados_filtrados = dados.head(50)

    # Exibição
    st.metric("Total de Registros no Filtro", len(dados_filtrados))
    st.dataframe(dados_filtrados, use_container_width=True)

except Exception as e:
    st.error(f"Ainda há um problema de conexão ou formato: {e}")
    st.info("Dica: Verifique se o link abre direto no seu navegador. Se abrir, o problema pode ser o 'separador' do CSV.")
