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
from util import cabEscala, sideBar, cabEscala1
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
menu_menu = "BI Pagamentos"
menu = cabEscala1(menu_menu)




names = ['Victor Silva','Lucas','Lauro','André']
usernames = ['pedrotivictor712@gmail.com','controller.eucatur@gmail.com','lauro.processos.eucatur@gmail.com','andre.unep@gmail.com']
hashed_passwords = ['admin','admin','admin','admin']

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
            'Form name':' ACESSAR BINTELLIGENCE',
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

    current_page = "BI Pagamentos" 
    sideBar(current_page)



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

           
            def padronizar_coluna(texto):
               
                if isinstance(texto, str):  # Verifica se o valor é uma string
                    if 'ENCOM COMERCIAL - CPO ENCOMENDAS' in texto or 'JI PARANA  EUCATUR - ENCOMENDAS COMERCIAL - CPO ENCOMENDAS' in texto:
                        return 'Encomendas'
                    elif 'ADMINISTRATIVO - DPTO PESSOAL' in texto or 'ADMINIST - DPTO PESSOAL' in texto:
                        return 'Departamento Pessoal'
                    elif 'FINANCEIRO - TESOURARIA' in texto or 'FINANCEIRO - PLANEJAMENTO' in texto or 'JI PARANA EUCATUR - FINANCEIRO - COMPRAS - FIN CORPORATIVO' in texto:
                        return 'Financeiro'
                    elif 'ADM - ESCRITORIO FILIAL' in texto or 'CUIABA EUCATUR - ADMINISTRATIVO - ESCR FILIAL' in texto:
                        return 'Escritório Filial'
                    elif 'MANUTENCAO - TECN/OFICINA' in texto:
                        return 'Manutenção'
                    elif 'ADMINIST - ADM ATIVOS' in texto:
                        return 'Administração de Ativos'
                    elif 'ADMINISTRATIVO - GERENCIA' in texto:
                        return 'Gerência Administrativa'
                    elif 'OPERAC - CPO OPER INTERNO' in texto :
                        return 'Operações Internas'
                    elif '' in texto:
                        return 'não informado'
                return texto 
            
            df['departamentoSolicitante'] = df['departamentoSolicitante'].apply(padronizar_coluna)
            #df= df[df['departamentoSolicitante'].notna() & (df['departamentoSolicitante'] != '')]

            
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
                    unidade_filter = multiselect_with_all("Unidade", df['unidadeSolicitante'].dropna().unique())
                    #regiao_filter = multiselect_with_all("Região", df['regiaoUnidade'].dropna().unique())
                with colsta5: 
                    solicitante_filter = multiselect_with_all("Solicitante", df['nomeSolicitante'].dropna().unique())

                #cidade_filter = multiselect_with_all("Cidade", df['cidadeFato'].dropna().unique())
                
                colsta6, colsta7,colsta8 = st.columns(3)
                with colsta6:
                    tp_filter = multiselect_with_all("Tipo de Pagamento", df['tpPagamento'].dropna().unique())
                with colsta7:
                    start_date_default  = df['startDate'].min().date() 
                    end_date_default = datetime.today().date()    
                        
                    start_date = st.date_input("Data Inicial", start_date_default)           
                with colsta8:
                
                    end_date = st.date_input("Data Final",end_date_default)
                departamento_filter = multiselect_with_all("Departamento", df['departamentoSolicitante'].dropna().unique())
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
            # Aplicar filtros
            filtered_df = df[
                (df['status'].isin(status_filter)) &
                (df['slaStatus'].isin(sla_filter)) &
                (df['tpPagamento'].isin(tp_filter)) &
                (df['nomeSolicitante'].isin(solicitante_filter)) &
                (df['unidadeSolicitante'].isin(unidade_filter)) &
                (df['departamentoSolicitante'].isin(departamento_filter)) &
                (df['empresaPagamento'].isin(empresa_filter)) & 
                ((df['startDate'] >= pd.Timestamp(start_date)) &
                (
                (df['endDate'].isna() & (df['startDate'] <= pd.Timestamp(end_date))) | 
                (df['endDate'] <= pd.Timestamp(end_date))  
                ))
            ]                
           
            col1, col2, col3, col4,col5,col6 = st.columns(6)
            total_processos = len(filtered_df)
            status_finalizado = filtered_df[filtered_df['status'] == 'Finalizado'].shape[0]
            status_aberto = filtered_df[filtered_df['status'] == 'Aberto'].shape[0]
            status_lead =   filtered_df['lead_time'].mean()
            status_aprovado = filtered_df[filtered_df['aprovarSolic'] == 'aprovado'].shape[0]
            
            
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
                            <h3>em edição </h3>
                            <h1>{}</h1>
                        </div>
                    """.format(status_aprovado), unsafe_allow_html=True)
            with col5:
                    st.markdown("""
                        <div class="card">
                            <h3>Processos Aprovados</h3>
                            <h1>{}</h1>
                        </div>
                    """.format(status_aprovado), unsafe_allow_html=True)     
            with col6:
                st.markdown("""
                        <div class="card">
                            <h3>Média de Lead Time</h3>
                            <h1>{:.2f}</h1>
                        </div>
                    """.format(status_lead), unsafe_allow_html=True)
                
            
            st.markdown("""
                <div class="section-divider">
                    <span>PAGAMENTOS UNIDADES</span>
                </div>
                """, unsafe_allow_html=True) 
            grafico_Unidades, mapa, tabela_Unidades = st.columns([2,0.05,1.2])
            with grafico_Unidades:
                
                st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Pagamentos por Unidade", unsafe_allow_html=True)
                unidade_count = filtered_df['unidadeSolicitante'].value_counts().reset_index()
                unidade_count.columns = ['Unidade', 'Total']

                fig_unidade = px.bar(
                    unidade_count,
                    x='Total',  # Total no eixo horizontal
                    y='Unidade',  # Unidade no eixo vertical
                    color='Total',  # Colorir as barras pelo total
                    color_continuous_scale=[[0, '#333333'], [1, '#92a5ac']],  # Escala de cores
                    orientation='h'  # Orientação horizontal
                )
                fig_unidade.update_layout(
                    xaxis_title='Total',
                    yaxis_title='Unidade',
                    legend_title='Gravidade Máxima',
                    yaxis={'categoryorder': 'total ascending'} ,
                    height=480  # Aumenta a altura do gráfico em pixels
                )

                # Exibir no Streamlit
                st.plotly_chart(fig_unidade, use_container_width=True)    
            with mapa:
                st.write("")    
            with tabela_Unidades:
                rankingUni = filtered_df.groupby('unidadeSolicitante').size().reset_index(name='num_pagamentos')
                rankingUni =  rankingUni.sort_values(by='num_pagamentos', ascending=False).reset_index(drop=True)
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
                            <span class="city-name">{row.unidadeSolicitante}</span>
                            <span class="case-count">{row.num_pagamentos}</span>
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
                    <span>PAGAMENTOS departamento</span>
                </div>
                """, unsafe_allow_html=True)     

            grafico_departamentos, mapa, tabela_departamentos = st.columns([2,0.05,1.2])
            with grafico_departamentos:
                
                st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Pagamentos por Departamento", unsafe_allow_html=True)
                unidade_count = filtered_df['departamentoSolicitante'].value_counts().reset_index()
                unidade_count.columns = ['Departamento', 'Total']

                fig_departamento = px.bar(
                    unidade_count,
                    x='Total',  # Total no eixo horizontal
                    y='Departamento',  # Unidade no eixo vertical
                    color='Total',  # Colorir as barras pelo total
                    color_continuous_scale=[[0, '#333333'], [1, '#92a5ac']],  # Escala de cores
                    orientation='h'  # Orientação horizontal
                )
                fig_departamento.update_layout(
                    xaxis_title='Total',
                    yaxis_title='Departamento',
                    legend_title='Gravidade Máxima',
                    yaxis={'categoryorder': 'total ascending'} ,
                    height=480  # Aumenta a altura do gráfico em pixels
                )

                # Exibir no Streamlit
                st.plotly_chart(fig_departamento, use_container_width=True)    
            with mapa:
                st.write("")    
            with tabela_departamentos:
                rankingUni = filtered_df.groupby('departamentoSolicitante').size().reset_index(name='num_pagamentos')
                rankingUni =  rankingUni.sort_values(by='num_pagamentos', ascending=False).reset_index(drop=True)
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
                            <span class="city-name">{row.departamentoSolicitante}</span>
                            <span class="case-count">{row.num_pagamentos}</span>
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
                    <span>LEAD TIME </span>
                </div>
                """,unsafe_allow_html=True)
            lead_time_grafico, gravidade, rank_lead = st.columns([2.6,0.8,1.6])
            
            with lead_time_grafico:
                average_lead_time = filtered_df.groupby('unidadeSolicitante', as_index=False)['lead_time'].mean()
                average_lead_time = average_lead_time.sort_values(by='lead_time', ascending=True)

                # Criar o gráfico de barras horizontal com Plotly Express
            
                fig = px.bar(
                    average_lead_time,
                    x='lead_time',
                    y='unidadeSolicitante',
                    orientation='h',  # Barras horizontais
                    title='Média de Lead Time por Unidade (em dias)',
                    labels={'lead_time_days': 'Média de Lead Time (dias)', 'unidade': 'Unidade'},
                    text='lead_time',  # Exibe o valor nas barras
                    color='lead_time',  # Mapear cores ao valor de lead_time_days
                    color_continuous_scale=[[0, '#333333'], [1, '#92a5ac']],
                )

                # Customizações
                fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')  # Formatação do texto
                fig.update_layout(
                    xaxis_title='Média de Lead Time (dias)',
                    yaxis_title='Unidade',
                    xaxis=dict(showgrid=True),
                    template='plotly_white' ,
                    height=500 # Estilo do gráfico
                )

                # Mostrar o gráfico
                st.plotly_chart(fig, use_container_width=True)
            with rank_lead:
                ranking_lead_time = (filtered_df.groupby('unidadeSolicitante', as_index=False)['lead_time'].mean().rename(columns={'lead_time': 'media_time'}))
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
                            <span class="city-name">{row.unidadeSolicitante}</span>
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
                    <span>Detalhamento de um Pagamento Específico</span>
                </div>
                """,unsafe_allow_html=True)  
    # Selecionar um processo específico
    processos_disponiveis = filtered_df['processInstanceId'].unique()
    processo_selecionado = st.selectbox("Selecione o ID do Processo", processos_disponiveis)

    # Obter os dados do processo selecionado
    dados_processo = filtered_df[filtered_df['processInstanceId'] == processo_selecionado].iloc[0]

    # Exibir os dados de forma organizada
    st.markdown(f"<p style='color:#333333;font-size:22px;font-weight: bold;'>Dados do Processo {processo_selecionado}", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="containerum">
    <div class="box">
        <h3>Informações Gerais</h3>
        <p><strong>Data Início:</strong> {dados_processo['startDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['startDate']) else 'N/A'}</p>
        <p><strong>Data Fim:</strong> {dados_processo['endDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['endDate']) else 'N/A'}</p>
        <p><strong>Lead Time:</strong> {dados_processo['lead_time']:.1f} dias</p>
        <p><strong>Status:</strong> {dados_processo['status']}</p>
        <p><strong>Status SLA:</strong> {dados_processo['slaStatus']}</p>
        <p><strong>Unidade:</strong> {dados_processo['unidadeSolicitante']}</p>
    </div>
    <div class="box">
        <h3>Detalhes do Pagamento</h3>
        <p><strong>Tipo de pagamento:</strong> {dados_processo['tpPagamento']}</p>
        <p><strong>Empresa Pagamento:</strong> {dados_processo['empresaPagamento']}</p>
        <p><strong>Departamento Solicitante:</strong> {dados_processo['departamentoSolicitante']}</p>
        <p><strong>Solicitante:</strong> {dados_processo['nomeSolicitante']}</p>
        <p><strong>Função Solicitante:</strong> {dados_processo['funcaoSolicitante']} </p>
    </div>
    </div>
    <div class="conclusao">
    <h4>Observação</h4>
    <p>{dados_processo['observacao']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
                <div class="section-divider">
                    <span> Detalhamento dos Pagamentos</span>
                </div>
                """,unsafe_allow_html=True)
  
    # Selecionar colunas relevantes
    cols_relevantes = ['processInstanceId', 'startDate', 'endDate', 'lead_time', 'status', 'slaStatus', 'unidadeSolicitante', 'tpPagamento', 'empresaPagamento', 'departamentoSolicitante',  'nomeSolicitante','funcaoSolicitante', 'observacao']
    tabela_sindicancias = filtered_df[cols_relevantes].copy()
    tabela_sindicancias.columns = ['ID Processo', 'Data Início', 'Data Fim', 'Lead Time', 'Status', 'Status SLA', 'Unidade', 'Tipo de Pagamento', 'Empresa de Pagamento', 'Departamento Solicitante', 'Nome do Solicitante', 'Função do Solicitante', 'Observação']

    # Definir função personalizada para formatar datas
    def format_date(x):
        return x.strftime('%d/%m/%Y') if pd.notnull(x) else ''

    # Exibir tabela com formatação
    st.dataframe(tabela_sindicancias.style.format({
        'Data Início': format_date,
        'Data Fim': format_date,
        'Prejuízo Financeiro': 'R${:,.2f}'
    }))
   
            
            
            
            






   
