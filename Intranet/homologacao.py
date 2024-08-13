import streamlit as st
from streamlit_option_menu import option_menu

# 1=sidebar menu, 2=horizontal menu, 3=horizontal menu w/ custom menu
EXAMPLE_NO = 1

def streamlit_menu(example=1):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Intranet Compras",  # required
                options=["Formulários", "Relatorios", "Gráficos"],  # required
                icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
                menu_icon="globe",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Formulários", "Relatorios", "Gráficos"],  # required
            icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
            menu_icon="battery-charging",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    if example == 3:
        # 2. horizontal menu with custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Formulários", "Relatorios", "Gráficos"],  # required
            icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
            menu_icon="battery-charging",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected


selected = streamlit_menu(example=EXAMPLE_NO)

if selected == "Formulários":
    st.title(f"Sua Seleção {selected}")
if selected == "Relatorios":
    st.title(f"Sua Seleção {selected}")
if selected == "Gráficos":
    st.title(f"Sua Seleção {selected}")




# 1=sidebar menu, 2=horizontal menu, 3=horizontal menu w/ custom menu
EXAMPLE_NO = 1

def streamlit_menu(example=1):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Intranet Compras",  # required
                options=["Formulários", "Relatorios", "Gráficos"],  # required
                icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
                menu_icon="globe",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Formulários", "Relatorios", "Gráficos"],  # required
            icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
            menu_icon="battery-charging",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    if example == 3:
        # 2. horizontal menu with custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Formulários", "Relatorios", "Gráficos"],  # required
            icons=["ui-checks-grid", "book", "bar-chart-fill"],  # optional
            menu_icon="battery-charging",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected


selected = streamlit_menu(example=EXAMPLE_NO)

if selected == "Formulários":
    st.title(f"Sua Seleção {selected}")
