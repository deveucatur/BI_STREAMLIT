import streamlit as st
import streamlit_authenticator as stauth

names = ["victor"]
usernames = ["pedrotivictor712@gmail.com"]
hashed_passwords = stauth.Hasher(["Jesusebom712"]).generate() 

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
authenticator = stauth.Authenticate(
    credentials,
    "victor_cookie",         # Chave do cookie
    "nome_cookie",           # Nome do cookie
    cookie_expiry_days=30    # Expiração do cookie
)

col1, col2,col3 = st.columns([1,3,1])
with col2:
    name, authentication_status, username = authenticator.login(location='main', fields={'Form name':'Acessar PROJEU', 'Username':'Login', 'Password':'Senha', 'Login':'Entrar'})

if authentication_status == False:
    with col2:
        st.error('Email ou Senha Incorreto')
elif authentication_status == None:
    with col2:
        st.warning('Insira seu Email e Senha')
else:
    authenticator.logout('Logout', 'sidebar')    