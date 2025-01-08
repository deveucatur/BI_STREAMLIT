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

conexao = conexaoBD()

mycursor = conexao.cursor()
setSession = "SET SESSION group_concat_max_len = 5000;"
mycursor.execute(setSession)

comandUSERS = """SELECT 
        projeu_users.*,
        (
            SELECT
                macroprocesso
            FROM 
                projeu_macropr
            WHERE 
                id = projeu_users.macroprocesso_fgkey
        ) 
    FROM 
        projeu_users 
    WHERE 
        perfil_proj IN ("A", "GV", "AS", "L");"""
mycursor.execute(comandUSERS)
dadosUser = mycursor.fetchall()
mycursor.close()


names = [x[2] for x in dadosUser]

usernames = [x[3] for x in dadosUser]
hashed_passwords = [x[7] for x in dadosUser]

def convert_to_dict(names, usernames, passwords):
    credentials = {"usernames": {}}
    for name, username, password in zip(names, usernames, passwords):
        user_credentials = {
            "email":username,
            "name": name,
            "password": password
        }
        credentials["usernames"][username] = user_credentials
    return credentials

credentials = convert_to_dict(names, usernames, hashed_passwords)
authenticator = stauth.Authenticate(credentials, "Teste", "abcde", cookie_expiry_days=30)

col1, col2,col3 = st.columns([1,3,1])
with col2:
    name, authentication_status, username = authenticator.login(
        location='main', fields={
            'Form name':'Acessar BI sindicancia',
            'Username':'Login', 
            'Password':'Senha', 
            'Login':'Entrar'
            })

if authentication_status == False:
    with col2:
        st.error('Email ou Senha Incorreto')
elif authentication_status == None:
    with col2:
        st.warning('Insira seu Email e Senha')
else:
    authenticator.logout('Logout', 'sidebar')  

