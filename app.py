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
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.replace(".", "", regex=False)
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.replace(".", "", regex=False)
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False)
estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False)
origem_df['COMPONENTE'] = origem_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False)
ordens_abertas_df['COMPONENTE'] = ordens_abertas_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False)
pedidos_abertos_df['PRODUTO'] = pedidos_abertos_df['PRODUTO'].astype(str).str.replace(".", "", regex=False)
estrutura_pedidos_abertos_df['PRODUTO'] = estrutura_pedidos_abertos_df['PRODUTO'].astype(str).str.replace(".", "", regex=False)
estrutura_pedidos_abertos_df['COMPONENTE'] = estrutura_pedidos_abertos_df['COMPONENTE'].astype(str).str.replace(".", "", regex=False)

# Sidebar com seleção de item
item_select = st.selectbox("Selecione o Código do Item:", curva_df['PRODUTO'].astype(str).unique())

# Mostrar dados do item
item_info = curva_df[curva_df['PRODUTO'].astype(str) == item_select]

# Função para formatar números com ponto de milhar
def format_number(x):
    if isinstance(x, (int, float)):
        return f"{x:,.0f}".replace(",", ".")
    return x

# Informação adicional em letra menor
st.caption("*As quantidades possíveis já consideram o desconto dos componentes reservados para pedidos em carteira.")

# Nova seção: Lista de Turbos que podem ser montados com algoritmo Greedy
st.subheader("Lista de Turbocompressores com Montagem Possível (Estoque Atual) - Algoritmo Otimizado")

# Calcular estoque inicial disponível
estoque_atual_df = estoque_df.copy()
estoque_atual_df['Estoque Disponivel'] = estoque_atual_df['QUANTIDADE']

# Calcular quantidade em carteira por produto
qtd_carteira = pedidos_abertos_df.groupby('PRODUTO')['QUANTIDADE PRODUZIR'].sum().reset_index().rename(columns={'QUANTIDADE PRODUZIR': 'Quantidade em Carteira'})

# Lista final
produtos_possiveis = []

# Criar dicionário de reservas por produto
reservas_estoque = qtd_carteira.set_index('PRODUTO')['Quantidade em Carteira'].to_dict()

# Ordenar produtos pela prioridade
curva_df['PRIORIDADE'] = curva_df['PRIORIDADE'].astype(int)
curva_ordenada = curva_df.sort_values('PRIORIDADE')

for _, row in curva_ordenada.iterrows():
    produto = row['PRODUTO']
    descricao_produto = row['DESCRICAO PRODUTO']
    curva_produto = row['CURVA']

    estrutura_item = estrutura_df[estrutura_df['PRODUTO'] == produto]

    if estrutura_item.empty:
        continue

    estrutura_item = estrutura_item.merge(estoque_atual_df[['COMPONENTE', 'Estoque Disponivel']], on='COMPONENTE', how='left')
    estrutura_item['Estoque Disponivel'] = estrutura_item['Estoque Disponivel'].fillna(0)

    if estrutura_item['QUANTIDADE'].isnull().any():
        continue

    estrutura_item['Qtd Possivel'] = estrutura_item['Estoque Disponivel'] / estrutura_item['QUANTIDADE']
    unidades_possiveis_iniciais = int(estrutura_item['Qtd Possivel'].min())

    # Descontar quantidade reservada (carteira)
    reserva = reservas_estoque.get(produto, 0)
    unidades_possiveis = max(0, unidades_possiveis_iniciais - int(reserva))

    if unidades_possiveis > 0:
        carteira = qtd_carteira[qtd_carteira['PRODUTO'] == produto]['Quantidade em Carteira'].sum()
        produtos_possiveis.append({
            'Produto': produto,
            'Descricao Produto': descricao_produto,
            'Curva': curva_produto,
            'Unidades Possíveis': unidades_possiveis,
            'Quantidade em Carteira': int(carteira), 'Grupo Planejador': row['DESCRICAO GRUPO PLANEJADOR']
        })

        # Atualizar estoque
        for idx, comp_row in estrutura_item.iterrows():
            componente = comp_row['COMPONENTE']
            quantidade_necessaria = comp_row['QUANTIDADE'] * unidades_possiveis
            estoque_atual_df.loc[estoque_atual_df['COMPONENTE'] == componente, 'Estoque Disponivel'] -= quantidade_necessaria

# Criar DataFrame final
df_possiveis = pd.DataFrame(produtos_possiveis)

# Calcular somatórios
total_montagem = df_possiveis['Unidades Possíveis'].sum()
total_carteira = df_possiveis['Quantidade em Carteira'].sum()
total_produtos = len(df_possiveis)

st.dataframe(df_possiveis.applymap(format_number))

# Exibir métricas abaixo da tabela

# Campo para digitar código do produto e consultar unidades possíveis
st.subheader("Consulta de Quantidade Possível por Produto")
codigo_busca = st.text_input('Digite o código do produto (ex: 805335-01):')

if codigo_busca:
    resultado = df_possiveis[df_possiveis['Produto'] == codigo_busca]
    if not resultado.empty:
        unidades_possiveis = resultado['Unidades Possíveis'].values[0]
        st.success(f"Quantidade possível de montagem para o produto {codigo_busca}: {format_number(unidades_possiveis)} unidades")
    else:
        st.warning(f"Produto {codigo_busca} não encontrado ou não possui unidades possíveis para montagem.")

# Layout de Dashboard com Caixas
col1, col2, col3 = st.columns(3)

col1.markdown(f"""
<div style='background-color:#e6f2ff; padding:20px; border-radius:10px; text-align:center;'>
    <h3 style='color:#1f77b4;'>Quantidade Total de Produtos</h3>
    <p style='font-size:36px; color:#1f77b4;'><b>{format_number(total_produtos)}</b></p>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div style='background-color:#e8f5e9; padding:20px; border-radius:10px; text-align:center;'>
    <h3 style='color:#2ca02c;'>Unidades Possíveis para Montagem</h3>
    <p style='font-size:36px; color:#2ca02c;'><b>{format_number(total_montagem)}</b></p>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div style='background-color:#fff3e0; padding:20px; border-radius:10px; text-align:center;'>
    <h3 style='color:#ff7f0e;'>Valor Total na Carteira</h3>
    <p style='font-size:36px; color:#ff7f0e;'><b>{format_number(total_carteira)}</b></p>
</div>
""", unsafe_allow_html=True)



# Botão para baixar a lista em Excel
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

# Nova seção: Lista de Pedidos que Podemos Atender
st.subheader("Lista de Pedidos que Podemos Atender com Estoque Atual")

# Juntar pedidos com produtos possíveis
pedidos_possiveis = pedidos_abertos_df.merge(df_possiveis[['Produto']], left_on='PRODUTO', right_on='Produto', how='inner')

# Remover pedidos com quantidade igual a zero
pedidos_possiveis = pedidos_possiveis[pedidos_possiveis['QUANTIDADE PRODUZIR'] > 0]

# Remover pontos do código e número do pedido
pedidos_possiveis['COD'] = pedidos_possiveis['COD'].astype(str).str.replace('.', '', regex=False)
pedidos_possiveis['PEDIDO'] = pedidos_possiveis['PEDIDO'].astype(str).str.replace('.', '', regex=False)

# Formatar datas no formato dd/mm/yyyy
pedidos_possiveis['DATA PREVISTA'] = pd.to_datetime(pedidos_possiveis['DATA PREVISTA']).dt.strftime('%d/%m/%Y')
pedidos_possiveis['DATA SOLICITADA'] = pd.to_datetime(pedidos_possiveis['DATA SOLICITADA']).dt.strftime('%d/%m/%Y')

# Selecionar colunas desejadas
pedidos_possiveis = pedidos_possiveis[['COD', 'CLIENTE', 'MERCADO', 'DOC', 'PEDIDO', 'PRODUTO', 'QUANTIDADE PRODUZIR', 'DATA PREVISTA', 'DATA SOLICITADA']]

# Remover pedidos com quantidade igual a zero
pedidos_possiveis = pedidos_possiveis[pedidos_possiveis['QUANTIDADE PRODUZIR'] > 0]

# Remover pontos do número do pedido
pedidos_possiveis['PEDIDO'] = pedidos_possiveis['PEDIDO'].astype(str).str.replace('.', '', regex=False)

# Formatar datas no formato dd/mm/yyyy
pedidos_possiveis['DATA PREVISTA'] = pd.to_datetime(pedidos_possiveis['DATA PREVISTA']).dt.strftime('%d/%m/%Y')
pedidos_possiveis['DATA SOLICITADA'] = pd.to_datetime(pedidos_possiveis['DATA SOLICITADA']).dt.strftime('%d/%m/%Y')

pedidos_possiveis = pedidos_possiveis[['COD', 'CLIENTE', 'MERCADO', 'DOC', 'PEDIDO', 'PRODUTO', 'QUANTIDADE PRODUZIR', 'DATA PREVISTA', 'DATA SOLICITADA']]

# Remover pedidos com quantidade igual a zero
pedidos_possiveis = pedidos_possiveis[pedidos_possiveis['QUANTIDADE PRODUZIR'] > 0]

# Calcular total de quantidade
total_pedidos_quantidade = pedidos_possiveis['QUANTIDADE PRODUZIR'].sum()

# Exibir tabela
st.dataframe(pedidos_possiveis.applymap(format_number))

# Exibir totalizador
st.markdown(f"""
<div style='background-color:#f1f8e9; padding:10px; border-radius:10px; text-align:center; margin-top:10px;'>
    <h3 style='color:#33691e;'>Total de Quantidade de Pedidos Atendíveis: <b>{format_number(total_pedidos_quantidade)}</b></h3>
</div>
""", unsafe_allow_html=True)

# Botão para baixar a lista de pedidos possíveis
output_pedidos = io.BytesIO()
with pd.ExcelWriter(output_pedidos, engine='openpyxl') as writer:
    pedidos_possiveis.to_excel(writer, index=False)
processed_pedidos = output_pedidos.getvalue()

st.download_button(
    label="Baixar Lista de Pedidos Atendíveis em Excel",
    data=processed_pedidos,
    file_name='pedidos_atendiveis.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    key='download_pedidos'
)
