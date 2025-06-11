import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Painel de Montagem e Pedidos", layout="wide")
st.title("🔧 Painel de Montagem de Produtos e Atendimento de Pedidos")

# URLs dos arquivos no GitHub
url_estoque_disponivel = "https://github.com/CamilaG288/IA/raw/main/ESTOQUE_DISPONIVEL.xlsx"
url_estrutura = "https://github.com/CamilaG288/IA/raw/main/ESTRUTURA.xlsx"
url_curva = "https://github.com/CamilaG288/IA/raw/main/CURVA%20ABC.xlsx"
url_pedidos = "https://github.com/CamilaG288/IA/raw/refs/heads/main/PEDIDOS_ABERTO.xlsx"
url_estrutura_pedidos = "https://github.com/CamilaG288/IA/raw/refs/heads/main/ESTRUTURA_PEDIDOS_ABERTOS.xlsx"
url_estoque_alx = "https://github.com/CamilaG288/IA/raw/refs/heads/main/ESTOQUE_ALMOX102.xlsx"

# ========================
# Produtos Montáveis
# ========================
estoque_df = pd.read_excel(url_estoque_disponivel)
estrutura_df = pd.read_excel(url_estrutura)
curva_df = pd.read_excel(url_curva)

estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
curva_df = curva_df[['PRODUTO', 'DESCRICAO PRODUTO', 'CURVA', 'DESCRICAO GRUPO PLANEJADOR', 'PRIORIDADE']]

estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

estrutura_com_dados = estrutura_df.merge(curva_df, on='PRODUTO', how='left')
produtos_ordenados = estrutura_com_dados[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

resultados = []

for _, linha in produtos_ordenados.iterrows():
    produto = linha['PRODUTO']
    estrutura_prod = estrutura_com_dados[estrutura_com_dados['PRODUTO'] == produto]

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

    if qtd_montar > 0:
        for _, comp in estrutura_prod.iterrows():
            componente = comp['COMPONENTE']
            qtd_necessaria = comp['QUANTIDADE']
            estoque_atual[componente] -= qtd_necessaria * qtd_montar

    descricao = estrutura_prod['DESCRICAO PRODUTO'].iloc[0]
    curva = estrutura_prod['CURVA'].iloc[0]
    grupo = estrutura_prod['DESCRICAO GRUPO PLANEJADOR'].iloc[0]

    resultados.append({
        'PRODUTO': produto,
        'DESCRIÇÃO': descricao,
        'UNIDADES POSSÍVEIS': qtd_montar,
        'CURVA': curva,
        'GRUPO PLANEJADOR': grupo
    })

resultado_df = pd.DataFrame(resultados)
resultado_df = resultado_df[resultado_df['UNIDADES POSSÍVEIS'] > 0]

st.subheader("📋 Produtos que podem ser montados com estoque atual")
st.dataframe(
    resultado_df[['PRODUTO', 'DESCRIÇÃO', 'UNIDADES POSSÍVEIS', 'CURVA', 'GRUPO PLANEJADOR']]
    .sort_values(by='UNIDADES POSSÍVEIS', ascending=False),
    use_container_width=True
)

# =============================
# Pedidos em Carteira
# =============================
pedidos_df = pd.read_excel(url_pedidos, dtype=str)
pedidos_df['QUANTIDADE PRODUZIR'] = pd.to_numeric(pedidos_df['QUANTIDADE PRODUZIR'], errors='coerce')
pedidos_df = pedidos_df[pedidos_df['QUANTIDADE PRODUZIR'] > 0].copy()
pedidos_df['DATA PREVISTA'] = pd.to_datetime(pedidos_df['DATA PREVISTA'], errors='coerce').dt.strftime('%d/%m/%Y')
pedidos_df['DATA SOLICITADA'] = pd.to_datetime(pedidos_df['DATA SOLICITADA'], errors='coerce').dt.strftime('%d/%m/%Y')

estrutura_df = pd.read_excel(url_estrutura_pedidos)
estoque_df = pd.read_excel(url_estoque_alx)

pedidos_df['PRODUTO'] = pedidos_df['PRODUTO'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()

estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()
pedidos_df = pedidos_df.sort_values(by='DATA PREVISTA')

linhas_atendidas = []
for _, pedido in pedidos_df.iterrows():
    produto = pedido['PRODUTO']
    qtd_necessaria = pedido['QUANTIDADE PRODUZIR']
    estrutura_prod = estrutura_df[estrutura_df['PRODUTO'] == produto]
    if estrutura_prod.empty:
        continue
    pode_montar = True
    for _, comp in estrutura_prod.iterrows():
        comp_cod = comp['COMPONENTE']
        qtd_comp = comp['QUANTIDADE'] * qtd_necessaria
        if estoque_atual.get(comp_cod, 0) < qtd_comp:
            pode_montar = False
            break
    if pode_montar:
        for _, comp in estrutura_prod.iterrows():
            comp_cod = comp['COMPONENTE']
            qtd_comp = comp['QUANTIDADE'] * qtd_necessaria
            estoque_atual[comp_cod] -= qtd_comp
        linhas_atendidas.append({
            'COD': pedido['COD'],
            'CLIENTE': pedido['CLIENTE'],
            'MERCADO': pedido['MERCADO'],
            'DOC': pedido['DOC'],
            'PEDIDO': pedido['PEDIDO'],
            'LINHA': pedido['LINHA'],
            'PRODUTO': produto,
            'QUANTIDADE PRODUZIR': qtd_necessaria,
            'DATA PREVISTA': pedido['DATA PREVISTA'],
            'DATA SOLICITADA': pedido['DATA SOLICITADA']
        })
