import mysql.connector
import pandas as pd
import streamlit as st
from datetime import datetime

# Conexão com o banco de dados
meubd = mysql.connector.connect(
    host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
    user='monolito',
    password='1642gEkdWYtQ',
    database='monolito'
)

cursor = meubd.cursor()

# Função para contar projetos por status
def contar_projetos_por_status(status, ano, mes):
    cursor.execute(f"""
        SELECT COUNT(DISTINCT p.id)
        FROM projects p
        JOIN clients c ON c.id = p.client_id
        JOIN homolagations h ON h.project_id = p.id
        JOIN statuses s ON s.id = h.status_id
        WHERE s.name = '{status}'
          AND c.name != 'Sociedade Goiana'
          AND YEAR(h.created_at) = {ano}
          AND MONTH(h.created_at) = {mes}
    """)
    return cursor.fetchone()[0]

# Título do Dashboard
st.title('Análise de Projetos - Mês e Ano Selecionados')

# Filtro de Data
st.sidebar.title('Filtro de Data')
ano_selecionado = st.sidebar.selectbox('Selecione o Ano:', range(2024, datetime.now().year + 1))
mes_selecionado = st.sidebar.selectbox('Selecione o Mês:', range(1, 13))

# Contando projetos em cada status
st.subheader(f"Contagem de Projetos por Status em {mes_selecionado}/{ano_selecionado}")

# Contar projetos em cada status
projetos_homologacao = contar_projetos_por_status("SOLICITAÇÃO DE HOMOLOGAÇÃO", ano_selecionado, mes_selecionado)
projetos_aprovados = contar_projetos_por_status("PROJETO APROVADO", ano_selecionado, mes_selecionado)
projetos_aguardando_aprovacao = contar_projetos_por_status("AGUARDANDO APROVAÇÃO", ano_selecionado, mes_selecionado)

st.write(f"Projetos em Homologação: {projetos_homologacao}")
st.write(f"Projetos Aprovados: {projetos_aprovados}")
st.write(f"Projetos Aguardando Aprovação: {projetos_aguardando_aprovacao}")

# Contar projetos com os status especificados
st.subheader("Contagem de Projetos por Status no Sistema Hoje (Mês 07)")
projetos_aguardando_liberacao_crea = contar_projetos_por_status("AGUARD. LIBERAÇAO CREA", datetime.now().year, 7)
projetos_dados_confirmados = contar_projetos_por_status("DADOS CONFIRMADOS", datetime.now().year, 7)
projetos_aguardando_pagamento_art = contar_projetos_por_status("AGUARDANDO PAGAMENTO DA ART", datetime.now().year, 7)
projetos_documentos_anexados = contar_projetos_por_status("DOCUMENTOS ANEXADOS", datetime.now().year, 7)

st.write(f"AGUARD. LIBERAÇAO CREA: {projetos_aguardando_liberacao_crea}")
st.write(f"DADOS CONFIRMADOS: {projetos_dados_confirmados}")
st.write(f"AGUARDANDO PAGAMENTO DA ART: {projetos_aguardando_pagamento_art}")
st.write(f"DOCUMENTOS ANEXADOS: {projetos_documentos_anexados}")

# Fechar a conexão com o banco de dados
cursor.close()
meubd.close()