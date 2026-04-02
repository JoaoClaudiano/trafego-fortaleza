# 🚦 VMD Fortaleza — Dashboard v2

Dashboard analítico para explorar os dados de **Volume Médio Diário (VMD) de Tráfego**
da Prefeitura de Fortaleza, com foco em análise temporal, espacial e detecção de anomalias.

## Funcionalidades

| Aba | Descrição |
|---|---|
| 📋 Dados | Tabela filtrável com download CSV |
| 📊 Ranking de vias | Top N vias + heatmap temporal |
| 📈 Série temporal | Evolução mensal + variação m/m + média móvel |
| 📆 Estatísticas anuais | Evolução anual, sazonalidade, boxplot por mês |
| 🏘️ Por bairro | Agregação por bairro + pivot bairro × ano |
| 🔀 Comparar períodos | Variação entre dois meses, scatter plot |
| ⚠️ Anomalias | Detecção por Z-score, cards de alertas, ranking |
| 🗺️ Mapa | Distribuição geográfica com intensidade de cores |

## Rodando localmente

```bash
git clone https://github.com/SEU_USUARIO/vmd-fortaleza.git
cd vmd-fortaleza

python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
streamlit run app.py
```

Acesse → **http://localhost:8501**

## Deploy no Streamlit Community Cloud (gratuito)

1. Suba o repositório no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. **New app** → selecione o repo → `app.py`
4. **Deploy** ✓

## Estrutura

```
vmd-fortaleza/
├── app.py          # Layout e UI (Streamlit)
├── data.py         # Carregamento, limpeza e análises
├── charts.py       # Todos os gráficos (Plotly)
├── requirements.txt
└── README.md
```

## Metodologia — Detecção de Anomalias

Calculado o Z-score de cada registro dentro da série histórica da mesma via:

```
Z = |VMD - média_via| / desvio_padrão_via
```

Registros com Z ≥ 2.5 (configurável na sidebar) são marcados como anômalos.

## Fonte

Portal de Dados Abertos — Prefeitura de Fortaleza  
https://dados.fortaleza.ce.gov.br
