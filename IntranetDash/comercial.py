import mysql.connector
import pandas as pd
import plotly.express as px
import io
from pandas import ExcelWriter
import xlsxwriter
import streamlit as st
from datetime import datetime


class BancoDeDados:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def conectar(self):
        """Conecta ao banco de dados."""
        self.conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()

    def buscar_dados(self, query):
        """Executa a consulta SQL e retorna os dados em um DataFrame."""
        if not self.cursor:
            self.conectar()
        self.cursor.execute(query)
        dados = self.cursor.fetchall()
        df = pd.DataFrame(dados, columns=[desc[0] for desc in self.cursor.description])
        return df

    def fechar_conexao(self):
        """Fecha a conexão com o banco de dados."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


class Dados:
    def __init__(self, df):
        self.df = df
        self.df['VALOR_RECEBIMENTO'] = pd.to_numeric(self.df['VALOR_RECEBIMENTO'], errors='coerce')
        self.df['DATA_PGMTO_CONFIRMADO'] = pd.to_datetime(self.df['DATA_PGMTO_CONFIRMADO'])
        self.df['QTD_PAINEIS'] = pd.to_numeric(self.df['QTD_PAINEIS'], errors='coerce')

    def filtrar_dados(self, ano_selecionado, mes_selecionado):
        """Filtra os dados com base no ano e mês selecionados."""
        if mes_selecionado == "Todos":
            return self.df[self.df['DATA_PGMTO_CONFIRMADO'].dt.year == ano_selecionado]
        else:
            return self.df[
                (self.df['DATA_PGMTO_CONFIRMADO'].dt.year == ano_selecionado) &
                (self.df['DATA_PGMTO_CONFIRMADO'].dt.month == mes_selecionado)
                ]

    def calcular_indicadores(self, df_filtrado):
        """Calcula os indicadores de faturamento, ticket médio e clientes atendidos."""
        faturamento_total = df_filtrado['VALOR_RECEBIMENTO'].sum()
        ticket_medio = df_filtrado['VALOR_RECEBIMENTO'].mean()
        clientes_atendidos = df_filtrado['CLIENTE'].nunique()
        return faturamento_total, ticket_medio, clientes_atendidos

    def calcular_ticket_medio_por_ano(self, ano_inicio=2020):
        """Calcula o ticket médio por ano a partir de um ano inicial."""
        anos = range(ano_inicio, datetime.now().year + 1)
        ticket_medios = []
        for ano in anos:
            df_ano = self.df[self.df['DATA_PGMTO_CONFIRMADO'].dt.year == ano]
            ticket_medio_ano = df_ano['VALOR_RECEBIMENTO'].mean()
            ticket_medios.append({'Ano': ano, 'Ticket Médio': f'R$ {ticket_medio_ano:,.2f}'})
        return pd.DataFrame(ticket_medios)

    def agrupar_vendas_por_cliente(self, df_filtrado, valor_minimo=80000):
        """Agrupa as vendas por cliente, filtrando por um valor mínimo."""
        df_agrupado = df_filtrado.groupby('CLIENTE')['VALOR_RECEBIMENTO'].sum().reset_index()
        df_agrupado = df_agrupado[df_agrupado['VALOR_RECEBIMENTO'] > valor_minimo]
        df_consultores = df_filtrado[['CLIENTE', 'CONSULTOR']].drop_duplicates()
        df_agrupado = df_agrupado.merge(df_consultores, on='CLIENTE', how='left')
        return df_agrupado

    def criar_grafico_vendas_por_cliente(self, df_agrupado):
        """Cria um gráfico de barras mostrando as vendas por cliente."""
        fig = px.bar(
            df_agrupado,
            x='CLIENTE',
            y='VALOR_RECEBIMENTO',
            title='Vendas por Cliente (Acima de 80k)',
            color='CLIENTE',
            barmode='group'
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            title_x=0.5,
            title_font_size=18,
            width=800,
            height=500,
        )

        fig.update_traces(
            texttemplate='%{y:.2f}R$',
            textposition='outside',
            customdata=df_agrupado[['CONSULTOR']].values
        )

        fig.update_yaxes(title='Valor Total (R$)')

        return fig


class Dashboard:
    def __init__(self):
        self.bd = BancoDeDados(
            host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
            user='monolito',
            password='1642gEkdWYtQ',
            database='monolito'
        )
        self.dados = None

    def carregar_dados(self):
        """Carrega os dados do banco de dados."""
        query = """
            select p.id              as ID_PROJETO,
       c.name               as CLIENTE,
       c2.name              as CIDADE_CLIENTE,
       p2.name              as ESTADO_CLIENTE,
       u.name               as CONSULTOR,
       u2.name              as CONSULTOR_EXTERNO,
       ppt.description      as FORMA_DE_PAGAMENTO,
       fr.VALOR_SOMADO      as VALOR_RECEBIMENTO,
       DATE(t2.created_at)  as DATA_ASSINADO,
       DATE(pi.created_at)  as DATA_PGMTO_CONFIRMADO,
       p.panel_type                               as PAINEL,
       (select sum(gk.panel_count)
        from generator_kits gk
             join generator_kit_projects gkp on gk.id = gkp.generator_kit_id
        where gkp.project_id = p.id)              as QTD_PAINEIS,
       (select group_concat(gk.description)
        from generator_kits gk
             join generator_kit_projects gkp on gk.id = gkp.generator_kit_id
        where gkp.project_id = p.id)              as DESCRICAO_INVERSORES
        
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
order by pi.created_at;

        """
        self.dados = Dados(self.bd.buscar_dados(query))

    def exibir_dashboard(self):
        """Exibe o dashboard no Streamlit."""
        st.title('Vendas Totais - Dep. Comercial')

        ano_atual = datetime.now().year
        mes_atual = datetime.now().month

        # Opção "Todos" para os anos
        anos_unicos = self.dados.df['DATA_PGMTO_CONFIRMADO'].dt.year.unique()
        anos_selecao = ["Todos"] + list(anos_unicos)
        ano_selecionado = st.sidebar.selectbox('Selecione o ano:', anos_selecao, index=len(anos_selecao) - 1)

        mes_selecionado = st.sidebar.selectbox('Selecione o mês:', ["Todos"] + list(range(1, 13)), index=mes_atual)

        if ano_selecionado == "Todos":
            df_filtrado = self.dados.df
        else:
            df_filtrado = self.dados.filtrar_dados(ano_selecionado, mes_selecionado)

        faturamento_total, ticket_medio, clientes_atendidos = self.dados.calcular_indicadores(df_filtrado)

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

        df_ticket_medio = self.dados.calcular_ticket_medio_por_ano()
        st.subheader('Ticket Médio por Ano (a partir de 2020)')
        st.table(df_ticket_medio.style.background_gradient(cmap='viridis'))

        df_agrupado = self.dados.agrupar_vendas_por_cliente(df_filtrado)
        fig = self.dados.criar_grafico_vendas_por_cliente(df_agrupado)
        st.plotly_chart(fig)

        st.subheader('Tabela de Vendas')
        st.dataframe(df_filtrado)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.close()
        output = buffer.getvalue()

        st.download_button(
            label="Download dos dados (XLSX)",
            data=output,
            file_name='comercial.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='download-xlsx'
        )

        # ---- Consultor Interno ----
        st.header('Relatório de Consultores')
        st.write('Dados dos Consultores:  ')

        st.subheader('Consultor Interno')
        query_consultor_interno = """
            select f.id                                    as ID_CONSULTOR,
                   concat(u.name, ' (', f.nickname, ')')   as CONSULTOR,
                   c2.name                                 as CIDADE_CONSULTOR,
                   p2.name                                 as ESTADO_CONSULTOR,
                   ifnull(f.mobile_number, f.phone_number) as CELULAR_CONSULTOR,
                   (select sum(fr.VALOR_SOMADO))           as VALOR_RECEBIMENTO,
                   (select count(distinct (r.id)))         as QTD_PROJETOS_PGMTO
            from projects p
                 join franchises f on p.franchise_id = f.id
                 join users u on f.user_id = u.id
                 join cities c2 on f.city_id = c2.id
                 join provinces p2 on c2.province_id = p2.id
                 join financings f2 on p.id = f2.project_id
                 left join (select sum(fr.value) as VALOR_SOMADO, fr.id, fr.financing_id
                            from financing_recipes fr
                            where fr.active = 1
                            group by fr.financing_id) fr on fr.financing_id = f2.id
                 join revenues r on p.id = r.project_id
                 join (select project_id,
                              MIN(created_at) AS pagamento_data
                       FROM project_interactions
                       WHERE type = 'status_change'
                         AND comment = 'PAGAMENTO CONFIRMADO'
                       GROUP BY project_id) pagamento ON pagamento.project_id = r.project_id
            where p.outsider_franchise_id is null
              and pagamento.pagamento_data between '2025-01-01 00:00:00' and '2025-12-31 23:59:59'
              and f2.status_id not in (123)
            group by p.franchise_id
            order by VALOR_RECEBIMENTO desc
        """
        df_consultor_interno = self.bd.buscar_dados(query_consultor_interno)
        st.dataframe(df_consultor_interno)

        buffer_interno = io.BytesIO()
        with pd.ExcelWriter(buffer_interno, engine='xlsxwriter') as writer:
            df_consultor_interno.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.close()
        output_interno = buffer_interno.getvalue()

        st.download_button(
            label="Download Relatório Consultor Interno (XLSX)",
            data=output_interno,
            file_name='consultor_interno.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='download-interno'
        )

        # ---- Consultor Externo ----
        st.subheader('Consultor Externo desde 2020 ')
        query_consultor_externo = """
            SELECT
    CONCAT(u.name, ' (', f.nickname, ')') AS CONSULTOR,
    c2.name AS CIDADE_CONSULTOR,
    p2.name AS ESTADO_CONSULTOR,
    IFNULL(f.mobile_number, f.phone_number) AS CELULAR_CONSULTOR,
    SUM(fr.VALOR_SOMADO) AS VALOR_RECEBIMENTO,
    COUNT(DISTINCT r.id) AS QTD_PROJETOS_PGMTO
FROM projects p
    JOIN outsider_franchises f ON p.outsider_franchise_id = f.id
    JOIN users u ON f.user_id = u.id
    JOIN cities c2 ON f.city_id = c2.id
    JOIN provinces p2 ON c2.province_id = p2.id
    JOIN financings f2 ON p.id = f2.project_id
    LEFT JOIN (
        SELECT
            fr.financing_id,
            SUM(fr.value) AS VALOR_SOMADO
        FROM financing_recipes fr
        WHERE fr.active = 1
        GROUP BY fr.financing_id
    ) fr ON fr.financing_id = f2.id
    JOIN revenues r ON p.id = r.project_id
    JOIN (
        SELECT
            project_id,
            MIN(created_at) AS pagamento_data
        FROM project_interactions
        WHERE type = 'status_change'
            AND comment = 'PAGAMENTO CONFIRMADO'
        GROUP BY project_id
    ) pagamento ON pagamento.project_id = r.project_id
WHERE pagamento.pagamento_data BETWEEN '2020-01-01 00:00:00' AND '2025-12-30 23:59:59'
    AND f2.status_id NOT IN (123)
GROUP BY CONSULTOR
ORDER BY VALOR_RECEBIMENTO DESC;
        """
        df_consultor_externo = self.bd.buscar_dados(query_consultor_externo)
        st.dataframe(df_consultor_externo)

        buffer_externo = io.BytesIO()
        with pd.ExcelWriter(buffer_externo, engine='xlsxwriter') as writer:
            df_consultor_externo.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.close()
        output_externo = buffer_externo.getvalue()

        st.download_button(
            label="Download Relatório Consultor Externo (XLSX)",
            data=output_externo,
            file_name='consultor_externo.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='download-externo'
        )


if __name__ == '__main__':
    dashboard = Dashboard()
    dashboard.carregar_dados()
    dashboard.exibir_dashboard()