import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
import plotly.express as px
import io
from io import BytesIO
from pandas import ExcelWriter
import xlsxwriter

# Conexão com o banco de dados
meubd = mysql.connector.connect(
    host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
    user='monolito',
    password='1642gEkdWYtQ',
    database='monolito'
)

cursor = meubd.cursor()

# Consulta SQL
query = """
SELECT p.id AS PROJETO,
       c.name AS CLIENTE,
       c2.name AS CIDADE_PROJETO,
       p2.initial AS ESTADO_PROJETO,
       SUM(gk.panel_count) AS QTD_PAINEIS,
       d.name AS CONCESSIONARIA,
       fr.VALOR_SOMADO AS VALOR_RECEBIMENTOS,
       DATE_FORMAT(assinatura.assinatura_data, '%d/%m/%Y') AS DATA_ASSINATURA,
       DATE_FORMAT(pagamento.pagamento_data, '%d/%m/%Y') AS DATA_PAGAMENTO,
       DATE_FORMAT(h.created_at, '%d/%m/%Y') AS DATA_ENTROU_HOMOLOG,
       DATE_FORMAT(entrega.entrega_data, '%d/%m/%Y') AS DATA_ENTREGUE,
       DATE_FORMAT(aprovado.aprovado_data, '%d/%m/%Y') AS DATA_APROVADO,
       DATE_FORMAT(instalacao.instalacao_data, '%d/%m/%Y') AS DATA_INSTALADO,
       i.price_panel AS VALOR_PAINEL_INSTALACAO,
       ip.name AS INSTALADOR,
       DATE_FORMAT(medidor.medidor_data, '%d/%m/%Y') AS DATA_VISTORIA_MEDIDOR,
       DATE_FORMAT(startado.startado_data, '%d/%m/%Y') AS DATA_STARTADO
FROM projects p
JOIN clients c ON p.client_id = c.id
JOIN cities c2 ON p.city_id = c2.id
JOIN provinces p2 ON c2.province_id = p2.id
JOIN financings f2 ON p.id = f2.project_id
LEFT JOIN (SELECT SUM(fr.value) AS VALOR_SOMADO, fr.id, fr.financing_id
           FROM financing_recipes fr
           WHERE fr.active = 1
           GROUP BY fr.financing_id) fr ON fr.financing_id = f2.id
JOIN module_contracts mc ON p.id = mc.project_id
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS assinatura_data
         FROM project_interactions
         WHERE department_id = 2
           AND type = 'status_change'
           AND comment = 'Contrato assinado cliente'
         GROUP BY project_id) assinatura ON assinatura.project_id = mc.project_id
JOIN revenues r ON p.id = r.project_id AND r.status_id = 52
JOIN (SELECT project_id,
             MIN(created_at) AS pagamento_data
      FROM project_interactions
      WHERE department_id = 4
        AND type = 'status_change'
        AND comment = 'PAGAMENTO CONFIRMADO'
      GROUP BY project_id) pagamento ON pagamento.project_id = r.project_id
LEFT JOIN logistics l ON p.id = l.project_id AND l.status_id IN (180, 261)
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS entrega_data
         FROM project_interactions
         WHERE department_id = 10
           AND type = 'status_change'
           AND comment LIKE '%ENTREGUE%'
         GROUP BY project_id) entrega ON entrega.project_id = l.project_id
LEFT JOIN installations i ON p.id = i.project_id
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS instalacao_data
         FROM project_interactions
         WHERE department_id = 5
           AND type = 'status_change'
           AND comment LIKE '%INSTALAÇÃO CONCLUÍDA%'
         GROUP BY project_id) instalacao ON instalacao.project_id = i.project_id
LEFT JOIN installation_people ip ON i.installation_person_id = ip.id
LEFT JOIN homolagations h ON p.id = h.project_id
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS aprovado_data
         FROM project_interactions
         WHERE department_id = 3
           AND type = 'status_change'
           AND comment = 'PROJETO APROVADO'
         GROUP BY project_id) aprovado ON aprovado.project_id = h.project_id
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS medidor_data
         FROM project_interactions
         WHERE department_id = 3
           AND type = 'status_change'
           AND comment = 'SOLICITADO VISTORIA E TROCA DO MEDIDOR'
         GROUP BY project_id) medidor ON medidor.project_id = h.project_id
LEFT JOIN (SELECT project_id,
                MIN(created_at) AS startado_data
         FROM project_interactions
         WHERE department_id = 3
           AND type = 'status_change'
           AND comment = 'PROJETO STARTADO'
         GROUP BY project_id) startado ON startado.project_id = h.project_id
JOIN dealerships d ON p.dealership_id = d.id
JOIN generator_kit_projects gkp ON p.id = gkp.project_id
JOIN generator_kits gk ON gkp.generator_kit_id = gk.id
GROUP BY p.id
ORDER BY pagamento.pagamento_data
"""

# Executar a consulta
cursor.execute(query)

# Obter os dados
dados = cursor.fetchall()

# Criar DataFrame
df = pd.DataFrame(dados, columns=[desc[0] for desc in cursor.description])
df['VALOR_RECEBIMENTOS'] = pd.to_numeric(df['VALOR_RECEBIMENTOS'], errors='coerce')
df['QTD_PAINEIS'] = pd.to_numeric(df['QTD_PAINEIS'], errors='coerce')

# Fechar a conexão
cursor.close()
meubd.close()

# Título do Dashboard
st.title('Projetos (Vistoria)')

# Barra lateral com filtros
st.sidebar.header("Filtros")

# Seleção Todos
mes = st.sidebar.selectbox(
    "Selecione o Mês",
    ('Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'),
    index=0
)

# Aplicar filtros
if mes != 'Todos':
    mes_numerico = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                   'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}[mes]
    df = df[pd.to_datetime(df['DATA_PAGAMENTO']).dt.month == mes_numerico]

# Filtra apenas projetos com data de pagamento confirmada
df = df[~df['DATA_PAGAMENTO'].isna()]

# Exibir a tabela
st.dataframe(df)

# Download como XLSX
buffer = io.BytesIO()
writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
df.to_excel(writer, index=False, sheet_name='Sheet1')
writer.close()  # Salva o arquivo Excel no buffer
output = buffer.getvalue()

st.download_button(
    label="Download dos dados (XLSX)",
    data=output,
    file_name='vistoria.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    key='download-xlsx'
)
