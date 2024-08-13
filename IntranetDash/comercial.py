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
from datetime import datetime
import plotly.graph_objects as go

# Conexão com o banco de dados
meubd = mysql.connector.connect(
    host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
    user='monolito',
    password='1642gEkdWYtQ',
    database='monolito'
)

cursor = meubd.cursor()

# Executa a consulta SQL (sem filtro de data)
cursor.execute("""
   select p.id              as ID_PROJETO,
       c.name               as CLIENTE,
       c2.name              as CIDADE_CLIENTE,
       p2.name              as ESTADO_CLIENTE,
       u.name               as CONSULTOR,
       u2.name              as CONSULTOR_EXTERNO,
       ppt.description      as FORMA_DE_PAGAMENTO,
       fr.VALOR_SOMADO      as VALOR_RECEBIMENTO,
       DATE(t2.created_at)  as DATA_ASSINADO,
       DATE(pi.created_at)  as DATA_PGMTO_CONFIRMADO
from projects p
         join clients c on p.client_id = c.id
         join franchises f on p.franchise_id = f.id
         join users u on f.user_id = u.id
         left join outsider_franchises o on p.outsider_franchise_id = o.id
         left join users u2 on o.user_id = u2.id
         join cities c2 on c.city_id = c2.id
         join provinces p2 on c2.province_id = p2.id
         join financings f2 on p.id = f2.project_id and f2.status_id not in (123)
         left join (select sum(fr.value) as VALOR_SOMADO, fr.id, fr.financing_id
                    from financing_recipes fr
                    where fr.active = 1
                    group by fr.financing_id) fr on fr.financing_id = f2.id
         join module_contracts mc on p.id = mc.project_id
         left join (select a.created_at, a.auditable_id
                    from audits a
                    where a.auditable_type = 'contract'
                      and a.new_values like '%{"status_id":"32"%') t2 on t2.auditable_id = mc.id
         join project_interactions pi
              on p.id = pi.project_id and pi.type = 'status_change' and pi.comment = 'PAGAMENTO CONFIRMADO'
         join project_payment_types ppt on p.payment_type_id = ppt.id
group by p.id
order by pi.created_at
     """)

# Obter os dados
dados = cursor.fetchall()

# Criar um DataFrame do Pandas
df = pd.DataFrame(dados, columns=[desc[0] for desc in cursor.description])

# Criar um DataFrame do Pandas e converter 'VALOR_RECEBIMENTOS' para numérico
df['VALOR_RECEBIMENTO'] = pd.to_numeric(df['VALOR_RECEBIMENTO'], errors='coerce')
df['DATA_PGMTO_CONFIRMADO'] = pd.to_datetime(df['DATA_PGMTO_CONFIRMADO'])

# Fechar a conexão com o banco de dados
cursor.close()
meubd.close()

# Título do Dashboard
st.title('Vendas Totais - Dep. Comercial')

# --- Layout com sidebar ---
st.sidebar.title('Filtros')

# Filtro de data
ano_atual = datetime.now().year
mes_atual = datetime.now().month

ano_selecionado = st.sidebar.selectbox('Selecione o ano:', df['DATA_PGMTO_CONFIRMADO'].dt.year.unique(), index=ano_atual - 2020)
mes_selecionado = st.sidebar.selectbox('Selecione o mês:', range(1, 13), index=mes_atual - 1)

# Filtra os dados de acordo com a seleção do usuário
df_filtrado = df[
    (df['DATA_PGMTO_CONFIRMADO'].dt.year == ano_selecionado) &
    (df['DATA_PGMTO_CONFIRMADO'].dt.month == mes_selecionado)
]

# Cálculo dos valores para o período filtrado
faturamento_total = df_filtrado['VALOR_RECEBIMENTO'].sum()
ticket_medio = df_filtrado['VALOR_RECEBIMENTO'].mean()
clientes_atendidos = df_filtrado['CLIENTE'].nunique()

# Exibindo os valores em uma tabela
st.table(
    pd.DataFrame({
        "Indicadores do Mês": ["Faturamento Total ", "Ticket Médio", "Clientes Atendidos"],
        "Valor": [
            f"R$ {faturamento_total:,.2f}",
            f"R$ {ticket_medio:,.2f}",
            f"{clientes_atendidos:,}",
        ],
    })
)

# Cálculo do Ticket Médio para os anos a partir de 2020
anos = range(2020, datetime.now().year + 1)
ticket_medios = []
for ano in anos:
    df_ano = df[df['DATA_PGMTO_CONFIRMADO'].dt.year == ano]
    ticket_medio_ano = df_ano['VALOR_RECEBIMENTO'].mean()
    ticket_medios.append({'Ano': ano, 'Ticket Médio': f'R$ {ticket_medio_ano:,.2f}'})

# Criar um DataFrame com os dados do Ticket Médio
df_ticket_medio = pd.DataFrame(ticket_medios)

# Criar a tabela com cores
st.subheader('Ticket Médio por Ano (a partir de 2020)')
st.table(df_ticket_medio.style.background_gradient(cmap='viridis'))


# Gráfico de barras
df_agrupado = df_filtrado.groupby('CLIENTE')['VALOR_RECEBIMENTO'].sum().reset_index()

# Filtra para mostrar apenas clientes acima de 150k
df_agrupado = df_agrupado[df_agrupado['VALOR_RECEBIMENTO'] > 80000]

# Cria um DataFrame com os consultores
df_consultores = df_filtrado[['CLIENTE', 'CONSULTOR']].drop_duplicates()

# Merge com o DataFrame agrupado
df_agrupado = df_agrupado.merge(df_consultores, on='CLIENTE', how='left')

fig = px.bar(
    df_agrupado,
    x='CLIENTE',
    y='VALOR_RECEBIMENTO',
    title='Vendas por Cliente (Acima de 80k)',
    color='CLIENTE',  # Define uma cor diferente para cada cliente
    barmode='group',  # Agrupa as barras para melhor visualização
)

# Ajusta a orientação do gráfico para horizontal
fig.update_layout(
    xaxis_tickangle=-45,  # Inclina os rótulos do eixo x
    title_x=0.5,  # Centraliza o título
    title_font_size=18,  # Define o tamanho da fonte do título
    width=800,  # Define a largura do gráfico (opcional)
    height=500,  # Define a altura do gráfico (opcional)
)

# Adiciona valores nas barras
fig.update_traces(
    texttemplate='%{y:.2f}R$',  # Define o formato do texto
    textposition='outside',  # Posiciona o texto fora das barras
)

# Adicionando título ao eixo y
fig.update_yaxes(title='Valor Total (R$)')

# Formata o nome do cliente para incluir o consultor
for i, a in enumerate(fig.layout.annotations):
    a.text = f"{a.text} ({df_agrupado['CONSULTOR'][i]})"

# Adiciona o nome do consultor como rótulo na barra do gráfico
fig.update_traces(
    texttemplate='%{y:.2f}R$<br>(%{customdata[0]})',
    textposition='outside',
    customdata=df_agrupado[['CONSULTOR']].values
)

st.plotly_chart(fig)

# Tabela com os dados
st.subheader('Tabela de Vendas')
st.dataframe(df_filtrado)

# Download como XLSX
buffer = io.BytesIO()
writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
df.to_excel(writer, index=False, sheet_name='Sheet1')
writer.close()  # Salva o arquivo Excel no buffer
output = buffer.getvalue()

st.download_button(
    label="Download dos dados (XLSX)",
    data=output,
    file_name='comercial.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    key='download-xlsx'
)





