# 🚦 VMD Fortaleza

Dashboard interativo para explorar os dados de **Volume Médio Diário (VMD) de Tráfego** da Prefeitura de Fortaleza, publicados no Portal de Dados Abertos.

## Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## Funcionalidades

- **Tabela** — dados paginados e filtráveis, download em CSV
- **Top vias** — ranking das vias com maior volume de tráfego
- **Série temporal** — evolução do VMD de uma via ao longo dos meses
- **Mapa** — distribuição geográfica dos pontos de medição
- Cache automático de 24h para não sobrecarregar o servidor da prefeitura

## Rodando localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/vmd-fortaleza.git
cd vmd-fortaleza

# 2. Crie e ative um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o app
streamlit run app.py
```

Acesse em → **http://localhost:8501**

## Deploy no Streamlit Community Cloud (gratuito)

1. Suba o repositório no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **New app** → selecione o repositório → `app.py`
4. Clique em **Deploy** — pronto!

## Fonte dos dados

| Campo | Descrição |
|---|---|
| `Sitio` | Código do ponto de medição |
| `Data` | Período (formato `AAAA-MM`) |
| `ViaSentido` | Nome da via e sentido |
| `VMD` | Volume Médio Diário (veículos/dia) |
| `Lon` / `Lat` | Coordenadas do ponto |

**URL do dataset:**
```
https://dados.fortaleza.ce.gov.br/dataset/94e77a67-a8a5-4f54-a27c-f9f58c4fe176
```

## Licença

MIT — dados públicos da Prefeitura de Fortaleza.
