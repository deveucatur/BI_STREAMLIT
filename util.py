import streamlit as st

def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Aplicar o CSS personalizado
local_css("style.css")

def sideBar():
    st.sidebar.page_link("Home.py")
    st.sidebar.page_link("pages/1 - BI Sindicancia.py")
    st.sidebar.page_link("pages/1 - BI Pagamentos.py")
    
def cabEscala(nome):
    st.markdown(""" 
    <div class="topo">
        <div class="logo">
            <img src="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/main/src/Logomarca%20ADP%20Vs2.png" >
            <span>{}</span>
        </div>
    </div>
"""  
   .format(nome), unsafe_allow_html=True)
    
def cabEscala1(nome):
    st.markdown(""" 
    <div class="topo">
        <div class="logo">
            <img >
            <span>{}</span>
        </div>
    </div>
"""  
   .format(nome), unsafe_allow_html=True)