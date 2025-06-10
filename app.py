import streamlit as st
import pandas as pd

st.title("🔧 Análise de Montagem com Estoque Real (Algoritmo Greedy)")

# Uploads
estoque_file = st.file_uploader("📦 Upload da planilha ESTOQUE_DISPONIVEL", type=["xlsx", "xls"])
estrutura_file = st.file_uploader("🧩 Upload da planilha ESTRUTURA", type=["xlsx", "xls"])
curva_file = st.file_uploader("📊 Upload da planilha CURVA ABC", type=["xlsx", "xls"])

if estoque_file and estrutura_file and curva_file:
    # Leitura dos arquivos
    estoque_df = pd.read_excel(estoque_file)
    estrutura_df = pd.read_excel(estrutura_file)
    curva_df = pd.read_excel(curva_file)

    # Limpeza e padronização
    estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
    estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
    curva_df = curva_df[['PRODUTO', 'CURVA', 'PRIORIDADE']]

    # Padronizar tipos
    estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
    estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
    estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
    curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

    # Estoque total disponível por componente
    estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

    # Juntar estrutura com curva ABC (para saber prioridade)
    estrutura_com_prioridade = estrutura_df.merge(curva_df, on='PRODUTO', how='left')

    # Ordenar produtos pela prioridade crescente (menor número = mais prioritário)
    produtos_ordenados = estrutura_com_prioridade[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
    produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

    # Inicializar resultado
    resultados = []

    for _, linha in produtos_ordenados.iterrows():
        produto = linha['PRODUTO']
        estrutura_prod = estrutura_com_prioridade[estrutura_com_prioridade['PRODUTO'] == produto]

        # Calcular quantas unidades podem ser montadas com o estoque atual
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

        # Atualiza o estoque
        if qtd_montar > 0:
            for _, comp in estrutura_prod.iterrows():
                componente = comp['COMPONENTE']
                qtd_necessaria = comp['QUANTIDADE']
                estoque_atual[componente] = estoque_atual.get(componente, 0) - qtd_necessaria * qtd_montar

        # Armazena resultado
        curva = estrutura_prod['CURVA'].iloc[0]
        prioridade = estrutura_prod['PRIORIDADE'].iloc[0]
        resultados.append({
            'PRODUTO': produto,
            'QUANTIDADE_MONTADA': qtd_montar,
            'CURVA': curva,
            'PRIORIDADE': prioridade
        })

    resultado_df = pd.DataFrame(resultados)

    # Filtro
    curva_sel = st.multiselect("Filtrar por CURVA", options=['A', 'B', 'C'], default=['A', 'B', 'C'])
    resultado_df = resultado_df[resultado_df['CURVA'].isin(curva_sel)]

    # Mostrar resultado
    st.subheader("📋 Resultado da Montagem (com estoque consumido)")
    st.dataframe(resultado_df.sort_values(by='QUANTIDADE_MONTADA', ascending=False))

else:
    st.info("⬆️ Envie as três planilhas para iniciar.")
