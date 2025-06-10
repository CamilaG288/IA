import streamlit as st
import pandas as pd

st.set_page_config(page_title="Montagem de Produtos", layout="wide")
st.title("🔧 Análise de Montagem com Estoque Real (Algoritmo Greedy)")

# 🔗 URLs dos arquivos Excel no GitHub (com acentos e espaços codificados)
url_estoque = "https://github.com/CamilaG288/IA/raw/main/ESTOQUE_DISPON%C3%8DVEL.xlsx"
url_estrutura = "https://github.com/CamilaG288/IA/raw/main/ESTRUTURA.xlsx"
url_curva = "https://github.com/CamilaG288/IA/raw/main/CURVA%20ABC.xlsx"

# 📥 Leitura dos arquivos diretamente do GitHub
estoque_df = pd.read_excel(url_estoque)
estrutura_df = pd.read_excel(url_estrutura)
curva_df = pd.read_excel(url_curva)

# 🔧 Limpeza e padronização
estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
curva_df = curva_df[['PRODUTO', 'CURVA', 'PRIORIDADE']]

estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

# 📦 Estoque atual em dicionário
estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

# 🔄 Juntar estrutura com prioridade
estrutura_com_prioridade = estrutura_df.merge(curva_df, on='PRODUTO', how='left')

# 📌 Ordenar produtos pela PRIORIDADE (menor = mais prioritário)
produtos_ordenados = estrutura_com_prioridade[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

# 🤖 Algoritmo Greedy
resultados = []

for _, linha in produtos_ordenados.iterrows():
    produto = linha['PRODUTO']
    estrutura_prod = estrutura_com_prioridade[estrutura_com_prioridade['PRODUTO'] == produto]

    min_montar = float('inf')
    for _, comp in estrutura_prod.iterr
