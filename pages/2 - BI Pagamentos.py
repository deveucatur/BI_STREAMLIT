import streamlit as st
st.set_page_config(page_title="BI Pagamentos", 
                   layout="wide",
                    initial_sidebar_state="collapsed",
                    page_icon="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/main/src/Logomarca%20ADP%20Vs2%20(1).png"
                   )

import pandas as pd
import plotly.express as px
from datetime import datetime
import json
from wordcloud import WordCloud, STOPWORDS
import requests
from requests_oauthlib import OAuth1
import os
from dotenv import load_dotenv 
from util import cabEscala, sideBar
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader





# Configurações iniciais


def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def carregar_css(file_name):
    with open(file_name) as f:
        return f.read()        

# Aplicar o CSS personalizado
css_carregado = carregar_css("stylesPag.css")
local_css("stylesPag.css")
cabEscala()




names = ['Victor Silva','Cleidimara Sander','Bruna Paio de Medeiros']
usernames = ['pedrotivictor712@gmail.com','cleidi.sander@gmail.com' ,'performance.eucatur@gmail.com']
hashed_passwords = ['admin','admin','admin']

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



    @st.cache_data(ttl=600)
    def load_data_from_api():
        load_dotenv()
        # Credenciais OAuth (substitua pelas suas credenciais de forma segura)
        oauth_consumer_key = os.getenv("oauth_consumer_key")
        oauth_consumer_secret = os.getenv("oauth_consumer_secret")
        oauth_token = os.getenv("oauth_token")
        oauth_token_secret = os.getenv("oauth_token_secret")

        # Verifica se as credenciais estão disponíveis
        if not all([oauth_consumer_key, oauth_consumer_secret, oauth_token, oauth_token_secret]):
            st.error("Credenciais OAuth não encontradas. Verifique suas variáveis de ambiente.")
            return None

        oauth = OAuth1(
            oauth_consumer_key,
            client_secret=oauth_consumer_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            signature_method='HMAC-SHA1'
        )

        url = "http://134.65.49.113:8080/process-management/api/v2/requests"
        params = {
            "status": ["OPEN", "FINALIZED"],
            "processId": "ARF-SolicitaçãodePagamentoAntecipado",
            "page": 1,
            "pageSize": 1000,
            "expand": "formFields"
        }

        response = requests.get(url, auth=oauth, params=params)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            st.error(f"Erro {response.status_code}: {response.reason}")
            return None

    # Carregar dados da API
    data = load_data_from_api()

    if data is not None:
        # Supondo que os registros estão na chave 'requests' ou 'items'
        records_list = data.get('requests', data.get('items', data))

        # Verificar se records_list é uma lista
        if not isinstance(records_list, list):
            st.error("Estrutura de dados inesperada. 'records_list' não é uma lista.")
        else:
            # Flatten dos dados e transformação em DataFrame
            records = []
            for record in records_list:
                if isinstance(record, dict):
                    flat_record = record.copy()
                    form_fields = {item['field']: item['value'] for item in record.get('formFields', [])}
                    flat_record.update(form_fields)
                    flat_record.pop('formFields', None)
                    records.append(flat_record)
                else:
                    st.warning(f"Registro ignorado por não ser um dicionário: {record}")

            df = pd.DataFrame(records)
          

            df['startDate'] = pd.to_datetime(df['startDate'], errors='coerce')
            df['endDate'] = pd.to_datetime(df['endDate'], errors='coerce')
            df['startDate'] = df['startDate'].dt.tz_localize(None)
            df['endDate'] = df['endDate'].dt.tz_localize(None)
            df['lead_time'] = ((df['endDate'].fillna(datetime.now()) - df['startDate']).dt.total_seconds() / 3600) / 24 
            df['status'] = df['status'].str.lower().map({'open': 'Aberto', 'finalized': 'Finalizado'}) 
            df['slaStatus'] = df['slaStatus'].str.lower().map({'on_time': 'No Prazo', 'overdue': 'Em Atraso'})
            st.write(df)
            with st.expander("Filtros"):
                

                def multiselect_with_all(label, options):
                    """Função para criar um multiselect com a opção 'Todos'."""
                    all_label = "Todos"
                    selected = st.multiselect(label, [all_label] + list(options), default=[all_label])
                    if all_label in selected:
                        return list(options)  # Retorna todas as opções se 'Todos' estiver selecionado
                    return selected
            

                colsta1, colsta2,colsta3 = st.columns(3)
                with colsta1:
                    status_filter = multiselect_with_all("Status", df['status'].dropna().unique())
                with colsta2:    
                    sla_filter = multiselect_with_all("Status do SLA", df['slaStatus'].dropna().unique())
                with colsta3:     
                    empresa_filter = multiselect_with_all("Empresa", df['empresaPagamento'].dropna().unique())
                colsta4, colsta5 = st.columns(2)
                with colsta4:
                    unidade_filter = multiselect_with_all("Unidade", df['unidadeSolicitante'].unique())
                    #regiao_filter = multiselect_with_all("Região", df['regiaoUnidade'].dropna().unique())
                with colsta5: 
                    solicitante_filter = multiselect_with_all("Solicitante", df['nomeSolicitante'].dropna().unique())

                #cidade_filter = multiselect_with_all("Cidade", df['cidadeFato'].dropna().unique())
                
                colsta6, colsta7,colsta8 = st.columns(3)
                with colsta6:
                    medida_filter = multiselect_with_all("Medida Corretiva", df['tpPagamento'].dropna().unique())
                with colsta7:
                    start_date_default  = df['startDate'].min().date() 
                    end_date_default = datetime.today().date()    
                        
                    start_date = st.date_input("Data Inicial", start_date_default)           
                with colsta8:
                
                    end_date = st.date_input("Data Final",end_date_default)
                    
                #irregularidade_filter = multiselect_with_all("Irregularidade", df['irregularidade'].dropna().unique())
                
                #investigado_filter = multiselect_with_all("Investigado", df['nmInvestigado'].dropna().unique()) 
            
            #end_date = datetime.today().date()
            # df = df[
            # (df['startDate'] >= pd.Timestamp(start_date)) &
            # (
            #     (df['endDate'].isna() & (df['startDate'] <= pd.Timestamp(end_date))) |  # Valores nulos, mas dentro do intervalo
            #     (df['endDate'] <= pd.Timestamp(end_date))  # Valores não nulos dentro do intervalo
            # )
            # ]
            
            

            # Aplicar filtros
            filtered_df = df[
                (df['status'].isin(status_filter)) &
                (df['slaStatus'].isin(sla_filter)) &
                #(df['cidadeFato'].isin(cidade_filter)) &
                (df['unidade'].isin(unidade_filter)) &
                #(df['regiaoUnidade'].isin(regiao_filter)) &
                (df['mddCorretSelecionada'].isin(medida_filter)) &
                #(df['irregularidade'].isin(irregularidade_filter)) &
                #(df['gravidadeMaxima'].isin(gravidade_filter)) &
                #(df['nmInvestigado'].isin(investigado_filter)) &
                (df['solicitante'].isin(solicitante_filter)) &
                (df['startDate'] >= pd.Timestamp(start_date)) &
                (
                (df['endDate'].isna() & (df['startDate'] <= pd.Timestamp(end_date))) |  # Valores nulos, mas dentro do intervalo
                (df['endDate'] <= pd.Timestamp(end_date))  # Valores não nulos dentro do intervalo
                )
            ]
