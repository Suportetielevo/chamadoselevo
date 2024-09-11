import streamlit as st
import mysql.connector
import pandas as pd
import io
from pandas import ExcelWriter
import xlsxwriter

class DataHandler:
    def __init__(self):
        # Conexão com o banco de dados usando secrets
        self.db_config = {
            'host': st.secrets["database"]["host"],
            'user': st.secrets["database"]["user"],
            'password': st.secrets["database"]["password"],
            'database': st.secrets["database"]["database"]
        }

        # Consulta SQL sem filtro de data
        self.query = """
        SELECT p.id                                            AS ID_PROJETO,
               c.name                                          AS CLIENTE,
               u.name                                          AS HOMOLOGADOR_ATUAL,
               u3.name                                         AS ADMINISTRADORA_ATUAL,
               u4.name                                         AS OPERADOR_ATUAL,
               s.name                                          AS STATUS_ATUAL,
               DATE_FORMAT(pi.created_at, '%d/%m/%Y %H:%i:%s') AS DATA,
               u2.name                                         AS 'QUEM COMENTOU OU ALTEROU STATUS',
               CASE
                   WHEN pi.type = 'status_change' THEN 'ALTEROU STATUS PARA:'
                   WHEN pi.type = 'comment' THEN 'COMENTOU:'
                   END                                         AS 'AÇÃO',
               fnStripTags(pi.comment)                         AS 'COMENTÁRIOS/ALTERAÇÃO DE STATUS'
        FROM projects p
                 JOIN clients c ON c.id = p.client_id
                 JOIN homolagations h ON h.project_id = p.id
                 LEFT JOIN users u ON u.id = h.engineer_user_id
                 JOIN statuses s ON s.id = h.status_id
                 JOIN project_interactions pi ON pi.project_id = p.id
                 LEFT JOIN users u2 ON u2.id = pi.user_id
                 LEFT JOIN users u3 ON h.homologation_administrator_id = u3.id
                 LEFT JOIN users u4 ON h.user_id = u4.id
        WHERE (pi.type = 'comment' AND pi.department_id = 3)
           OR (pi.type = 'status_change' AND pi.department_id = 3)
        GROUP BY pi.id, s.name, c.name
        ORDER BY pi.created_at
        """

        self.df = None

    def connect_to_db(self):
        """Conecta ao banco de dados e recupera os dados."""
        try:
            with mysql.connector.connect(**self.db_config) as conn:
                self.df = pd.read_sql(self.query, conn)
        except mysql.connector.Error as e:
            st.error(f"Erro ao conectar ao MySQL: {e}")
            self.df = pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
        return self.df

    def apply_filters(self, mes, ano, status):
        """Aplica filtros ao DataFrame com base no mês, ano e status selecionados."""
        if mes != 'Todos':
            mes_numerico = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                            'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}[mes]
            self.df = self.df[(pd.to_datetime(self.df['DATA'], format='%d/%m/%Y %H:%M:%S').dt.month == mes_numerico) &
                              (pd.to_datetime(self.df['DATA'], format='%d/%m/%Y %H:%M:%S').dt.year == ano)]

        if status != 'Todos':
            self.df = self.df[self.df['STATUS_ATUAL'] == status]

        return self.df


def main():
    data_handler = DataHandler()
    df = data_handler.connect_to_db()

    st.title('Relatório de Homologação')

    st.sidebar.header("Filtros")

    # Seleção do mês e ano
    mes = st.sidebar.selectbox(
        "Selecione o Mês",
        ('Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
         'Novembro', 'Dezembro'),
        index=8
    )
    ano = st.sidebar.selectbox(
        "Selecione o Ano",
        sorted(df['DATA'].apply(lambda x: pd.to_datetime(x, format='%d/%m/%Y %H:%M:%S').year).unique(), reverse=True)
    )

    status = st.sidebar.selectbox(
        "Selecione o Status",
        ['Todos'] + df['STATUS_ATUAL'].unique().tolist()
    )

    df = data_handler.apply_filters(mes, ano, status)

    # Filtra apenas projetos com data confirmada
    df = df[~df['DATA'].isna()]

    # Contagem de clientes distintos
    clientes_distintos = df['CLIENTE'].nunique()

    st.write(f"Número de clientes distintos: {clientes_distintos}")

    # Exibir a tabela
    st.dataframe(df)

    # Download como XLSX
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
    output = buffer.getvalue()

    st.download_button(
        label="Download dos dados (XLSX)",
        data=output,
        file_name='homologacao.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='download-xlsx'
    )


if __name__ == "__main__":
    main()



