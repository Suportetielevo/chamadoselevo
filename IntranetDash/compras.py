import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
import plotly.express as px
import io
from io import BytesIO
from pandas import ExcelWriter
import xlsxwriter
import streamlit as st
from streamlit_option_menu import option_menu


# Conexão com o banco de dados
meubd = mysql.connector.connect(
    host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
    user='monolito',
    password='1642gEkdWYtQ',
    database='monolito'
)

cursor = meubd.cursor()

# Executa a consulta SQL
cursor.execute("""
SELECT p.id                                       as PROJETO,
       c.name                                     as CLIENTE,
       u.name                                     as CONSULTOR,
       fr.VALOR_SOMADO                            as VALOR_RECEBIMENTOS,
       c2.name                                    as CIDADE,
       p2.name                                    as ESTADO,
       p.panel_type                               as PAINEL,
       (select sum(gk.panel_count)
        from generator_kits gk
                 join generator_kit_projects gkp on gk.id = gkp.generator_kit_id
        where gkp.project_id = p.id)              as QTD_PAINEIS,
       group_concat(wp.description)               as INVERSOR,
       l.truck_routes                             as ROTAS,
       s.name                                     as STATUS_LOGISTICA,
       rs.name                                     as STATUS_FATURAMENTO,
       if((f2.sol_facil) = 1, 'SOL FACIL', 'NAO') as SOL_FACIL,
       DATE(t.created_at)                               as DATA_PGMTO_CONFIRMADO,
       datediff(curdate(), l.created_at)          as DIAS_DESDE_ENTROU_LOGISTICA,
       DATE(p.created_at)                               as DATA_CRIACAO_PROJETO
from projects p
         join clients c on p.client_id = c.id
         join franchises f on p.franchise_id = f.id
         join users u on f.user_id = u.id
         join financings f2 on p.id = f2.project_id
         left join (select sum(fr.value) as VALOR_SOMADO, fr.id, fr.financing_id
                    from financing_recipes fr
                    where fr.active = 1
                    group by fr.financing_id) fr on fr.financing_id = f2.id
         join revenues r on p.id = r.project_id
         join statuses rs on rs.id = r.status_id
         left join (select a.created_at, a.auditable_id
                    from audits a
                    where a.auditable_type = 'revenue'
                      and a.new_values like '%{"status_id":"52"%'
                    group by a.auditable_id) t on t.auditable_id = r.id
         left join logistics l on p.id = l.project_id
         left join statuses s on l.status_id = s.id
         join cities c2 on p.city_id = c2.id
         join provinces p2 on c2.province_id = p2.id
         join generator_kit_projects gkp on p.id = gkp.project_id
         join generator_kits gk on gkp.generator_kit_id = gk.id
         left join generator_kit_products g on gk.id = g.generator_kit_id
         left join warehouse_products wp on g.warehouse_product_id = wp.id and wp.type like '%inve%'
where l.status_id in (199, 152)
   or r.status_id in (273)
group by p.id
order by l.created_at asc
 """)

# Obter os dados
dados = cursor.fetchall()

# Criar um DataFrame do Pandas
df = pd.DataFrame(dados, columns=[desc[0] for desc in cursor.description])

# Criar um DataFrame do Pandas e converter 'VALOR_RECEBIMENTOS' para numérico
df = pd.DataFrame(dados, columns=[desc[0] for desc in cursor.description])
df['VALOR_RECEBIMENTOS'] = pd.to_numeric(df['VALOR_RECEBIMENTOS'], errors='coerce')

# Converter a coluna 'QTD_PAINEIS' para numérico
df['QTD_PAINEIS'] = pd.to_numeric(df['QTD_PAINEIS'], errors='coerce')

# Fechar a conexão com o banco de dados
cursor.close()
meubd.close()

# Título do Dashboard
st.title('Projetos por Rotas ( Compras )')

# Filtragem por mês e ano
st.sidebar.header("Filtros")

# Seleção do mês
mes = st.sidebar.selectbox(
    "Selecione o Mês",
    ('Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'),
    index=0
)

# Seleção do ano
ano = st.sidebar.slider("Selecione o Ano", min_value=2020, max_value=2024, value=2024)

# Aplicar filtros ao DataFrame
if mes != 'Todos':
    mes_numerico = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                   'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}[mes]
    df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.month == mes_numerico]
if ano != 2024:
    df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]

if ano != 2023:
    df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]

if ano != 2022:
    df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]

if ano != 2021:
    df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]
# Exibir a tabela com os dados
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
    file_name='compras.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    key='download-xlsx'
)