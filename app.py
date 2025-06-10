import streamlit as st
import pandas as pd

st.set_page_config(page_title="Montagem de Produtos", layout="wide")
st.title("🔧 Análise de Montagem com Estoque Real (Algoritmo Greedy)")

# URLs dos arquivos no GitHub
url_estoque = "https://github.com/CamilaG288/IA/raw/main/ESTOQUE_DISPONIVEL.xlsx"
url_estrutura = "https://github.com/CamilaG288/IA/raw/main/ESTRUTURA.xlsx"
url_curva = "https://github.com/CamilaG288/IA/raw/main/CURVA%20ABC.xlsx"

# Leitura dos dados
estoque_df = pd.read_excel(url_estoque)
estrutura_df = pd.read_excel(url_estrutura)
curva_df = pd.read_excel(url_curva)

# Seleção e padronização
estoque_df = estoque_df[['COMPONENTE', 'QUANTIDADE']]
estrutura_df = estrutura_df[['PRODUTO', 'COMPONENTE', 'QUANTIDADE']]
curva_df = curva_df[['PRODUTO', 'DESCRICAO PRODUTO', 'CURVA', 'DESCRICAO GRUPO PLANEJADOR', 'PRIORIDADE']]

estoque_df['COMPONENTE'] = estoque_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['COMPONENTE'] = estrutura_df['COMPONENTE'].astype(str).str.strip()
estrutura_df['PRODUTO'] = estrutura_df['PRODUTO'].astype(str).str.strip()
curva_df['PRODUTO'] = curva_df['PRODUTO'].astype(str).str.strip()

# Criar dicionário de estoque atual
estoque_atual = estoque_df.groupby('COMPONENTE')['QUANTIDADE'].sum().to_dict()

# Unir estrutura com curva ABC
estrutura_com_dados = estrutura_df.merge(curva_df, on='PRODUTO', how='left')
produtos_ordenados = estrutura_com_dados[['PRODUTO', 'PRIORIDADE']].drop_duplicates()
produtos_ordenados = produtos_ordenados.sort_values(by='PRIORIDADE')

# Algoritmo greedy
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

# Montar DataFrame final
resultado_df = pd.DataFrame(resultados)

# Filtrar apenas produtos com unidades possíveis > 0
resultado_df = resultado_df[resultado_df['UNIDADES POSSÍVEIS'] > 0]

# Exibir tabela
st.subheader("📋 Produtos que podem ser montados com estoque atual")
st.dataframe(
    resultado_df[['PRODUTO', 'DESCRIÇÃO', 'UNIDADES POSSÍVEIS', 'CURVA', 'GRUPO PLANEJADOR']]
    .sort_values(by='UNIDADES POSSÍVEIS', ascending=False),
    use_container_width=True
)

# === DASHBOARD VISUAL ABAIXO DA TABELA ===
total_codigos_montaveis = resultado_df.shape[0]
total_unidades_montadas = resultado_df['UNIDADES POSSÍVEIS'].sum()

# Cartões com HTML + CSS (com chaves escapadas)
st.markdown("""
<style>
.card-container {{
    display: flex;
    gap: 20px;
    margin-top: 10px;
    justify-content: center;
}}
.card {{
    flex: 1;
    padding: 20px;
    border-radius: 10px;
    color: white;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    max-width: 300px;
}}
.card-blue {{
    background-color: #1976D2;
}}
.card-green {{
    background-color: #2E7D32;
}}
.card small {{
    display: block;
    font-size: 14px;
    font-weight: normal;
    margin-top: 5px;
}}
</style>

<div class="card-container">
    <div class="card card-blue">
        {codigos}
        <small>Total de Códigos Montáveis</small>
    </div>
    <div class="card card-green">
        {unidades}
        <small>Total de Unidades Possíveis</small>
    </div>
</div>
""".format(
    codigos=total_codigos_montaveis,
    unidades=total_unidades_montadas
), unsafe_allow_html=True)

# === BOTÃO DE DOWNLOAD EXCEL ===
st.markdown("### 📥 Exportar resultados")
st.download_button(
    label="📥 Baixar resultados em Excel",
    data=resultado_df.to_excel(index=False, engine='openpyxl'),
    file_name="produtos_montaveis.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
