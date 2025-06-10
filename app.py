import streamlit as st
import pandas as pd

st.title("🔧 Análise de Montagem com Algoritmo Greedy (dados do GitHub)")

# URLs dos arquivos no GitHub
url_estoque = "https://github.com/CamilaG288/IA/raw/refs/heads/main/ESTOQUE_DISPONIVEL.xlsx"
url_estrutura = "https://github.com/CamilaG288/IA/raw/refs/heads/main/ESTRUTURA.xlsx"
url_curva = "https://github.com/CamilaG288/IA/raw/refs/heads/main/CURVA%20ABC.xlsx"

# Carregar planilhas direto do GitHub
estoque_df = pd.read_excel(url_estoque)
estrutura_df = pd.read_excel(url_estrutura)
curva_df = pd.read_excel(url_curva)

# Limpar e padronizar colunas
estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
curva_df = curva_df[['PRODUTO', 'CURVA', 'PRIORIDADE']]

# Padronização de tipos
estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

# Estoque atual em dicionário
estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

# Juntar estrutura com curva ABC para saber prioridade
estrutura_com_prioridade = estrutura_df.merge(curva_df, on='PRODUTO', how='left')

# Ordenar produtos pela PRIORIDADE (menor número = mais prioritário)
produtos_ordenados = estrutura_com_prioridade[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

# Aplicar algoritmo greedy
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

    # Atualiza estoque caso vá montar
    if qtd_montar > 0:
        for _, comp in estrutura_prod.iterrows():
            componente = comp['COMPONENTE']
            qtd_necessaria = comp['QUANTIDADE']
            estoque_atual[componente] = estoque_atual.get(componente, 0) - qtd_necessaria * qtd_montar

    curva = estrutura_prod['CURVA'].iloc[0]
    prioridade = estrutura_prod['PRIORIDADE'].iloc[0]
    resultados.append({
        'PRODUTO': produto,
        'QUANTIDADE_MONTADA': qtd_montar,
        'CURVA': curva,
        'PRIORIDADE': prioridade
    })

# Exibir resultados
resultado_df = pd.DataFrame(resultados)
st.subheader("📋 Resultado da Montagem (com estoque consumido)")
st.dataframe(resultado_df.sort_values(by='QUANTIDADE_MONTADA', ascending=False))
