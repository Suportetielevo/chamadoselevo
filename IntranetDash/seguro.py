import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
import io

# Função para conectar ao banco e obter dados
@st.cache_data
def get_data():
    db_config = {
        'host': 'monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
        'user': 'monolito',
        'password': '1642gEkdWYtQ',
        'database': 'monolito'
    }

    query = """
        SELECT 
            p.id AS PROJETO,
            c.fantasy_name AS NOME_FANTASIA,
            c.name AS NOME_CLIENTE,
            c.document AS DOCUMENTO,
            c.secondary_document AS DOCUMENTO_SECUNDARIO,
            c.zip_code AS CEP_CLIENTE,
            c2.name AS CIDADE_CLIENTE,
            p2.name AS ESTADO_CLIENTE,
            c.home_address AS ENDERECO_CLIENTE,
            c.home_address_number AS NUMERO_ENDERECO_CLIENTE,
            c.neighborhood AS BAIRRO_CLIENTE,
            c.installation_zip_code AS CEP_CLIENTE_INSTALACAO,
            c3.name AS CIDADE_INSTALACAO,
            p3.name AS ESTADO_INSTALACAO,
            c.installation_address AS ENDERECO_INSTALACAO,
            c.installation_address_number AS NUMERO_ENDERECO_INSTALACAO,
            c.installation_neighborhood AS BAIRRO_INSTALACAO
        FROM client c
        LEFT JOIN project p ON c.id = p.client_id
        LEFT JOIN city c2 ON c.city_id = c2.id
        LEFT JOIN state p2 ON c2.state_id = p2.id
        LEFT JOIN city c3 ON c.installation_city_id = c3.id
        LEFT JOIN state p3 ON c3.state_id = p3.id
        LIMIT 500
    """

    conn = mysql.connector.connect(**db_config)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Interface do Streamlit
st.set_page_config(page_title="Relatório de Clientes", layout="wide")
st.title("📋 Relatório de Clientes e Projetos")

# Obtenção de dados
df = get_data()

# Filtro simples por cidade
cidade_opcao = st.selectbox("Filtrar por Cidade do Cliente:", ["Todas"] + sorted(df["CIDADE_CLIENTE"].dropna().unique().tolist()))
if cidade_opcao != "Todas":
    df_filtered = df[df["CIDADE_CLIENTE"] == cidade_opcao]
else:
    df_filtered = df

# Exibir tabela
st.dataframe(df_filtered, use_container_width=True)

# Botão de download em Excel
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='Sheet1')
buffer.seek(0)

st.download_button(
    label="⬇️ Baixar Dados (XLSX)",
    data=buffer,
    file_name="relatorio_clientes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
