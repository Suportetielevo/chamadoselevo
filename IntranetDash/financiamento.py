import streamlit as st
import mysql.connector
import pandas as pd
import io
from pandas import ExcelWriter
import xlsxwriter


class DataHandler:
    def __init__(self):
        # Conexão com o banco de dados
        self.db_config = {
            'host': 'monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
            'user': 'monolito',
            'password': '1642gEkdWYtQ',
            'database': 'monolito'
        }

        # Consulta SQL específica para financiamentos
        self.query = """
        SELECT p.id                                   AS PROJETO,
               c.name                                 AS CLIENTE,
               frm.label                              AS TIPO_RECEBIMENTO,
               fr.value                               AS VALOR,
               u.name                                 AS CARTEIRA,
               IFNULL(frs.name, 'SEM STATUS')         AS STATUS_ATUAL,
               CASE
                   WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) = '{'
                       THEN 'Vencimento não cadastrado'
                   WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) IS NULL
                       THEN 'Vencimento não cadastrado'
                   WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) IS NULL AND frm.id = 2
                       THEN 'À VISTA'
                   WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) IS NULL AND frm.id = 6
                       THEN 'CARTÃO'
                   WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) =
                        SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1)
                       THEN DATE_FORMAT(SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1), '%d/%m/%Y')
               END                                AS DATA_VENCIMENTO,
               IFNULL(DATEDIFF(CURDATE(), SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1)),
                      'SEM_VENCIMENTO')               AS DATA_DESDE_VENCIMENTO,
               DATE_FORMAT(fr.created_at, '%d/%m/%Y') AS DATA_CRIADO_RECEBIMENTO
        FROM projects p
                 JOIN financings f ON p.id = f.project_id
                 JOIN users u ON f.user_id = u.id
                 JOIN financing_recipes fr ON f.id = fr.financing_id AND fr.active = 1
                 JOIN financing_recipe_methods frm ON fr.financing_recipe_method_id = frm.id
                 JOIN clients c ON p.client_id = c.id
                 LEFT JOIN financing_recipe_statuses frs ON fr.financing_recipe_status_id = frs.id
                 JOIN revenues r ON p.id = r.project_id AND r.status_id = 52
                 LEFT JOIN (SELECT a.created_at, a.auditable_id
                            FROM audits a
                            WHERE a.auditable_type = 'revenue'
                              AND a.new_values LIKE '%{"status_id":"52"%') t ON t.auditable_id = r.id
        WHERE (fr.financing_recipe_status_id NOT IN (5, 15, 16, 17, 18, 21, 25, 27, 28, 29, 30, 32, 36, 37, 38)
              AND f.status_id NOT IN (123)
              AND DATEDIFF(CURDATE(), SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1)) >= 0)
           OR (fr.financing_recipe_status_id NOT IN (5, 15, 16, 17, 18, 21, 25, 27, 28, 29, 30, 32, 36, 37, 38)
              AND f.status_id NOT IN (123)
              AND SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) = '{')
           OR (fr.financing_recipe_status_id NOT IN (5, 15, 16, 17, 18, 21, 25, 27, 28, 29, 30, 32, 36, 37, 38)
              AND f.status_id NOT IN (123)
              AND SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) IS NULL)
           OR (fr.financing_recipe_status_id IS NULL
              AND f.status_id NOT IN (123)
              AND DATEDIFF(CURDATE(), SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1)) >= 0)
           OR (fr.financing_recipe_status_id IS NULL
              AND f.status_id NOT IN (123)
              AND SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) = '{')
           OR (fr.financing_recipe_status_id IS NULL
              AND f.status_id NOT IN (123)
              AND SUBSTRING_INDEX(SUBSTRING_INDEX(fr.properties, 'date": "', -1), '"', 1) IS NULL)
        ORDER BY fr.created_at
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

    def apply_filters(self, mes):
        """Aplica filtros ao DataFrame com base no mês selecionado."""
        if mes != 'Todos':
            mes_numerico = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                            'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}[mes]
            self.df = self.df[pd.to_datetime(self.df['DATA_CRIADO_RECEBIMENTO'], format='%d/%m/%Y').dt.month == mes_numerico]
        return self.df


def main():
    data_handler = DataHandler()
    df = data_handler.connect_to_db()

    st.title('Relatório de Financiamentos')

    st.sidebar.header("Filtros")

    # Seleção do mês
    mes = st.sidebar.selectbox(
        "Selecione o Mês",
        ('Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'),
        index=10
    )
    df = data_handler.apply_filters(mes)

    # Filtra apenas projetos com data de recebimento confirmada
    df = df[~df['DATA_CRIADO_RECEBIMENTO'].isna()]

    # Exibir valores únicos e quantidades na coluna STATUS_ATUAL
    status_counts = df['STATUS_ATUAL'].value_counts()
    st.write("Valores únicos na coluna STATUS_ATUAL com quantidades:")
    st.dataframe(status_counts)

    # Calcula a quantidade de projetos enviados para aprovação
    projetos_aprovacao = df[df['STATUS_ATUAL'].str.contains('Aprovação', na=False, case=False)]
    st.metric("📤 Projetos Enviados para Aprovação", len(projetos_aprovacao))

    # Quantidade de projetos por carteira de atendente
    carteira_projetos = df.groupby('CARTEIRA')['PROJETO'].nunique().reset_index()
    carteira_projetos.rename(columns={'PROJETO': 'Quantidade de Projetos'}, inplace=True)

    st.subheader("💼 Quantidade de Projetos por Carteira")
    st.dataframe(carteira_projetos)

    # Exibir a tabela original
    st.subheader("📊 Tabela Completa")
    st.dataframe(df)

    # Download como XLSX
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        carteira_projetos.to_excel(writer, index=False, sheet_name='Por_Carteira')
        writer.close()
    output = buffer.getvalue()

    st.download_button(
        label="⬇️ Download dos dados (XLSX)",
        data=output,
        file_name='relatorio_financiamentos.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='download-xlsx'
    )

if __name__ == "__main__":
    main()

