import streamlit as st
import pandas as pd

st.set_page_config(page_title="Montagem de Produtos", layout="wide")
st.title("🔧 Análise de Montagem com Estoque Real (Algoritmo Greedy)")

# 🔗 URLs corrigidas (sem acento no nome do arquivo)
url_estoque = "https://github.com/CamilaG288/IA/raw/main/ESTOQUE_DISPONIVEL.xlsx"
url_estrutura = "https://github.com/CamilaG288/IA/raw/main/ESTRUTURA.xlsx"
url_curva = "https://github.com/CamilaG288/IA/raw/main/CURVA%20ABC.xlsx"

# 📥 Leitura dos arquivos Excel direto do GitHub
estoque_df = pd.read_excel(url_estoque)
estrutura_df = pd.read_excel(url_estrutura)
curva_df = pd.read_excel(url_curva)

# 🔧 Limpeza e padronização de colunas
estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
curva_df = curva_df[['PRODUTO', 'CURVA', 'PRIORIDADE']]

estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

# 📦 Estoque atual
estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

# 🔄 Combinar estrutura com curva ABC
estrutura_com_prioridade = estrutura_df.merge(curva_df, on='PRODUTO', how='left')
produtos_ordenados = estrutura_com_prioridade[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

# 🤖 Aplicar algoritmo greedy
resultados = []

for _, linha in produtos_ordenados.iterrows():
    produto = linha['PRODUTO']
    estrutura_prod = estrutura_com_prioridade[estrutura_com_prioridade['PRODUTO'] == produto]

    min_montar = float('inf')
    for _, comp in estrutura_prod.iterrows():
        componente = comp['COMPONENTE']
        qtd_necessaria = comp['QUANTIDADE']
        qtd_disponivel = estoque_atual.get(componente, 0)

        if qtd_necessaria == 0:
            continue
        montar = qtd_disponivel // qtd_necessaria
        min_montar = min(min_montar, montar)

    qtd_montar = int(min_montar) if min_montar != float('inf') else 0

    # Atualizar estoque
    if qtd_montar > 0:
        for _, comp in estrutura_prod.iterrows():
            componente = comp['COMPONENTE']
            qtd_necessaria = comp['QUANTIDADE']
            estoque_atual[componente] -= qtd_necessaria * qtd_montar

    curva = estrutura_prod['CURVA'].iloc[0]
    prioridade = estrutura_prod['PRIORIDADE'].iloc[0]
    resultados.append({
        'PRODUTO': produto,
        'QUANTIDADE_MONTADA': qtd_montar,
        'CURVA': curva,
        'PRIORIDADE': prioridade
    })

# 📊 Mostrar resultado
resultado_df = pd.DataFrame(resultados)
st.subheader("📋 Produtos que podem ser montados com estoque atual")
st.dataframe(resultado_df.sort_values(by='QUANTIDADE_MONTADA', ascending=False), use_container_width=True)
