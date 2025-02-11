import streamlit as st
st.set_page_config(page_title="BI Sindicancia", 
                   layout="wide",
                    initial_sidebar_state="collapsed",
                    page_icon="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/main/src/Logomarca%20ADP%20Vs2%20(1).png"
                   )



import pandas as pd
import plotly.express as px
from datetime import datetime,timedelta
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
css_carregado = carregar_css("style.css")
local_css("style.css")




menu_menu = "BI Sindicância"
menu = cabEscala(menu_menu)




names = ['Victor Silva','Cleidimara Sander','Bruna Paio de Medeiros', 'Juliano.Marca','Vanessa']
usernames = ['pedrotivictor712@gmail.com','cleidi.sander@gmail.com' ,'performance.eucatur@gmail.com','juliano.marca','performance4.eucatur@gmail.com']
hashed_passwords = ['admin','admin','admin','admin','admin']

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
            'Form name':'ACESSAR BINTELLIGENCE',
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

    current_page = "BI Sindicancia" 
    sideBar(current_page)
 
        # Função para carregar dados da API
    @st.cache_data(ttl=600)
    def load_data_from_api(url, params=None):
        load_dotenv()
        
        oauth_consumer_key = os.getenv("oauth_consumer_key")
        oauth_consumer_secret = os.getenv("oauth_consumer_secret")
        oauth_token = os.getenv("oauth_token")
        oauth_token_secret = os.getenv("oauth_token_secret")

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

        response = requests.get(url, auth=oauth, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro {response.status_code}: {response.reason}")
            return None

    # Carregar dados dos processos
    url_processes = "http://134.65.49.113:8080/process-management/api/v2/requests"
    params_processes = {
        "status": ["OPEN", "FINALIZED"],
        "processId": "ElaborarRelatoriodeSindicancia",
        "page": 1,
        "pageSize": 1000,
        "expand": "formFields"
    }

    data_processes = load_data_from_api(url_processes, params_processes)

    if data_processes is not None:
        records_list = data_processes.get('requests', data_processes.get('items', data_processes))

        if isinstance(records_list, list):
            records = []
            for record in records_list:
                if isinstance(record, dict):
                    flat_record = record.copy()
                    form_fields = {item['field']: item['value'] for item in record.get('formFields', [])}
                    flat_record.update(form_fields)
                    flat_record.pop('formFields', None)
                    records.append(flat_record)

            df = pd.DataFrame(records)
        else:
            st.error("Estrutura de dados inesperada para processos.")
    else:
        df = pd.DataFrame()

    # Carregar dados das atividades
    url_activities = "http://134.65.49.113:8080/process-management/api/v2/activities"
    params_activities = {
        "processId": "ElaborarRelatoriodeSindicancia",
        "page": 1,
        "pageSize": 10000,
    }
    data_activities = load_data_from_api(url_activities,params_activities)

    if data_activities is not None:
        activity_list = data_activities.get('activities', data_activities.get('items', data_activities))

        if isinstance(activity_list, list):
            estados_desejados = [
                "Início", "Classificar Irregularidade", "Levantar os Fatos",
                "Realizar Parecer Jurídico", "Realizar Parecer Técnico",
                "Definir Medida Corretiva", "Aprovar Desligamento", "Fim"
            ]
            activity_records = []
            for activity in activity_list:

                if isinstance(activity, dict):
                        
                        process = activity.get("processInstanceId")
                        state_desc = activity.get("state", {}).get("stateName", "Desconhecido")
                        start_date = activity.get("startDate")
                        end_date = activity.get("endDate")

                        if state_desc in estados_desejados:
                            activity_records.append({
                                "processInstanceId": process,
                                "stateName": state_desc,
                                "startDate": start_date,
                                "endDate":end_date
                            })

            df_activities = pd.DataFrame(activity_records)
        else:
            st.error("Estrutura de dados inesperada para atividades.")
    else:
        df_activities = pd.DataFrame()

    # Exibir os DataFrames

    df_activities ['startDate'] = pd.to_datetime(df_activities ['startDate'], errors='coerce')
    df_activities ['endDate'] = pd.to_datetime( df_activities ['endDate'], errors='coerce')
    df_activities ['startDate'] = df_activities ['startDate'].dt.tz_localize(None)
    df_activities ['endDate'] =  df_activities ['endDate'].dt.tz_localize(None)
   
    # Converter colunas de datas para datetime
    df['startDate'] = pd.to_datetime(df['startDate'], errors='coerce')
    df['endDate'] = pd.to_datetime(df['endDate'], errors='coerce')
    df['startDate'] = df['startDate'].dt.tz_localize(None)
    df['endDate'] = df['endDate'].dt.tz_localize(None)

    # Calcular Lead Time
    #df_filtrado = df['lead_time'] = (df['endDate'] - df['startDate']).dt.days
    df['lead_time'] = ((df['endDate'].fillna(datetime.now()) - df['startDate']).dt.total_seconds() / 3600) / 24

    df['prejFinanc'] = df['prejFinanc'].str.replace(',', '')
    
    
    df['prejFinanc'] = pd.to_numeric(df['prejFinanc'], errors='coerce')
    df['prejFinanc'] = df['prejFinanc'].apply(lambda x: None if x == 0 else x)
    

        
        
                

            # Ajustar gravidade para três categorias: Leve, Moderada, Grave
    def ajustar_gravidade(gravidade):
            if isinstance(gravidade, str):
                gravidade = gravidade.lower()
                if 'leve' in gravidade:
                    return 'Leve'
                elif 'moderada' in gravidade or 'média' in gravidade or 'moderado' in gravidade:
                    return 'Moderada'
                elif 'grave' in gravidade:
                    return 'Grave'
                elif gravidade.strip() == '':
                    return 'Não informado'
                elif 'outra' in gravidade:
                    return 'Não informado'
            return gravidade
        
    df['gravidadeMaxima'] = df['gravidadeMaxima'].apply(ajustar_gravidade)

    def padronizar_suspensao(suspensao):
            if isinstance(suspensao, str):
                if 'Suspensão' in suspensao:
                    return 'Suspensão'
                elif 'Orientação Disciplinar' in suspensao:
                    return 'Orientação Disciplinar'
                elif 'Advertência Escrita' in suspensao:
                    return 'Advertência Escrita'
                elif 'Desligamento (Justa Causa) - Desligamento (Justa Causa)' in suspensao:
                    return 'Desligamento (Justa Causa)'
                elif suspensao.strip() == '':
                    return 'Não informada'
                
            return suspensao
        
    def padronizar_unidade(unidade):
            if isinstance(unidade, str):
                if 'CEEM Boa Vista - Manaus' in unidade:
                    return 'CEEM Boa Vista/Manaus'
                elif unidade.strip() == '':
                    return 'Não informada'


            return unidade    


        
    def padronizar_irregularidade(irregularidade):
            if irregularidade is None:  
                return 'Indefinido/Outra'
            if isinstance(irregularidade, str):
                
                # Casos específicos de padronização
                if 'equivocosatividadesprocedimentos' in irregularidade:
                    return 'Equívocos em Atividades ou Procedimentos'
                elif 'ausenciasnaojustificadas' in irregularidade:
                    return 'Ausências Não Justificadas'
                elif 'equivocosdocumentosregistros' in irregularidade:
                    return 'Equívocos em Documentos ou Registros'
                elif 'violacaonormasprocedimentos' in irregularidade:
                    return 'Violação de Normas ou Procedimentos'
                elif 'falsificacaodocumentos' in irregularidade:
                    return 'Falsificação de Documentos'
                elif 'recorrenciacondutasmoderadas' in irregularidade:
                    return 'Recorrência de Condutas Moderadas'
                elif 'recorrenciacondutasleves' in irregularidade:
                    return 'Recorrência de Condutas Leves'
                elif 'usoexcessivocelular' in irregularidade:
                    return 'Uso Excessivo de Celular'
                elif 'infracaotransitosuspensaocnh' in irregularidade:
                    return 'Infração de Trânsito com Suspensão de CNH'
                elif 'infracaotransito' in irregularidade:
                    return 'Infração de Trânsito'
                elif 'abandonoemprego' in irregularidade:
                    return 'Abandono de Emprego'
                elif 'violacaopoliticasgrave' in irregularidade:
                    return 'Violação Grave de Políticas'
                elif 'assediomoralsexual' in irregularidade:
                    return 'Assédio Moral ou Sexual'
                elif 'embriaguezdrogas' in irregularidade:
                    return 'Embriaguez ou Drogas'
                elif 'desrespeitoseguranca' in irregularidade:
                    return 'Desrespeito às Regras de Segurança'
                elif 'desidia' in irregularidade:
                    return 'Desídia'
                elif 'usoimpropriorecursos' in irregularidade:
                    return 'Uso Impróprio de Recursos'
                elif 'atrasosfrequentesinjustificados' in irregularidade:
                    return 'Atrasos Frequentes e Injustificados'
                elif 'atrasosesporadicos' in irregularidade:
                    return 'Atrasos Esporádicos'
                elif 'indefinido_outra' in irregularidade or 'outra' in irregularidade:                   
                    return 'Indefinido/Outra'
                elif irregularidade is None or irregularidade.strip() == '':
                    return 'Indefinido/Outra'
            
            # Retorna o valor original caso não haja correspondência
            return irregularidade
            
    df['tbIrregularidade___1'] = df['tbIrregularidade___1'].apply(lambda x: 'Indefinido/Outra' if x is None or str(x).strip() == '' else x)
    df['tbIrregularidade___1'] =  df['tbIrregularidade___1'].apply(padronizar_irregularidade)  
    df['mddCorretSelecionada'] =  df['mddCorretSelecionada'].apply(padronizar_suspensao)   
    #df = df.dropna(subset=['mddCorretSelecionada'])
    df['unidade'] = df['unidade'].apply(padronizar_unidade)
    
    # Traduzir e padronizar status e slaStatus
    df['status'] = df['status'].str.lower().map({'open': 'Aberto', 'finalized': 'Finalizado'})
    df['slaStatus'] = 'Em Atraso'

    df.loc[
        (df['tbIrregularidade___1'] == 'Indefinido/Outra') &
        (df['gravidadeMaxima'].isin(['Leve', 'Moderada'])) &
        (df['lead_time'] <= 3),
        'slaStatus'
    ] = 'No Prazo'
    df.loc[
        (df['gravidadeMaxima'] == 'Grave') &
        (df['lead_time'] <= 10),
        'slaStatus'
    ] = 'No Prazo'

    df.loc[
        (df['tbIrregularidade___1'] != 'Indefinido/Outra') &
        (df['gravidadeMaxima'].isin(['Leve', 'Moderada'])) &
        (df['lead_time'] <= 1),
        'slaStatus'
    ] = 'No Prazo'
    df.loc[
        (df['gravidadeMaxima'] == 'Grave') &
        (df['lead_time'] <= 5),
        'slaStatus'
    ] = 'No Prazo'
        
        # 2. Filtros Interativos
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
                status_filter = multiselect_with_all("Status", df['status'].unique())
            with colsta2:    
                sla_filter = multiselect_with_all("Status do SLA", df['slaStatus'].unique())
            with colsta3:     
                gravidade_filter = multiselect_with_all("Gravidade", ['Leve', 'Moderada', 'Grave', 'Não informado'])
            colsta4, colsta5 = st.columns(2)
            with colsta4:
                unidade_filter = multiselect_with_all("Unidade", df['unidade'].unique())
                #regiao_filter = multiselect_with_all("Região", df['regiaoUnidade'].dropna().unique())
            with colsta5: 
                solicitante_filter = multiselect_with_all("Solicitante", df['solicitante'].unique())

            #cidade_filter = multiselect_with_all("Cidade", df['cidadeFato'].dropna().unique())
            
            colsta6, colsta7,colsta8 = st.columns(3)
            with colsta6:
                medida_filter = multiselect_with_all("Medida Corretiva", df['mddCorretSelecionada'].dropna().unique())
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
        
            
        
    end_date = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    filtered_metrics = df[ 
                (df['startDate'] >= pd.Timestamp(start_date)) &
                (
                (df['endDate'].isna() & (df['startDate'] <= pd.Timestamp(end_date) )) |  # Valores nulos, mas dentro do intervalo
                (df['endDate'] <= pd.Timestamp(end_date) )) &
                (df['unidade'].isin(unidade_filter)) 
                
        ]
        

        # Aplicar filtros
    filtered_df = df[
            (df['status'].isin(status_filter)) &
            (df['slaStatus'].isin(sla_filter)) &
            #(df['cidadeFato'].isin(cidade_filter)) &
            (df['unidade'].isin(unidade_filter)) &
            #(df['regiaoUnidade'].isin(regiao_filter)) &
            (df['mddCorretSelecionada'].isin(medida_filter)) &
            #(df['irregularidade'].isin(irregularidade_filter)) &
            (df['gravidadeMaxima'].isin(gravidade_filter)) &
            #(df['nmInvestigado'].isin(investigado_filter)) &
            (df['solicitante'].isin(solicitante_filter)) &
            (df['startDate'] >= pd.Timestamp(start_date)) &
            (df['unidade'].isin(unidade_filter))&
            ((
            (df['endDate'].isna() & (df['startDate'] <= pd.Timestamp(end_date))) |  # Valores nulos, mas dentro do intervalo
            (df['endDate'] <= pd.Timestamp(end_date)   # Valores não nulos dentro do intervalo
            )))
        ]

    tab1, tab2= st.tabs(["Metrics Geral", "Metrics Filtradas"])
    with tab1:

                col1, col2, col3, col4,col5,col6 = st.columns(6)
                total_processos = len(filtered_metrics)
                status_finalizado = filtered_metrics[filtered_metrics['status'] == 'Finalizado'].shape[0]
                status_aberto = filtered_metrics[filtered_metrics['status'] == 'Aberto'].shape[0]
                status_prazo = filtered_metrics[filtered_metrics['slaStatus'] == 'No Prazo' ].shape[0]
                status_atraso = filtered_metrics[filtered_metrics['slaStatus'] == 'Em Atraso'].shape[0]
                status_lead =   filtered_metrics['lead_time'].mean()
                status_preju = soma_total = filtered_metrics['prejFinanc'].sum() 
                
                with col1:
                    st.markdown("""
                    <div class="card">
                        <h3>Total de Processos</h3>
                        <h1>{}</h1>
                    </div>
                """.format( total_processos), unsafe_allow_html=True)

                with col2:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos Finalizados</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_finalizado), unsafe_allow_html=True)
                with col3:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos Abertos</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_aberto), unsafe_allow_html=True)

                with col4:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos no Prazo</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_prazo ), unsafe_allow_html=True)
                with col5:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos em Atraso</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_atraso), unsafe_allow_html=True)     
                with col6:
                    st.markdown("""
                            <div class="card">
                                <h3>Média de Lead Time</h3>
                                <h1>{:.2f}</h1>
                            </div>
                        """.format(status_lead), unsafe_allow_html=True) 
                
                    
    with tab2: 
                col1, col2, col3, col4,col5,col6 = st.columns(6)
                total_processos = len(filtered_df)
                status_finalizado = filtered_df[filtered_df['status'] == 'Finalizado'].shape[0]
                status_aberto = filtered_df[filtered_df['status'] == 'Aberto'].shape[0]
                status_prazo = filtered_df[filtered_df['slaStatus'] == 'No Prazo' ].shape[0]
                status_atraso = filtered_df[filtered_df['slaStatus'] == 'Em Atraso'].shape[0]
                status_lead =   filtered_df['lead_time'].mean()
                status_preju = soma_total = filtered_df['prejFinanc'].sum() 
                
                with col1:
                    st.markdown("""
                    <div class="card">
                        <h3>Total de Processos</h3>
                        <h1>{}</h1>
                    </div>
                """.format( total_processos), unsafe_allow_html=True)

                with col2:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos Finalizados</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_finalizado), unsafe_allow_html=True)
                with col3:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos Abertos</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_aberto), unsafe_allow_html=True)

                with col4:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos no Prazo</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_prazo ), unsafe_allow_html=True)
                with col5:
                        st.markdown("""
                            <div class="card">
                                <h3>Processos em Atraso</h3>
                                <h1>{}</h1>
                            </div>
                        """.format(status_atraso), unsafe_allow_html=True)     
                with col6:
                    st.markdown("""
                            <div class="card">
                                <h3>Média de Lead Time</h3>
                                <h1>{:.2f}</h1>
                            </div>
                        """.format(status_lead), unsafe_allow_html=True)               
    

        # with tabCidades:
                
        #        ####################  CIDADES ##############################
        #         grafico_cidade, macroprocesso, tabela_cidades = st.columns([2.1,0.8,1.6])
        #         with grafico_cidade:
                    
        #             st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Sindicâncias por Cidade", unsafe_allow_html=True)
        #             cidade_count = filtered_df['cidadeFato'].value_counts().reset_index()
        #             cidade_count.columns = ['Cidade', 'Total']

        #             fig_cidade = px.bar(
        #                 cidade_count,
        #                 x='Total',  # Total no eixo horizontal
        #                 y='Cidade',  # Cidade no eixo vertical
        #                 color='Total',  # Colorir as barras pelo total
        #                 color_continuous_scale=[[0, '#05AFF2'], [1, '#2BD957']],  # Escala de cores
        #                 orientation='h'  # Orientação horizontal
        #             )
        #             fig_cidade.update_layout(
        #                 height=540  # Aumenta a altura do gráfico em pixels
        #             )

        #             # Exibir no Streamlit
        #             st.plotly_chart(fig_cidade, use_container_width=True)
            
        #         with macroprocesso:
        #             st.markdown("")
        #         #     st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Macroprocesso", unsafe_allow_html=True)
        #         #     st.markdown("""
        #         #     <div class="metric">
        #         #         <h3>Administrar</h3>
        #         #         <h1>{}</h1>
        #         #     </div>
        #         # """.format(status_prazo ), unsafe_allow_html=True)
        #         #     st.markdown("")
        #         #     st.markdown("""
        #         #     <div class="metric">
        #         #         <h3>Operar</h3>
        #         #         <h1>{}</h1>
        #         #     </div>
        #         # """.format(status_prazo ), unsafe_allow_html=True)
        #         #     st.markdown("")
        #         #     st.markdown("""
        #         #     <div class="metric">
        #         #         <h3>Relacionamento Cargas</h3>
        #         #         <h1>{}</h1>
        #         #     </div>
        #         # """.format(status_prazo ), unsafe_allow_html=True)
        #         #     st.markdown("")
        #         #     st.markdown("""
        #         #     <div class="metric">
        #         #         <h3>Relacionamento Pessoas</h3>
        #         #         <h1>{}</h1>
        #         #     </div>
        #         # """.format(status_prazo ), unsafe_allow_html=True)
        
        #         with tabela_cidades:
        #             ranking = filtered_df.groupby('cidadeFato').size().reset_index(name='num_sindicancias')
        #             ranking = ranking.sort_values(by='num_sindicancias', ascending=False).reset_index(drop=True)
        #             ranking['ranking'] = ranking.index + 1

        #             html_content1 = f"""
        #                 <body>
        #                 <style>
        #                 {css_carregado}
        #                 </style>
        #                     <div class="ranking-container">
        #                         <div class="ranking-header">
        #                             Ranking de Cidades
        #                         </div>
        #                         <ul class="ranking-list">
        #             """            
        #             for  row in ranking.itertuples():
        #                 html_content1 += f"""
        #                     <li class="ranking-item">
        #                         <span class="ranking-position">{row.ranking}º</span>
        #                         <span class="city-name">{row.cidadeFato}</span>
        #                         <span class="case-count">{row.num_sindicancias} sindicâncias</span>
        #                     </li> 
        #                 """
        #             html_content1 += """
        #                         </ul>
        #                     </div>
        #                 </body>
        #                 """
        #             components.html(html_content1, height=540)

        #         ####################  IRREGULARIDADES ##############################
        #         tabela_irregula, gravidade, grafico_irregula = st.columns([2.1,0.8,1.6])
        #         with tabela_irregula:    
        #             st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Cidade", unsafe_allow_html=True)
        #             irregularidade_por_cidade_df = filtered_df.groupby(
        #             ['cidadeFato', 'irregularidade', 'gravidadeMaxima']
        #             ).size().reset_index(name='Frequência')

        #             # Criar o gráfico de barras horizontais
        #             fig_irregularidade_barras_horizontais = px.bar(
        #                 irregularidade_por_cidade_df,
        #                 x='Frequência',  # Eixo X exibe a frequência
        #                 y='cidadeFato',  # Eixo Y exibe as cidades (cidadeFato)
        #                 color='gravidadeMaxima',  # Diferencia por gravidade máxima
        #                 orientation='h',  # Orientação horizontal
        #                 text='irregularidade',  # Exibe irregularidade como rótulo
        #                 color_discrete_sequence=['#5C6F7A', '#7B8C96', '#9CA5AE', '#BFC0C2', '#333333']   # Paleta de cores
        #             )

        #             # Configurar o layout do gráfico
        #             fig_irregularidade_barras_horizontais.update_layout(
                    
        #                 xaxis_title='Total',
        #                 yaxis_title='Cidade',
        #                 legend_title='Gravidade Máxima',
        #                 yaxis={'categoryorder': 'total ascending'} ,
        #                 height=540  # Ordenação opcional por frequência
        #             )
                
        #             # Exibir o gráfico na aplicação Streamlit
        #             st.plotly_chart(fig_irregularidade_barras_horizontais, use_container_width=True)


        #         with gravidade:
        #             gravidade_total = len(filtered_df['gravidadeMaxima'])
        #             gravidade_grave = filtered_df[filtered_df['gravidadeMaxima'] == 'Grave'].shape[0]
        #             gravidade_mediana = filtered_df[filtered_df['gravidadeMaxima'] == 'Moderada'].shape[0]
        #             gravidade_leve = filtered_df[filtered_df['gravidadeMaxima'] == 'Leve'].shape[0]
        #             st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Gravidade", unsafe_allow_html=True)
        #             st.markdown("""
        #             <div class="metric">
        #                 <h3>Total</h3>
        #                 <h1>{}</h1>
        #             </div>
        #         """.format(gravidade_total ), unsafe_allow_html=True)
        #             st.markdown("")
        #             st.markdown("""
        #             <div class="metric">
        #                 <h3>Grave</h3>
        #                 <h1>{}</h1>
        #             </div>
        #         """.format(gravidade_grave), unsafe_allow_html=True)
        #             st.markdown("")
        #             st.markdown("""
        #             <div class="metric">
        #                 <h3>Mediana</h3>
        #                 <h1>{}</h1>
        #             </div>
        #         """.format(gravidade_mediana), unsafe_allow_html=True)
        #             st.markdown("")
        #             st.markdown("""
        #             <div class="metric">
        #                 <h3>Leve</h3>
        #                 <h1>{}</h1>
        #             </div>
        #         """.format(gravidade_leve), unsafe_allow_html=True)
                        
        #         with grafico_irregula:   

        #             ranking_cidades = (filtered_df.groupby('tbIrregularidade___1')['gravidadeMaxima'].size().reset_index(name='total_irregularidades'))
        #             ranking_cidades = ranking_cidades.sort_values(by='total_irregularidades', ascending=False).reset_index(drop=True)
        #             ranking_cidades['ranking'] = ranking_cidades.index + 1

        #             html_content1 = f"""
        #                 <body>
        #                 <style>
        #                 {css_carregado}
        #                 </style>
        #                     <div class="ranking-container">
        #                         <div class="ranking-header">
        #                             Ranking de Irregularidades
        #                         </div>
        #                         <ul class="ranking-list">
        #             """            
        #             for  row in ranking_cidades.itertuples():
        #                 html_content1 += f"""
        #                     <li class="ranking-item">
        #                         <span class="ranking-position">{row.ranking}º</span>
        #                         <span class="city-name">{row.tbIrregularidade___1}</span>
        #                         <span class="case-count">{row.total_irregularidades} </span>
        #                     </li> 
        #                 """
        #             html_content1 += """
        #                         </ul>
        #                     </div>
        #                 </body>
        #                 """
        #             components.html(html_content1, height=570)
        #             st.markdown("")

        #         tabela_medida ,colsp, grafico_medida= st.columns([1.9,0.5,4])
        #         with tabela_medida:
        #             ranking_medidas = (filtered_df.groupby('mddCorretSelecionada')['gravidadeMaxima'].size().reset_index(name='total_medidas'))
        #             ranking_medidas = ranking_medidas.sort_values(by='total_medidas', ascending=False).reset_index(drop=True)
        #             ranking_medidas['ranking'] = ranking_medidas.index + 1

        #             html_content1 = f"""
        #                 <body>
        #                 <style>
        #                 {css_carregado}
        #                 </style>
        #                     <div class="ranking-container">
        #                         <div class="ranking-header">
        #                             Ranking de Medidas
        #                         </div>
        #                         <ul class="ranking-list">
        #             """            
        #             for  row in ranking_medidas.itertuples():
        #                 html_content1 += f"""
        #                     <li class="ranking-item">
        #                         <span class="ranking-position">{row.ranking}º</span>
        #                         <span class="city-name">{row.mddCorretSelecionada}</span>
        #                         <span class="case-count">{row.total_medidas} Medidas</span>
        #                     </li> 
        #                 """
        #             html_content1 += """
        #                         </ul>
        #                     </div>
        #                 </body>
        #                 """
        #             components.html(html_content1, height=570)


        #         with grafico_medida:
        #             st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Nº de Medidas Disciplinares por Tipo e Cidade", unsafe_allow_html=True)
        #             grouped_data = filtered_df.groupby(['cidadeFato', 'mddCorretSelecionada']).size().reset_index(name='Total')
        #             custom_greys = ['#2b2b2b', '#525252', '#7f7f7f', '#aaaaaa', '#d4d4d4']
        #             # Criar gráfico de barras empilhadas na horizontal
        #             fig = px.bar(
        #                 grouped_data,
        #                 x='cidadeFato',
        #                 y='Total',
        #                 color='mddCorretSelecionada',
        #                 labels={'cidadeFato': 'Cidade', 'Total': 'Total de Medidas', 'mddCorretSelecionada': 'Tipo de Medida'},
        #                 text_auto=True,
        #                 color_discrete_sequence=custom_greys   # Paleta de cinza
        #             )

        #             # Ajustar altura do gráfico
        #             fig.update_layout(
        #                 height=550  # Define a altura do gráfico
        #             )

        #             # Exibir gráfico no Streamlit
        #             st.plotly_chart(fig, use_container_width=True)


    
    st.markdown("")
    st.markdown("""
        <div class="section-divider">
            <span> Sindicâncias</span>
        </div>
        """, unsafe_allow_html=True)
    grafico_Unidades, mapa, tabela_Unidades = st.columns([2,0.05,1.2])
    with grafico_Unidades:
        
        st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Sindicâncias por Unidade", unsafe_allow_html=True)
        unidade_count = filtered_df['unidade'].value_counts().reset_index()
        unidade_count.columns = ['Unidade', 'Total']

        fig_unidade = px.bar(
            unidade_count,
            x='Total',  # Total no eixo horizontal
            y='Unidade',  # Unidade no eixo vertical
            color='Total',  # Colorir as barras pelo total
            color_continuous_scale=[[0, '#05AFF2'], [1, '#2BD957']],  # Escala de cores
            orientation='h'  # Orientação horizontal
        )
        fig_unidade.update_layout(
            height=540  # Aumenta a altura do gráfico em pixels
        )

        # Exibir no Streamlit
        st.plotly_chart(fig_unidade, use_container_width=True)
    
    with mapa:
        st.write("")
        # from geopy.geocoders import Nominatim
        # geolocator = Nominatim(user_agent="my_app")

        # # Criar um cache para coordenadas para evitar múltiplas chamadas
        # @st.cache_data()
        # def get_city_coordinates(cities):
        #     coordinates = {}
        #     for city in cities:
        #         try:
        #             location = geolocator.geocode(city + ", Brasil", timeout=10)
        #             if location:
        #                 coordinates[city] = {'latitude': location.latitude, 'longitude': location.longitude}
        #             else:
        #                 coordinates[city] = {'latitude': None, 'longitude': None}
        #         except:
        #             coordinates[city] = {'latitude': None, 'longitude': None}
        #     return coordinates

        # city_counts = filtered_df['cidadeFato'].value_counts().reset_index()
        # city_counts.columns = ['Cidade', 'Total']

        # city_coords = get_city_coordinates(city_counts['Cidade'])

        # city_counts['latitude'] = city_counts['Cidade'].apply(lambda x: city_coords[x]['latitude'])
        # city_counts['longitude'] = city_counts['Cidade'].apply(lambda x: city_coords[x]['longitude'])

        # # Remover cidades sem coordenadas
        # city_counts = city_counts.dropna(subset=['latitude', 'longitude'])
        # center_lat = city_counts['latitude'].mean()
        # center_lon = city_counts['longitude'].mean()

        # # Ajustar o zoom (pode ser ajustado conforme necessário)
        # zoom_level = 4

        # # Criar o mapa focado nas ocorrências
        # fig_map = px.scatter_mapbox(
        #     city_counts,
        #     lat='latitude',
        #     lon='longitude',
        #     size='Total',
        #     hover_name='Cidade',
        #     color='Total',
        #     zoom=zoom_level,
        #     mapbox_style='open-street-map',
        #     title='Sindicâncias por Cidade',
        #     center={"lat": center_lat, "lon": center_lon}
        # )

        # # Mostrar o mapa no Streamlit
        # st.plotly_chart(fig_map, use_container_width=True)



    with tabela_Unidades:
        rankingUni = filtered_df.groupby('unidade').size().reset_index(name='num_sindicancias')
        rankingUni =  rankingUni.sort_values(by='num_sindicancias', ascending=False).reset_index(drop=True)
        rankingUni ['ranking'] = rankingUni.index + 1

        html_content1 = f"""
            <body>
            <style>
            {css_carregado}
            </style>
                <div class="ranking-container ranking-green">
                    <div class="ranking-header">
                        Ranking de Unidades
                    </div>
                    <ul class="ranking-list">
        """            
        for  row in rankingUni.itertuples():
            html_content1 += f"""
                <li class="ranking-item">
                    <span class="ranking-position">{row.ranking}º</span>
                    <span class="city-name">{row.unidade}</span>
                    <span class="case-count">{row.num_sindicancias}</span>
                </li> 
            """
        html_content1 += """
                    </ul>
                </div>
            </body>
            """
        components.html(html_content1, height=570)
        
    st.markdown("""
        <div class="section-divider">
            <span>Gravidade e Irregularidades</span>
        </div>
        """,unsafe_allow_html=True)
    tabela_irregula, gravidade, grafico_irregula = st.columns([2.1,0.8,1.6])
    
    with tabela_irregula:    
        st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Unidade", unsafe_allow_html=True)
        irregularidade_por_unidade_df = filtered_df.groupby(
        ['unidade', 'irregularidade', 'gravidadeMaxima']
        ).size().reset_index(name='Frequência')

        # Criar o gráfico de barras horizontais
        fig_irregularidade_barras_horizontais_Uni = px.bar(
            irregularidade_por_unidade_df,
            x='Frequência',  # Eixo X exibe a frequência
            y='unidade',  # Eixo Y exibe as cidades (cidadeFato)
            color='gravidadeMaxima',  # Diferencia por gravidade máxima
            orientation='h',  # Orientação horizontal
            text='irregularidade',  # Exibe irregularidade como rótulo
            color_discrete_sequence=['#F22771', '#2BD957', '#F29422']   # Paleta de cores
        )

        # Configurar o layout do gráfico
        fig_irregularidade_barras_horizontais_Uni.update_layout(
            
            xaxis_title='Total',
            yaxis_title='Unidade',
            legend_title='Gravidade Máxima',
            yaxis={'categoryorder': 'total ascending'} ,
            height=540  # Ordenação opcional por frequência
        )
        
        # Exibir o gráfico na aplicação Streamlit
        st.plotly_chart(fig_irregularidade_barras_horizontais_Uni, use_container_width=True)


    with gravidade:
        gravidade_total = len(filtered_df['gravidadeMaxima'])
        gravidade_grave = filtered_df[filtered_df['gravidadeMaxima'] == 'Grave'].shape[0]
        gravidade_mediana = filtered_df[filtered_df['gravidadeMaxima'] == 'Moderada'].shape[0]
        gravidade_leve = filtered_df[filtered_df['gravidadeMaxima'] == 'Leve'].shape[0]
        st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Gravidade", unsafe_allow_html=True)
        st.markdown("""
        <div class="metric">
            <h3>Total</h3>
            <h1>{}</h1>
        </div>
    """.format(gravidade_total ), unsafe_allow_html=True)
        st.markdown("")
        st.markdown("""
        <div class="metric metric-pink">
            <h3>Grave</h3>
            <h1>{}</h1>
        </div>
    """.format(gravidade_grave), unsafe_allow_html=True)
        st.markdown("")
        st.markdown("""
        <div class="metric metric-orange">
            <h3>Mediana</h3>
            <h1>{}</h1>
        </div>
    """.format(gravidade_mediana), unsafe_allow_html=True)
        st.markdown("")
        st.markdown("""
        <div class="metric metric-green">
            <h3>Leve</h3>
            <h1>{}</h1>
        </div>
    """.format(gravidade_leve), unsafe_allow_html=True)
                
    with grafico_irregula:   

        ranking_cidades = (filtered_df.groupby('tbIrregularidade___1')['gravidadeMaxima'].size().reset_index(name='total_irregularidades'))
        ranking_cidades = ranking_cidades.sort_values(by='total_irregularidades', ascending=False).reset_index(drop=True)
        ranking_cidades['ranking'] = ranking_cidades.index + 1

        html_content1 = f"""
            <body>
            <style>
            {css_carregado}
            </style>
                <div class="ranking-container">
                    <div class="ranking-header">
                        Ranking de Irregularidades
                    </div>
                    <ul class="ranking-list">
        """            
        for  row in ranking_cidades.itertuples():
            html_content1 += f"""
                <li class="ranking-item">
                    <span class="ranking-position">{row.ranking}º</span>
                    <span class="city-name">{row.tbIrregularidade___1}</span>
                    <span class="case-count">{row.total_irregularidades} </span>
                </li> 
            """
        html_content1 += """
                    </ul>
                </div>
            </body>r
            """
        components.html(html_content1, height=600)


    st.markdown("""
        <div class="section-divider">
            <span>Lead Time</span>
        </div>
        """,unsafe_allow_html=True)
    grafico_lead,space,tabela_lead = st.columns([2.7,0.2,2.3])
    with grafico_lead:
            average_lead_time = filtered_df.groupby('unidade', as_index=False)['lead_time'].mean()
            average_lead_time = average_lead_time.sort_values(by='lead_time', ascending=True)

            # Criar o gráfico de barras horizontal com Plotly Express
        
            fig = px.bar(
                average_lead_time,
                x='lead_time',
                y='unidade',
                orientation='h',  # Barras horizontais
                title='Média de Lead Time por Unidade (em dias)',
                labels={'lead_time_days': 'Média de Lead Time (dias)', 'unidade': 'Unidade'},
                text='lead_time',  # Exibe o valor nas barras
                color='lead_time',  # Mapear cores ao valor de lead_time_days
                color_continuous_scale=[[0, '#F29422'], [1, '#F24B4B']],
            )

            # Customizações
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')  # Formatação do texto
            fig.update_layout(
                xaxis_title='Média de Lead Time (dias)',
                yaxis_title='Unidade',
                xaxis=dict(showgrid=True),
                template='plotly_white' ,
                height=500 # Estilo do gráfico
            )

            # Mostrar o gráfico
            st.plotly_chart(fig, use_container_width=True)
    with space:
             st.write("")
    with tabela_lead:     

            ranking_lead_time = (filtered_df.groupby('unidade', as_index=False)['lead_time'].mean().rename(columns={'lead_time': 'media_time'}))
            ranking_lead_time = (ranking_lead_time.sort_values(by='media_time', ascending=False).reset_index(drop=True))
            
            ranking_lead_time['ranking'] = ranking_lead_time.index + 1

            html_content1 = f"""
                <body>
                <style>
                {css_carregado}
                </style>
                    <div class="ranking-container">
                        <div class="ranking-header">
                            Ranking de Lead Time por Unidade (em dias)
                        </div>
                        <ul class="ranking-list">
            """            
            for  row in ranking_lead_time.itertuples():
                html_content1 += f"""
                    <li class="ranking-item">
                        <span class="ranking-position">{row.ranking}º</span>
                        <span class="city-name">{row.unidade}</span>
                        <span class="case-count">{row.media_time:.1f} dias</span>
                    </li> 
                """
            html_content1 += """
                        </ul>
                    </div>
                </body>
                """
            components.html(html_content1, height=500)

    grafico_lead1,space,tabela_lead1 = st.columns([3,0.2,2])

    with grafico_lead1:

        df_activities['lead_time'] =(((df_activities['endDate'].fillna(datetime.now()) - df_activities['startDate']).dt.total_seconds()/3600)/24).round(2) 
        average_lead_time = df_activities.groupby('stateName', as_index=False)['lead_time'].mean()
        average_lead_time = average_lead_time.sort_values(by='lead_time', ascending=True)

        # Criar o gráfico de barras horizontal com Plotly Express
    
        fig = px.bar(
            average_lead_time,
            x='lead_time',
            y='stateName',
            orientation='h',  # Barras horizontais
            title='Média de Lead Time por Tarefa (em dias)',
            labels={'lead_time': 'Lead Time', 'Tarefa': 'Tarefa'},
            text='lead_time',  # Exibe o valor nas barras
            color='lead_time',  # Mapear cores ao valor de lead_time_days
            color_continuous_scale=[[0, '#F29422'], [1, '#F24B4B']],
        )

        # Customizações
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')  # Formatação do texto
        fig.update_layout(
            xaxis_title='Média de Lead Time',
            yaxis_title='Tarefae',
            xaxis=dict(showgrid=True),
            template='plotly_white' ,
            height=500 # Estilo do gráfico
        )

        # Mostrar o gráfico
        st.plotly_chart(fig, use_container_width=True)
    with space:
         st.write("")    
    with tabela_lead1:  
            st.markdown("")
            st.markdown("")
            st.markdown("")
            st.markdown("")
            ranking_lead_time = (df_activities.groupby('stateName', as_index=False)['lead_time'].mean().rename(columns={'lead_time': 'media_time'}))
            ranking_lead_time = (ranking_lead_time.sort_values(by='media_time', ascending=False).reset_index(drop=True))
            
            ranking_lead_time['ranking'] = ranking_lead_time.index + 1

            html_content1 = f"""
                <body>
                <style>
                {css_carregado}
                </style>
                    <div class="ranking-container">
                        <div class="ranking-header">
                            Ranking de Lead Time por Tarefa (em dias)
                        </div>
                        <ul class="ranking-list">
            """            
            for  row in ranking_lead_time.itertuples():
                html_content1 += f"""
                    <li class="ranking-item">
                        <span class="ranking-position">{row.ranking}º</span>
                        <span class="city-name">{row.stateName}</span>
                        <span class="case-count">{row.media_time:.1f} dias</span>
                    </li> 
                """
            html_content1 += """
                        </ul>
                    </div>
                </body>
                """
            components.html(html_content1, height=500)
              


    st.markdown("""
        <div class="section-divider">
            <span>Medidas Corretivas</span>
        </div>
        """,unsafe_allow_html=True)
    tabela_medida,space,grafico_medida= st.columns([2.3,0.2,2.7])

    with grafico_medida:
       
        ############################### GRAFICO MEDIDA #####################################
        grouped_data = filtered_df.groupby(['unidade', 'mddCorretSelecionada']).size().reset_index(name='Total')
        custom_greys = ['#F22771', '#05AFF2', '#2BD957', '#F29422', '#F24B4B','#A316F5']
        # Criar gráfico de barras empilhadas na horizontal
        fig = px.bar(
            grouped_data,
            x='unidade',
            y='Total',
         
            color='mddCorretSelecionada',
            labels={'unidade': 'Unidade', 'Total': 'Total de Medidas', 'mddCorretSelecionada': 'Tipo de Medida'},
            text_auto=True,
            color_discrete_sequence=custom_greys   # Paleta de cinza
        )

        # Ajustar altura do gráfico
        fig.update_layout(
            height=500  # Define a altura do gráfico
        )

        # Exibir gráfico no Streamlit
        st.plotly_chart(fig, use_container_width=True)
    with space:
        st.write("") 
        ############################### TABELA  MEDIDA #####################################
    with tabela_medida:
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        ranking_medidas = (filtered_df.groupby('mddCorretSelecionada')['gravidadeMaxima'].size().reset_index(name='total_medidas'))
        ranking_medidas = ranking_medidas.sort_values(by='total_medidas', ascending=False).reset_index(drop=True)
        ranking_medidas['ranking'] = ranking_medidas.index + 1

        html_content1 = f"""
            <body>
            <style>
            {css_carregado}
            </style>
                <div class="ranking-container">
                    <div class="ranking-header">
                        Ranking de Medidas
                    </div>
                    <ul class="ranking-list">
        """            
        for  row in ranking_medidas.itertuples():
            html_content1 += f"""
                <li class="ranking-item">
                    <span class="ranking-position">{row.ranking}º</span>
                    <span class="city-name">{row.mddCorretSelecionada}</span>
                    <span class="case-count">{row.total_medidas} Medidas</span>
                </li> 
            """
        html_content1 += """
                    </ul>
                </div>
            </body>
            """
        components.html(html_content1, height=390)
     

    


                            
# with tabRegioes:
#     col1, col2 = st.columns(2)
#     with col1:
#         # regiao_count = filtered_df['regiaoUnidade'].value_counts().reset_index()
#         # regiao_count.columns = ['Região', 'Total']
#         # fig_regiao = px.bar(regiao_count, x='Região', y='Total', title='Processos por Região', color='Total', color_continuous_scale='rainbow')
#         # st.plotly_chart(fig_regiao, use_container_width=True)
#         st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Processos por região", unsafe_allow_html=True)
#         regiao_count = filtered_df['regiaoUnidade'].value_counts().reset_index()
#         regiao_count.columns = ['Região', 'Total']
#         fig_regiao = px.bar(
#             regiao_count,
#             x='Total',  # Total no eixo horizontal
#             y='Região',  # Região no eixo vertical
#             color='Total',  # Colorir as barras pelo total
#             color_continuous_scale='rainbow',  # Escala de cores
#             orientation='h'  # Orientação horizontal
#         )
#         st.plotly_chart(fig_regiao, use_container_width=True)
#     with col2:
#             st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Região", unsafe_allow_html=True)
#             irregularidade_por_cidade_df = filtered_df.groupby(
#             ['regiaoUnidade', 'irregularidade', 'gravidadeMaxima']
#             ).size().reset_index(name='Frequência')

#             # Criar o gráfico de barras horizontais
#             fig_irregularidade_barras_horizontais = px.bar(
#                 irregularidade_por_cidade_df,
#                 x='Frequência',  # Eixo X exibe a frequência
#                 y='regiaoUnidade',  # Eixo Y exibe as cidades (cidadeFato)
#                 color='gravidadeMaxima',  # Diferencia por gravidade máxima
#                 orientation='h',  # Orientação horizontal
#                 text='irregularidade',  # Exibe irregularidade como rótulo
#                 color_discrete_sequence=px.colors.sequential.RdBu  # Paleta de cores
#             )
#             fig_irregularidade_barras_horizontais.update_layout(
                
#                 xaxis_title='Total',
#                 yaxis_title='Região',
#                 legend_title='Gravidade Máxima',
#                 yaxis={'categoryorder': 'total ascending'}  # Ordenação opcional por frequência
#             )
#             st.plotly_chart(fig_irregularidade_barras_horizontais, use_container_width=True)
            
        
    # irregularidade_df = filtered_df.groupby(['irregularidade', 'gravidadeMaxima']).size().reset_index(name='Frequência')
    # fig_irregularidade = px.pie(
    #     irregularidade_df, 
    #     names='gravidadeMaxima', 
    #     values='Frequência', 
    #     color='gravidadeMaxima',
    #     color_discrete_sequence=px.colors.sequential.RdBu
    # )
    # st.plotly_chart(fig_irregularidade, use_container_width=True) 
    



    
    # fig_sla = px.pie(filtered_df, names='slaStatus', title='Processos por Status do SLA', color_discrete_sequence=px.colors.sequential.RdBu)
    # st.plotly_chart(fig_sla, use_container_width=True)
    # irregularidade_df = filtered_df.groupby(['irregularidade', 'gravidadeMaxima']).size().reset_index(name='Frequência')

        # Criar gráfico de barras horizontal
    # st.markdown("<p style='color:#bb2e2eb7;font-size:17px;font-weight: bold;'>Status dos Motoristas Ativos", unsafe_allow_html=True)
    # fig_status = px.pie(
    #     filtered_df, 
    #     names='status', 
    #     color_discrete_sequence=px.colors.sequential.RdBu
    # ) 

    # # Ajustar layout para reduzir áreas brancas
    # fig_status.update_layout(
    #         margin=dict(t=15, b=15),  # Ajusta margens superior, inferior, esquerda e direita
    #         height=250
    #     )

    #     # Exibir no Streamlit
    # st.plotly_chart(fig_status, use_container_width=True)
    












# # Gráficos adicionais
# tab1, tab2, tab3 = st.tabs(["Cidades", "Unidades", "Regiões"])

# with tab1:
#     cidade_count = filtered_df['cidadeFato'].value_counts().reset_index()
#     cidade_count.columns = ['Cidade', 'Total']
#     fig_cidade = px.bar(cidade_count, x='Cidade', y='Total', title='Processos por Cidade', color='Total', color_continuous_scale='rainbow')
#     st.plotly_chart(fig_cidade, use_container_width=True)

# with tab2:
#     unidade_count = filtered_df['unidade'].value_counts().reset_index()
#     unidade_count.columns = ['Unidade', 'Total']
#     fig_unidade = px.bar(unidade_count, x='Unidade', y='Total', title='Processos por Unidade', color='Total', color_continuous_scale='rainbow')
#     st.plotly_chart(fig_unidade, use_container_width=True)

# with tab3:
#     regiao_count = filtered_df['regiaoUnidade'].value_counts().reset_index()
#     regiao_count.columns = ['Região', 'Total']
#     fig_regiao = px.bar(regiao_count, x='Região', y='Total', title='Processos por Região', color='Total', color_continuous_scale='rainbow')
#     st.plotly_chart(fig_regiao, use_container_width=True)

# 5. Painel de Irregularidades e Gravidades

# st.header("Painel de Irregularidades e Gravidades")

# irregularidade_df = filtered_df.groupby(['irregularidade', 'gravidadeMaxima']).size().reset_index(name='Frequência')
# fig_irregularidade = px.bar(irregularidade_df, x='irregularidade', y='Frequência', color='gravidadeMaxima', barmode='group', title='Irregularidades por Tipo e Gravidade')
# st.plotly_chart(fig_irregularidade, use_container_width=True)

# # Tabela dinâmica
# st.subheader("Tabela de Frequência de Irregularidades")
# tabela_irregularidades = irregularidade_df.pivot_table(values='Frequência', index='irregularidade', columns='gravidadeMaxima', fill_value=0)
# st.dataframe(tabela_irregularidades.style.highlight_max(axis=0, color='lightblue'))

# # 6. Painel de Investigados e Resultados
# st.markdown("---")
# st.header("Painel de Investigados e Resultados")







# Tabela com todos os principais dados das sindicâncias
    st.markdown("""
                <div class="section-divider">
                    <span>Detalhamento de uma Sindicância Específica</span>
                </div>
                """,unsafe_allow_html=True)
    # Selecionar um processo específico
    processos_disponiveis = filtered_df['processInstanceId'].unique()
    processo_selecionado = st.selectbox("Selecione o ID do Processo", processos_disponiveis)
    
    # Obter os dados do processo selecionado
    dados_processo = filtered_df[filtered_df['processInstanceId'] == processo_selecionado].iloc[0]
    df_processo = df_activities[df_activities['processInstanceId'] == processo_selecionado]
    st.markdown(f"### Linha do Tempo do Processo {processo_selecionado}")
    fig = px.timeline(
        df_processo,
        x_start="startDate",
        x_end="endDate",
        y="stateName",
        color="stateName",
        labels={"stateName": "Tarefa"},
    )

    # Ordenar estados de forma decrescente
    fig.update_yaxes(categoryorder="total descending")

    # Configuração do layout
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Tarefa",
        height=400
    )

    # Exibir gráfico no Streamlit
    st.plotly_chart(fig)
    # Exibir os dados de forma organizada
    st.markdown(f"### Dados do Processo {processo_selecionado}")
    df_activities.to_csv('df.csv', index=False, encoding='utf-8')

    st.markdown(f"""
    <div class="containerum">
    <div class="box">
        <h3>Informações Gerais</h3>
        <p><strong>Data Início:</strong> {dados_processo['startDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['startDate']) else 'N/A'}</p>
        <p><strong>Data Fim:</strong> {dados_processo['endDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['endDate']) else 'N/A'}</p>
        <p><strong>Lead Time:</strong> {dados_processo['lead_time']:.3f} dias</p>
        <p><strong>Status:</strong> {dados_processo['status']}</p>
        <p><strong>Status SLA:</strong> {dados_processo['slaStatus']}</p>
        <p><strong>Unidade:</strong> {dados_processo['unidade']}</p>
        <p><strong>Cidade:</strong> {dados_processo['cidadeFato']}</p>
        <p><strong>Região:</strong> {dados_processo['regiaoUnidade']}</p>
    </div>
    <div class="box">
        <h3>Detalhes do Caso</h3>
        <p><strong>Irregularidade:</strong> {dados_processo['tbIrregularidade___1']}</p>
        <p><strong>Gravidade:</strong> {dados_processo['gravidadeMaxima']}</p>
        <p><strong>Investigado:</strong> {dados_processo['nmInvestigado']}</p>
        <p><strong>Solicitante:</strong> {dados_processo['solicitante']}</p>
        <p><strong>Prejuízo Financeiro:</strong> R${dados_processo['prejFinanc']:.2f} </p>
        <p><strong>Descrição do Fato:</strong> {dados_processo['descFato']}</p>
    </div>
    </div>
    <div class="conclusao">
    <h4>Conclusão</h4>
    <p>{dados_processo['conclusao']}</p>
    </div>
    """, unsafe_allow_html=True)


    st.subheader("Detalhamento das Sindicâncias")
    # Selecionar colunas relevantes
    cols_relevantes = ['processInstanceId', 'startDate', 'endDate', 'lead_time', 'status', 'slaStatus', 'cidadeFato', 'unidade', 'regiaoUnidade', 'tbIrregularidade___1', 'gravidadeMaxima', 'nmInvestigado', 'solicitante', 'conclusao', 'prejFinanc']
    tabela_sindicancias = filtered_df[cols_relevantes].copy()
    tabela_sindicancias.columns = ['ID Processo', 'Data Início', 'Data Fim', 'Lead Time', 'Status', 'Status SLA', 'Cidade', 'Unidade', 'Região', 'Irregularidade', 'Gravidade', 'Investigado', 'Solicitante', 'Conclusão', 'Prejuízo Financeiro']

    # Definir função personalizada para formatar datas
    def format_date(x):
        return x.strftime('%d/%m/%Y') if pd.notnull(x) else ''

    # Exibir tabela com formatação
    st.dataframe(tabela_sindicancias.style.format({
        'Data Início': format_date,
        'Data Fim': format_date,
        'Prejuízo Financeiro': 'R${:,.2f}'
    }))
    total =  len(tabela_sindicancias)
    
  
# 7. Novo Painel para Visualização Detalhada de uma Sindicância




#         # Impacto Financeiro ao longo do tempo aprimorado
#         st.subheader("Impacto Financeiro ao Longo do Tempo")
#         impacto_financeiro = filtered_df.groupby(pd.Grouper(key='startDate', freq='M'))['prejFinanc'].sum().reset_index()
#         impacto_financeiro['prejFinanc'] = impacto_financeiro['prejFinanc'].fillna(0)
#         fig_financeiro = px.area(impacto_financeiro, x='startDate', y='prejFinanc', title='Impacto Financeiro Mensal', markers=True)
#         fig_financeiro.update_layout(yaxis_tickprefix='R$')
#         st.plotly_chart(fig_financeiro, use_container_width=True)

#         # 9. Painel Temporal
#         st.markdown("---")
#         st.header("Painel Temporal")

#         # Volume de processos por mês
#         volume_processos = filtered_df.groupby(pd.Grouper(key='startDate', freq='M')).size().reset_index(name='Total')
#         fig_volume = px.line(volume_processos, x='startDate', y='Total', title='Volume de Processos ao Longo do Tempo', markers=True)
#         st.plotly_chart(fig_volume, use_container_width=True)


# else:
#     st.write("Não foi possível carregar os dados da API.")
