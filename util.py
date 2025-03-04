import streamlit as st

def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Aplicar o CSS personalizado
local_css("style.css")

# def sideBar():
    
    
    

def sideBar(current_page):
  
    if current_page == "BI Pagamentos":
       st.sidebar.page_link("pages/2 - BI Pagamentos.py")
       
      
    elif current_page == "BI Sindicância":
      st.sidebar.page_link("Home.py")

    elif current_page == "BI Cadeia de valor":
        st.sidebar.page_link("pages/3 - BI Cadeia de Valor.py")
      
    elif current_page == "Home":
        st.sidebar.write("🔒 Home")
      
    
    
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