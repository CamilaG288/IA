import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("Painel de Planejamento - Montagem Possível de Turbocompressores")

# Carregamento de planilhas
curva_df = pd.read_excel("CURVA ABC.xlsx")
estrutura_df = pd.read_excel("ESTRUTURA.xlsx")
estoque_df = pd.read_excel("ESTOQUE_DISPONIVEL.xlsx")  # nova planilha com reserva descontada
pedidos_df = pd.read_excel("PEDIDOS_ABERTO.xlsx")

# Tratamento básico de colunas
for df in [curva_df, estrutura_df, estoque_df, pedidos_df]:
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().str.replace(".", "", regex=False)

# Preparação de dados
curva_df['PRIORIDADE'] = curva_df['PRIORIDADE'].astype(int)
curva_ordenada = curva_df.sort_values("PRIORIDADE")

# Agrupamento de pedidos abertos por produto
qtd_carteira = pedidos_df.groupby("PRODUTO")["QUANTIDADE PRODUZIR"].sum().reset_index().rename(columns={"QUANTIDADE PRODUZIR": "Quantidade em Carteira"})

# Construção da tabela de montagem possível
estoque_df = estoque_df.rename(columns={"QUANTIDADE": "Estoque Disponivel"})
estoque_disponivel = estoque_df.set_index("COMPONENTE")
possiveis = []

for _, row in curva_ordenada.iterrows():
    produto = row["PRODUTO"]
    estrutura_item = estrutura_df[estrutura_df["PRODUTO"] == produto]

    if estrutura_item.empty:
        continue

    estrutura_item = estrutura_item.merge(estoque_disponivel[["Estoque Disponivel"]], on="COMPONENTE", how="left")
    estrutura_item["Estoque Disponivel"] = estrutura_item["Estoque Disponivel"].fillna(0)
    estrutura_item["Qtd Possivel"] = estrutura_item["Estoque Disponivel"] / estrutura_item["QUANTIDADE"]

    unidades_possiveis = int(estrutura_item["Qtd Possivel"].min())

    if unidades_possiveis > 0:
        carteira = qtd_carteira[qtd_carteira["PRODUTO"] == produto]["Quantidade em Carteira"].sum()
        possiveis.append({
            "Produto": produto,
            "Descrição Produto": row["DESCRICAO PRODUTO"],
            "Unidades Possíveis": unidades_possiveis,
            "Quantidade em Carteira": int(carteira),
            "Grupo Planejador": row["DESCRICAO GRUPO PLANEJADOR"],
            "Curva": row["CURVA"]
        })

        for _, comp_row in estrutura_item.iterrows():
            comp = comp_row["COMPONENTE"]
            qtd = comp_row["QUANTIDADE"] * unidades_possiveis
            if comp in estoque_disponivel.index:
                estoque_disponivel.at[comp, "Estoque Disponivel"] -= qtd
                if estoque_disponivel.at[comp, "Estoque Disponivel"] < 0:
                    estoque_disponivel.at[comp, "Estoque Disponivel"] = 0

# Exibição
st.subheader("Produtos com Montagem Possível")
if possiveis:
    df_resultado = pd.DataFrame(possiveis)
    df_resultado.index += 1
    st.dataframe(df_resultado)

    # Exportar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resultado.to_excel(writer, index=False)
    st.download_button(
        label="📦 Baixar resultado em Excel",
        data=output.getvalue(),
        file_name="montagem_possivel.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Nenhum produto pode ser montado com o estoque atual.")

