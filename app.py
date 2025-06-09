import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("Montagem de Turbocompressores - Estoque Disponível")

# Carregamento dos dados
estoque_df = pd.read_excel("ESTOQUE_DISPONIVEL.xlsx")
estrutura_df = pd.read_excel("ESTRUTURA.xlsx")

# Limpeza dos dados
estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.replace(".", "", regex=False).str.strip()

# Garantir tipos numéricos
estoque_df['QUANTIDADE'] = pd.to_numeric(estoque_df['QUANTIDADE'], errors='coerce').fillna(0)
estrutura_df['QUANTIDADE'] = pd.to_numeric(estrutura_df['QUANTIDADE'], errors='coerce').fillna(0)

# Estoque como dicionário para consulta rápida
estoque_dict = estoque_df.set_index('COMPONENTE')['QUANTIDADE'].to_dict()

# Lista para armazenar os produtos possíveis
produtos_possiveis = []

# Obter todos os produtos únicos na estrutura
produtos_unicos = estrutura_df['PRODUTO'].unique()

# Algoritmo greedy para calcular a quantidade possível de montagem
for produto in produtos_unicos:
    estrutura_item = estrutura_df[estrutura_df['PRODUTO'] == produto]

    min_montagem = float('inf')
    for _, row in estrutura_item.iterrows():
        componente = row['COMPONENTE']
        quantidade_necessaria = row['QUANTIDADE']
        estoque_disponivel = estoque_dict.get(componente, 0)

        if quantidade_necessaria == 0:
            continue

        unidades_possiveis = estoque_disponivel // quantidade_necessaria
        min_montagem = min(min_montagem, unidades_possiveis)

    if min_montagem > 0 and min_montagem != float('inf'):
        produtos_possiveis.append({
            'Produto': produto,
            'Unidades Possíveis': int(min_montagem)
        })

# Criar DataFrame de resultado
df_resultado = pd.DataFrame(produtos_possiveis)
df_resultado.index = df_resultado.index + 1

# Exibir resultado
st.subheader("Produtos Possíveis de Montar com Estoque Atual")
st.dataframe(df_resultado)

# Botão para download
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_resultado.to_excel(writer, index=False)
processed_data = output.getvalue()

st.download_button(
    label="Baixar Lista de Produtos Possíveis",
    data=processed_data,
    file_name='produtos_possiveis.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
