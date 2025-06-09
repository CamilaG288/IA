import streamlit as st
import pandas as pd
import io

# Carregamento dos dados
curva_df = pd.read_excel("CURVA ABC.xlsx", header=0)
curva_df.columns = curva_df.columns.str.strip()

estrutura_df = pd.read_excel("ESTRUTURA.xlsx")
estoque_df = pd.read_excel("ESTOQUE_ALMOX102.xlsx")
origem_df = pd.read_excel("COMPONENTES_ORIGEM.xlsx")
ordens_abertas_df = pd.read_excel("ORDENS_COMPRA_PRODUCAO_ABERTA.xlsx")
pedidos_abertos_df = pd.read_excel("PEDIDOS_ABERTO.xlsx")
estrutura_pedidos_abertos_df = pd.read_excel("ESTRUTURA_PEDIDOS_ABERTOS.xlsx")

st.set_page_config(layout="wide")

st.title("Painel de Planejamento Montagem de Turbocompressores X Estoque")

# Remover pontos dos códigos
for df in [curva_df, estrutura_df, estoque_df, origem_df, ordens_abertas_df, pedidos_abertos_df, estrutura_pedidos_abertos_df]:
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(".", "", regex=False)

# Função para formatar números com ponto de milhar
def format_number(x):
    if isinstance(x, (int, float)):
        return f"{x:,.0f}".replace(",", ".")
    return x

# Informação adicional
st.caption("*As quantidades possíveis já consideram o desconto dos componentes reservados para pedidos em carteira.")

# Reservar componentes para atender pedidos em carteira
reservas_componentes = estrutura_pedidos_abertos_df.copy()
reservas_componentes = reservas_componentes.merge(pedidos_abertos_df[['PRODUTO', 'QUANTIDADE PRODUZIR']], on='PRODUTO', how='left')
reservas_componentes['Reserva Total'] = reservas_componentes['QUANTIDADE'] * reservas_componentes['QUANTIDADE PRODUZIR']
reservas_estoque = reservas_componentes.groupby('COMPONENTE')['Reserva Total'].sum().reset_index()

# Atualizar estoque
estoque_df['Estoque Disponivel'] = estoque_df['QUANTIDADE']
estoque_atual_df = estoque_df.merge(reservas_estoque, on='COMPONENTE', how='left')
estoque_atual_df['Reserva Total'] = estoque_atual_df['Reserva Total'].fillna(0)
estoque_atual_df['Estoque Disponivel'] -= estoque_atual_df['Reserva Total']
estoque_atual_df['Estoque Disponivel'] = estoque_atual_df['Estoque Disponivel'].clip(lower=0)

# Preparar estrutura
curva_df['PRIORIDADE'] = curva_df['PRIORIDADE'].astype(int)
curva_ordenada = curva_df.sort_values('PRIORIDADE')
qtd_carteira = pedidos_abertos_df.groupby('PRODUTO')['QUANTIDADE PRODUZIR'].sum().reset_index().rename(columns={'QUANTIDADE PRODUZIR': 'Quantidade em Carteira'})

produtos_possiveis = []
estoque_montagem_df = estoque_atual_df.copy()

for _, row in curva_ordenada.iterrows():
    produto = row['PRODUTO']
    estrutura_item = estrutura_df[estrutura_df['PRODUTO'] == produto]

    if estrutura_item.empty:
        continue

    estrutura_item = estrutura_item.merge(estoque_montagem_df[['COMPONENTE', 'Estoque Disponivel']], on='COMPONENTE', how='left')
    estrutura_item['Estoque Disponivel'] = estrutura_item['Estoque Disponivel'].fillna(0)

    if estrutura_item['QUANTIDADE'].isnull().any():
        continue

    estrutura_item['Qtd Possivel'] = estrutura_item['Estoque Disponivel'] / estrutura_item['QUANTIDADE']
    unidades_possiveis = int(estrutura_item['Qtd Possivel'].min())

    if unidades_possiveis > 0:
        carteira = qtd_carteira[qtd_carteira['PRODUTO'] == produto]['Quantidade em Carteira'].sum()
        produtos_possiveis.append({
            'Produto': produto,
            'Descricao Produto': row['DESCRICAO PRODUTO'],
            'Curva': row['CURVA'],
            'Unidades Possíveis': unidades_possiveis,
            'Quantidade em Carteira': int(carteira),
            'Grupo Planejador': row['DESCRICAO GRUPO PLANEJADOR']
        })

        for idx, comp_row in estrutura_item.iterrows():
            componente = comp_row['COMPONENTE']
            quantidade_necessaria = comp_row['QUANTIDADE'] * unidades_possiveis
            estoque_montagem_df.loc[estoque_montagem_df['COMPONENTE'] == componente, 'Estoque Disponivel'] -= quantidade_necessaria
            estoque_montagem_df['Estoque Disponivel'] = estoque_montagem_df['Estoque Disponivel'].clip(lower=0)

# Exibir resultado
st.subheader("Lista de Turbocompressores com Montagem Possível (Estoque Atual)")

if produtos_possiveis:
    df_possiveis = pd.DataFrame(produtos_possiveis)
    df_possiveis.index = df_possiveis.index + 1

    st.dataframe(df_possiveis.reset_index().applymap(format_number))

    total_montagem = df_possiveis['Unidades Possíveis'].sum()
    total_carteira = df_possiveis['Quantidade em Carteira'].sum()
    total_produtos = len(df_possiveis)

    col1, col2, col3 = st.columns(3)

    col1.metric("Quantidade Total de Produtos", format_number(total_produtos))
    col2.metric("Unidades Possíveis para Montagem", format_number(total_montagem))
    col3.metric("Valor Total na Carteira", format_number(total_carteira))

    # Botão para baixar
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_possiveis.to_excel(writer, index=False)
    processed_data = output.getvalue()

    st.download_button(
        label="Baixar Lista de Montagem Possível em Excel",
        data=processed_data,
        file_name='montagem_possivel.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='download_montagem'
    )

# Consulta de quantidade possível por produto
st.subheader("Consulta de Quantidade Possível por Produto")
codigo_busca = st.text_input('Digite o código do produto (ex: 805335-01):')

if codigo_busca:
    resultado = df_possiveis[df_possiveis['Produto'] == codigo_busca]
    if not resultado.empty:
        unidades_possiveis = resultado['Unidades Possíveis'].values[0]
        st.success(f"Quantidade possível de montagem para o produto {codigo_busca}: {format_number(unidades_possiveis)} unidades")
    else:
        st.warning(f"Produto {codigo_busca} não encontrado ou não possui unidades possíveis para montagem.")
