import streamlit as st
st.set_page_config(page_title="BI ", 
                   layout="wide",
                    initial_sidebar_state="collapsed",
                    page_icon="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/main/src/Logomarca%20ADP%20Vs2%20(1).png"
                   )

import streamlit_authenticator as stauth
from conexao import conexaoBD
from util import cabEscala, sideBar




def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def carregar_css(file_name):
    with open(file_name) as f:
        return f.read()        
css_carregado = carregar_css("style.css")
local_css("style.css")
cabEscala()

