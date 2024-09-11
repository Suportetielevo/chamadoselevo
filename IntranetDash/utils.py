import streamlit as st
from streamlit_option_menu import option_menu

# 1=sidebar menu, 2=horizontal menu, 3=horizontal menu w/ custom menu
EXAMPLE_NO = 1

def streamlit_menu(example=1):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Intranet",  # required
                options=["Visão Geral", "Análise", "Comparativos", "Previsões", "Alertas", "Configurações"],  # required
                icons=[],  # optional
                menu_icon="globe",  # optional
                default_index=0,  # optional
            )
        return selected

selected = streamlit_menu(example=EXAMPLE_NO)

if selected == "Visão Geral":
    st.title(f"{selected}  ( Análise Rápida )")

#####################
if selected == "Análise":
    st.title(f"{selected} ( Gráficos e Tabelas  )")

######################
if selected == "Comparativos":
    st.title(f"{selected} ( Períodos, Regiões, Grupos )")

######################
if selected == "Previsões":
    st.title(f"{selected} ( Projeções Futuras )")

######################
if selected == "Alertas":
    st.title(f"{selected} ( Eventos e Metas ou indicadores )")

####################
if selected == "Configurações":
    st.title(f"{selected} ( Filtros e Outras )")