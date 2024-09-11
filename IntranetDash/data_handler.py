import mysql.connector
import pandas as pd


class DataHandler:
    def __init__(self, db_config):
        self.db_config = db_config
        self.df = None

    def connect_to_db(self):
        """Connect to the database and fetch the data."""
        sql_query = """ -- your SQL query here -- """
        with mysql.connector.connect(**self.db_config) as conn:
            self.df = pd.read_sql(sql_query, conn)
        self.df['VALOR_RECEBIMENTOS'] = pd.to_numeric(self.df['VALOR_RECEBIMENTOS'], errors='coerce')
        self.df['QTD_PAINEIS'] = pd.to_numeric(self.df['QTD_PAINEIS'], errors='coerce')
        return self.df

    def apply_filters(self, df, mes, ano):
        """Apply filters to the DataFrame."""
        if mes != 'Todos':
            mes_numerico = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                            'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}[mes]
            df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.month == mes_numerico]
        if ano != 2024:
            df = df[pd.to_datetime(df['DATA_PGMTO_CONFIRMADO']).dt.year == ano]
        return df

    def get_panel_count_by_type_and_state(self, df):
        """Get the count of panels by type and state."""
        filtered_df = df[df['QTD_PAINEIS'].notnull()]
        panel_count = filtered_df.groupby(['PAINEL', 'ESTADO'])['QTD_PAINEIS'].sum().unstack(fill_value=0)
        panel_count['TOTAL'] = panel_count.sum(axis=1)
        return panel_count
