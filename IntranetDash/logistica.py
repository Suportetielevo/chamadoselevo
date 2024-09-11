import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
import io
from io import BytesIO
from pandas import ExcelWriter
import xlsxwriter


class DataHandler:
    def __init__(self):
        self.db_config = {
            'host': 'monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
            'user': 'monolito',
            'password': '1642gEkdWYtQ',
            'database': 'monolito'
        }
        self.sql_query = """
        SELECT p.id as PROJETO, c.name as CLIENTE, u.name as CONSULTOR, fr.VALOR_SOMADO as VALOR_RECEBIMENTOS, 
               c2.name as CIDADE, p2.name as ESTADO, p.panel_type as PAINEL, 
               (SELECT SUM(gk.panel_count) FROM generator_kits gk
                JOIN generator_kit_projects gkp ON gk.id = gkp.generator_kit_id
                WHERE gkp.project_id = p.id) as QTD_PAINEIS, 
               GROUP_CONCAT(wp.description) as INVERSOR, l.truck_routes as ROTAS, 
               s.name as STATUS_LOGISTICA, rs.name as STATUS_FATURAMENTO, 
               IF(f2.sol_facil = 1, 'SOL FACIL', 'NAO') as SOL_FACIL, 
               DATE(t.created_at) as DATA_PGMTO_CONFIRMADO, 
               DATEDIFF(CURDATE(), l.created_at) as DIAS_DESDE_ENTROU_LOGISTICA, 
               DATE(p.created_at) as DATA_CRIACAO_PROJETO
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        JOIN franchises f ON p.franchise_id = f.id
        JOIN users u ON f.user_id = u.id
        JOIN financings f2 ON p.id = f2.project_id
        LEFT JOIN (SELECT SUM(fr.value) as VALOR_SOMADO, fr.financing_id
                   FROM financing_recipes fr
                   WHERE fr.active = 1
                   GROUP BY fr.financing_id) fr ON fr.financing_id = f2.id
        JOIN revenues r ON p.id = r.project_id
        JOIN statuses rs ON rs.id = r.status_id
        LEFT JOIN (SELECT a.created_at, a.auditable_id
                   FROM audits a
                   WHERE a.auditable_type = 'revenue' AND a.new_values LIKE '%{"status_id":"52"%'
                   GROUP BY a.auditable_id) t ON t.auditable_id = r.id
        LEFT JOIN logistics l ON p.id = l.project_id
        LEFT JOIN statuses s ON l.status_id = s.id
        JOIN cities c2 ON p.city_id = c2.id
        JOIN provinces p2 ON c2.province_id = p2.id
        LEFT JOIN generator_kit_projects gkp ON p.id = gkp.project_id
        LEFT JOIN generator_kits gk ON gkp.generator_kit_id = gk.id
        LEFT JOIN generator_kit_products g ON gk.id = g.generator_kit_id
        LEFT JOIN warehouse_products wp ON g.warehouse_product_id = wp.id AND wp.type LIKE '%inve%'
        WHERE l.status_id IN (199, 152) OR r.status_id IN (273)
        GROUP BY p.id
        ORDER BY l.created_at ASC
        """
        self.df = None

    def connect_to_db(self):
        """Connects to the MySQL database and fetches data."""
        try:
            conn = mysql.connector.connect(**self.db_config)
            self.df = pd.read_sql(self.sql_query, conn)
            conn.close()
            self.df['VALOR_RECEBIMENTOS'] = pd.to_numeric(self.df['VALOR_RECEBIMENTOS'], errors='coerce')
            self.df['QTD_PAINEIS'] = pd.to_numeric(self.df['QTD_PAINEIS'], errors='coerce')
        except mysql.connector.Error as e:
            st.error(f"Error connecting to MySQL: {e}")
            self.df = pd.DataFrame()
        return self.df

    def apply_filters(self, mes, ano, status_logistica):
        """Applies filtering to the DataFrame based on selected month, year, and logistics status."""
        df = self.df.copy()
        if mes != 'Todos':
            mes_numerico = {
                'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
            }[mes]
            df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.month == mes_numerico]
        if ano != 2024:
            df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]
        if status_logistica != 'Todos':
            df = df[df['STATUS_LOGISTICA'] == status_logistica]
        return df

    def get_panel_count_by_type_and_state(self, df):
        """Calculates and returns the count of panels for each type and state."""
        filtered_df = df[df['QTD_PAINEIS'].notnull()]
        panel_count = filtered_df.groupby(['PAINEL', 'ESTADO'])['QTD_PAINEIS'].sum().reset_index()
        return panel_count

    def get_inversor_distribution(self, df):
        """Returns the distribution of inversor types."""
        inversor_df = df['INVERSOR'].str.split(',', expand=True).stack().reset_index(drop=True, level=1).reset_index(name='INVERSOR')
        inversor_distribution = inversor_df['INVERSOR'].value_counts().reset_index()
        inversor_distribution.columns = ['INVERSOR', 'COUNT']
        return inversor_distribution


def create_bar_chart(df, x, y, color, title):
    """Creates a grouped bar chart with Altair."""
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(x, sort='-y'),
        y=y,
        color=color,
        tooltip=[x, y, color]
    ).properties(
        title=title,
        width=600,
        height=400
    ).interactive()
    return chart


def main():
    st.title('Projetos por Rotas (Logistica)')
    data_handler = DataHandler()
    df = data_handler.connect_to_db()

    if df.empty:
        st.warning("No data available.")
        return

    st.sidebar.header("Filtros Pag.Confirmados")
    mes = st.sidebar.selectbox(
        "Selecione o Mês",
        ['Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
         'Novembro', 'Dezembro'],
        index=0
    )
    ano = st.sidebar.slider("Selecione o Ano", min_value=2020, max_value=2024, value=2024)
    status_logistica = st.sidebar.selectbox(
        "Selecione o Status de Logística",
        ['Todos'] + df['STATUS_LOGISTICA'].unique().tolist()
    )

    df_filtered = data_handler.apply_filters(mes, ano, status_logistica)

    # Chart: Panel Count by Type and State
    st.header("Quantidade de Painéis Vendidos por Tipo e Estado")
    panel_count_by_type_and_state = data_handler.get_panel_count_by_type_and_state(df_filtered)
    st.dataframe(panel_count_by_type_and_state)

    panel_chart = create_bar_chart(panel_count_by_type_and_state, 'ESTADO', 'QTD_PAINEIS', 'PAINEL', "Total de Painéis por Tipo e Estado")
    st.altair_chart(panel_chart)

    # Tabela: Distribuição dos Inversores
    st.header("Distribuição dos Tipos de Inversores")
    inversor_distribution = data_handler.get_inversor_distribution(df_filtered)
    st.dataframe(inversor_distribution)

    # Display filtered DataFrame
    st.header("Dados Filtrados")
    st.dataframe(df_filtered)

    # Download the data as XLSX
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()

    buffer.seek(0)
    st.download_button(
        label="Download dos dados (XLSX)",
        data=buffer,
        file_name='logistica.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='download-xlsx'
    )


if __name__ == "__main__":
    main()