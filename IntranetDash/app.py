import streamlit as st
from database import BancoDeDados
from data_processor import Dados
from dashboard import Dashboard

def main():
    st.set_page_config(
        page_title="Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database connection with production credentials
    bd = BancoDeDados(
        host="monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com",
        user="monolito",
        password="1642gEkdWYtQ",
        database="monolito"
    )
    
    try:
        # Create dashboard instance
        dashboard = Dashboard(bd)
        # Load data and display dashboard
        dashboard.carregar_dados()
        dashboard.exibir_dashboard()
    except Exception as e:
        st.error(f"Erro ao carregar o dashboard: {str(e)}")
    finally:
        bd.fechar_conexao()

if __name__ == "__main__":
    main()