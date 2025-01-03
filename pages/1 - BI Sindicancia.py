import streamlit as st
st.set_page_config(page_title="BI Sindicancia", 
                   layout="wide",
                    initial_sidebar_state="collapsed"
                   )

import pandas as pd
import plotly.express as px
from datetime import datetime
import json
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import requests
from requests_oauthlib import OAuth1
import os
from dotenv import load_dotenv 
from util import cabEscala, sideBar
import streamlit.components.v1 as components



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
cabEscala()

# Função para carregar dados da API
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
        "processId": "ElaborarRelatoriodeSindicancia",
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

        # Converter colunas de datas para datetime
        df['startDate'] = pd.to_datetime(df['startDate'], errors='coerce')
        df['endDate'] = pd.to_datetime(df['endDate'], errors='coerce')

        # Calcular Lead Time
        df['lead_time'] = (df['endDate'] - df['startDate']).dt.days

        # Tratar colunas específicas
        df['prejFinanc'] = pd.to_numeric(df['prejFinanc'], errors='coerce')

             

        # Ajustar gravidade para três categorias: Leve, Moderada, Grave
        def ajustar_gravidade(gravidade):
            if isinstance(gravidade, str):
                gravidade = gravidade.lower()
                if 'leve' in gravidade:
                    return 'Leve'
                elif 'moderada' in gravidade or 'média' in gravidade:
                    return 'Moderada'
                elif 'grave' in gravidade:
                    return 'Grave'
            return 'Não Informada'

        df['gravidadeMaxima'] = df['gravidadeMaxima'].apply(ajustar_gravidade)

        def padronizar_suspensao(suspensao):
            if isinstance(suspensao, str):
                if 'Suspensão' in suspensao:
                    return 'Suspensão'
                elif 'Orientação Disciplinar' in suspensao:
                    return 'Orientação Disciplinar'
                elif 'Advertência Escrita' in suspensao:
                    return 'Advertência Escrita'
            
            return suspensao 
        def padronizar_irregularidade(irregularidade):
        
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
                elif 'indefinido_outra' in irregularidade:
                    return 'Indefinido/Outra'
            
            # Retorna o valor original caso não haja correspondência
            return irregularidade
            

        df['tbIrregularidade___1'] =  df['tbIrregularidade___1'].apply(padronizar_irregularidade)  
        df['mddCorretSelecionada'] =  df['mddCorretSelecionada'].apply(padronizar_suspensao)   
        
        # Traduzir e padronizar status e slaStatus
        df['status'] = df['status'].str.lower().map({'open': 'Aberto', 'finalized': 'Finalizado'})
        df['slaStatus'] = df['slaStatus'].str.lower().map({'on_time': 'No Prazo', 'overdue': 'Em Atraso'})
        
        # 2. Filtros Interativos
        with st.expander("Filtros BI"):
            

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
                 gravidade_filter = multiselect_with_all("Gravidade", ['Leve', 'Moderada', 'Grave'])
            colsta4, colsta5 = st.columns(2)
            with colsta4:
                 regiao_filter = multiselect_with_all("Região", df['regiaoUnidade'].dropna().unique())
            with colsta5: 
                 solicitante_filter = multiselect_with_all("Solicitante", df['solicitante'].dropna().unique())

            cidade_filter = multiselect_with_all("Cidade", df['cidadeFato'].dropna().unique())
            unidade_filter = multiselect_with_all("Unidade", df['unidade'].dropna().unique())
            medida_filter = multiselect_with_all("Medida Corretiva", df['mddCorretSelecionada'].dropna().unique())
            #irregularidade_filter = multiselect_with_all("Irregularidade", df['irregularidade'].dropna().unique())
            
            #investigado_filter = multiselect_with_all("Investigado", df['nmInvestigado'].dropna().unique())
           

        # Aplicar filtros
        filtered_df = df[
            (df['status'].isin(status_filter)) &
            (df['slaStatus'].isin(sla_filter)) &
            (df['cidadeFato'].isin(cidade_filter)) &
            (df['unidade'].isin(unidade_filter)) &
            (df['regiaoUnidade'].isin(regiao_filter)) &
            (df['mddCorretSelecionada'].isin(medida_filter)) &
            #(df['irregularidade'].isin(irregularidade_filter)) &
            (df['gravidadeMaxima'].isin(gravidade_filter)) &
            #(df['nmInvestigado'].isin(investigado_filter)) &
            (df['solicitante'].isin(solicitante_filter))
        ]
       
        col1, col2, col3, col4,col5,col6 = st.columns(6)
        total_processos = len(filtered_df)
        status_finalizado = filtered_df[filtered_df['status'] == 'Finalizado'].shape[0]
        status_aberto = filtered_df[filtered_df['status'] == 'Aberto'].shape[0]
        status_prazo = filtered_df[filtered_df['slaStatus'] == 'No Prazo'].shape[0]
        status_lead =   filtered_df['lead_time'].mean()
        status_irregularidade = filtered_df
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
                        <h3>Processos Irregulares</h3>
                        <h1>{:.2f}</h1>
                    </div>
                """.format(status_lead ), unsafe_allow_html=True)     
        with col6:
            st.markdown("""
                    <div class="card">
                        <h3>Média de Lead Time</h3>
                        <h1>{:.2f}</h1>
                    </div>
                """.format(status_lead ), unsafe_allow_html=True)     
        # Gráficos organizados
        st.markdown("")
         # Gráficos adicionais
        
        
 
        tabCidades, tabUnidades, tabRegioes = st.tabs(["Cidades", "Unidades", "Regiões"])

        with tabCidades:
                # cidade_count = filtered_df['cidadeFato'].value_counts().reset_index()
                # cidade_count.columns = ['Cidade', 'Total']
                # fig_cidade = px.bar(cidade_count, x='Cidade', y='Total', title='Processos por Cidade', color='Total', color_continuous_scale='rainbow')
                # st.plotly_chart(fig_cidade, use_container_width=True)

               ####################  CIDADES ##############################
                grafico_cidade, macroprocesso, tabela_cidades = st.columns([2.1,0.8,1.6])
                with grafico_cidade:
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Sindicâncias por Cidade", unsafe_allow_html=True)
                    cidade_count = filtered_df['cidadeFato'].value_counts().reset_index()
                    cidade_count.columns = ['Cidade', 'Total']

                    fig_cidade = px.bar(
                        cidade_count,
                        x='Total',  # Total no eixo horizontal
                        y='Cidade',  # Cidade no eixo vertical
                        color='Total',  # Colorir as barras pelo total
                        color_continuous_scale=[[0, '#5C6F7A'], [1, '#333333']],  # Escala de cores
                        orientation='h'  # Orientação horizontal
                    )
                    fig_cidade.update_layout(
                        height=540  # Aumenta a altura do gráfico em pixels
                    )

                    # Exibir no Streamlit
                    st.plotly_chart(fig_cidade, use_container_width=True)
               
                with macroprocesso:
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Macroprocesso", unsafe_allow_html=True)
                    st.markdown("""
                    <div class="metric">
                        <h3>Administrar</h3>
                        <h1>{}</h1>
                    </div>
                """.format(status_prazo ), unsafe_allow_html=True)
                    st.markdown("")
                    st.markdown("""
                    <div class="metric">
                        <h3>Operar</h3>
                        <h1>{}</h1>
                    </div>
                """.format(status_prazo ), unsafe_allow_html=True)
                    st.markdown("")
                    st.markdown("""
                    <div class="metric">
                        <h3>Relacionamento Cargas</h3>
                        <h1>{}</h1>
                    </div>
                """.format(status_prazo ), unsafe_allow_html=True)
                    st.markdown("")
                    st.markdown("""
                    <div class="metric">
                        <h3>Relacionamento Pessoas</h3>
                        <h1>{}</h1>
                    </div>
                """.format(status_prazo ), unsafe_allow_html=True)
        
                with tabela_cidades:
                    ranking = filtered_df.groupby('cidadeFato').size().reset_index(name='num_sindicancias')
                    ranking = ranking.sort_values(by='num_sindicancias', ascending=False).reset_index(drop=True)
                    ranking['ranking'] = ranking.index + 1

                    html_content = f"""
                        <body>
                        <style>
                        {css_carregado}
                        </style>
                            <div class="ranking-container">
                                <div class="ranking-header">
                                    Ranking de Cidades
                                </div>
                                <ul class="ranking-list">
                    """            
                    for  row in ranking.itertuples():
                        html_content += f"""
                            <li class="ranking-item">
                                <span class="ranking-position">{row.ranking}º</span>
                                <span class="city-name">{row.cidadeFato}</span>
                                <span class="case-count">{row.num_sindicancias} sindicâncias</span>
                            </li> 
                        </ul>
                        </body>
                        """
                    components.html(html_content, height=540)

                ####################  IRREGULARIDADES ##############################
                tabela_irregula, gravidade, grafico_irregula = st.columns([2.1,0.8,1.6])
                with tabela_irregula:    
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Cidade", unsafe_allow_html=True)
                    irregularidade_por_cidade_df = filtered_df.groupby(
                    ['cidadeFato', 'irregularidade', 'gravidadeMaxima']
                    ).size().reset_index(name='Frequência')

                    # Criar o gráfico de barras horizontais
                    fig_irregularidade_barras_horizontais = px.bar(
                        irregularidade_por_cidade_df,
                        x='Frequência',  # Eixo X exibe a frequência
                        y='cidadeFato',  # Eixo Y exibe as cidades (cidadeFato)
                        color='gravidadeMaxima',  # Diferencia por gravidade máxima
                        orientation='h',  # Orientação horizontal
                        text='irregularidade',  # Exibe irregularidade como rótulo
                        color_discrete_sequence=['#5C6F7A', '#7B8C96', '#9CA5AE', '#BFC0C2', '#333333']   # Paleta de cores
                    )

                    # Configurar o layout do gráfico
                    fig_irregularidade_barras_horizontais.update_layout(
                       
                        xaxis_title='Total',
                        yaxis_title='Cidade',
                        legend_title='Gravidade Máxima',
                        yaxis={'categoryorder': 'total ascending'} ,
                        height=540  # Ordenação opcional por frequência
                    )
                   
                    # Exibir o gráfico na aplicação Streamlit
                    st.plotly_chart(fig_irregularidade_barras_horizontais, use_container_width=True)


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
                    <div class="metric">
                        <h3>Grave</h3>
                        <h1>{}</h1>
                    </div>
                """.format(gravidade_grave), unsafe_allow_html=True)
                    st.markdown("")
                    st.markdown("""
                    <div class="metric">
                        <h3>Mediana</h3>
                        <h1>{}</h1>
                    </div>
                """.format(gravidade_mediana), unsafe_allow_html=True)
                    st.markdown("")
                    st.markdown("""
                    <div class="metric">
                        <h3>Leve</h3>
                        <h1>{}</h1>
                    </div>
                """.format(gravidade_leve), unsafe_allow_html=True)
                          
                with grafico_irregula:   

                    ranking_cidades = (filtered_df.groupby('tbIrregularidade___1')['gravidadeMaxima'].size().reset_index(name='total_irregularidades'))
                    ranking_cidades = ranking_cidades.sort_values(by='total_irregularidades', ascending=False).reset_index(drop=True)
                    ranking_cidades['ranking'] = ranking_cidades.index + 1

                    html_content = f"""
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
                        html_content += f"""
                            <li class="ranking-item">
                                <span class="ranking-position">{row.ranking}º</span>
                                <span class="city-name">{row.tbIrregularidade___1}</span>
                                <span class="case-count">{row.total_irregularidades} </span>
                            </li> 
                        </ul>
                        </body>
                        """
                    components.html(html_content, height=570)
                    st.markdown("")

                tabela_medida ,colsp, grafico_medida= st.columns([1.9,0.5,4])
                with tabela_medida:
                    ranking_medidas = (filtered_df.groupby('mddCorretSelecionada')['gravidadeMaxima'].size().reset_index(name='total_medidas'))
                    ranking_medidas = ranking_medidas.sort_values(by='total_medidas', ascending=False).reset_index(drop=True)
                    ranking_medidas['ranking'] = ranking_medidas.index + 1

                    html_content = f"""
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
                        html_content += f"""
                            <li class="ranking-item">
                                <span class="ranking-position">{row.ranking}º</span>
                                <span class="city-name">{row.mddCorretSelecionada}</span>
                                <span class="case-count">{row.total_medidas} Medidas</span>
                            </li> 
                        </ul>
                        </body>
                        """
                    components.html(html_content, height=570)


                with grafico_medida:
                    grouped_data = df.groupby(['cidadeFato', 'mddCorretSelecionada']).size().reset_index(name='Total')
                    custom_greys = ['#2b2b2b', '#525252', '#7f7f7f', '#aaaaaa', '#d4d4d4']
                    # Criar gráfico de barras empilhadas na horizontal
                    fig = px.bar(
                        grouped_data,
                        x='Total',
                        y='cidadeFato',
                        color='mddCorretSelecionada',
                        orientation='h',  # Horizontal
                        title='Nº de Medidas Disciplinares por Tipo e Cidade',
                        labels={'cidadeFato': 'Cidade', 'Total': 'Total de Medidas', 'mddCorretSelecionada': 'Tipo de Medida'},
                        text_auto=True,
                        color_discrete_sequence=custom_greys   # Paleta de cinza
                    )

                    # Ajustar altura do gráfico
                    fig.update_layout(
                        height=550  # Define a altura do gráfico
                    )

                    # Exibir gráfico no Streamlit
                    st.plotly_chart(fig, use_container_width=True)
 

        with tabUnidades:
                col1, col2 = st.columns(2)
                with col1:
                    # unidade_count = filtered_df['unidade'].value_counts().reset_index()
                    # unidade_count.columns = ['Unidade', 'Total']
                    # fig_unidade = px.bar(unidade_count, x='Unidade', y='Total', title='Processos por Unidade', color='Total', color_continuous_scale='rainbow')
                    # st.plotly_chart(fig_unidade, use_container_width=True)
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Processos por Unidade", unsafe_allow_html=True)
                    unidade_count = filtered_df['unidade'].value_counts().reset_index()
                    unidade_count.columns = ['Unidade', 'Total']
                    fig_unidade = px.bar(
                        unidade_count,
                        x='Total',  # Total no eixo horizontal
                        y='Unidade',  # Unidade no eixo vertical
                    
                        color='Total',  # Colorir as barras pelo total
                        color_continuous_scale='rainbow',  # Escala de cores
                        orientation='h'  # Orientação horizontal
                    )
                    st.plotly_chart(fig_unidade, use_container_width=True)
                with col2:
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Unidades", unsafe_allow_html=True)
                    irregularidade_por_cidade_df = filtered_df.groupby(
                    ['unidade', 'irregularidade', 'gravidadeMaxima']
                    ).size().reset_index(name='Frequência')

                    # Criar o gráfico de barras horizontais
                    fig_irregularidade_barras_horizontais = px.bar(
                        irregularidade_por_cidade_df,
                        x='Frequência',  # Eixo X exibe a frequência
                        y='unidade',  # Eixo Y exibe as cidades (cidadeFato)
                        color='gravidadeMaxima',  # Diferencia por gravidade máxima
                        orientation='h',  # Orientação horizontal
                        text='irregularidade',  # Exibe irregularidade como rótulo
                        color_discrete_sequence=px.colors.sequential.RdBu  # Paleta de cores
                    )
                    fig_irregularidade_barras_horizontais.update_layout(
                       
                        xaxis_title='Total',
                        yaxis_title='Unidade',
                        legend_title='Gravidade Máxima',
                        yaxis={'categoryorder': 'total ascending'}  # Ordenação opcional por frequência
                    )
                    st.plotly_chart(fig_irregularidade_barras_horizontais, use_container_width=True)
                         
        with tabRegioes:
            col1, col2 = st.columns(2)
            with col1:
                # regiao_count = filtered_df['regiaoUnidade'].value_counts().reset_index()
                # regiao_count.columns = ['Região', 'Total']
                # fig_regiao = px.bar(regiao_count, x='Região', y='Total', title='Processos por Região', color='Total', color_continuous_scale='rainbow')
                # st.plotly_chart(fig_regiao, use_container_width=True)
                st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Processos por região", unsafe_allow_html=True)
                regiao_count = filtered_df['regiaoUnidade'].value_counts().reset_index()
                regiao_count.columns = ['Região', 'Total']
                fig_regiao = px.bar(
                    regiao_count,
                    x='Total',  # Total no eixo horizontal
                    y='Região',  # Região no eixo vertical
                    color='Total',  # Colorir as barras pelo total
                    color_continuous_scale='rainbow',  # Escala de cores
                    orientation='h'  # Orientação horizontal
                )
                st.plotly_chart(fig_regiao, use_container_width=True)
            with col2:
                    st.markdown("<p style='color:#333333;font-size:17px;font-weight: bold;'>Irregularidades por Região", unsafe_allow_html=True)
                    irregularidade_por_cidade_df = filtered_df.groupby(
                    ['regiaoUnidade', 'irregularidade', 'gravidadeMaxima']
                    ).size().reset_index(name='Frequência')

                    # Criar o gráfico de barras horizontais
                    fig_irregularidade_barras_horizontais = px.bar(
                        irregularidade_por_cidade_df,
                        x='Frequência',  # Eixo X exibe a frequência
                        y='regiaoUnidade',  # Eixo Y exibe as cidades (cidadeFato)
                        color='gravidadeMaxima',  # Diferencia por gravidade máxima
                        orientation='h',  # Orientação horizontal
                        text='irregularidade',  # Exibe irregularidade como rótulo
                        color_discrete_sequence=px.colors.sequential.RdBu  # Paleta de cores
                    )
                    fig_irregularidade_barras_horizontais.update_layout(
                       
                        xaxis_title='Total',
                        yaxis_title='Região',
                        legend_title='Gravidade Máxima',
                        yaxis={'categoryorder': 'total ascending'}  # Ordenação opcional por frequência
                    )
                    st.plotly_chart(fig_irregularidade_barras_horizontais, use_container_width=True)
                 
               
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
            st.markdown("---")


        ################## Mapa interativo ##########################
       
        # # Obter coordenadas das cidades
        # from geopy.geocoders import Nominatim
        # geolocator = Nominatim(user_agent="geoapiExercises")

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

        # fig_map = px.scatter_geo(
        #     city_counts,
        #     lat='latitude',
        #     lon='longitude',
        #     size='Total',
        #     hover_name='Cidade',
        #     color='Total',
        #     color_continuous_scale=px.colors.sequential.Greys,  # Paleta de cinza
        #     projection="mercator",  # Projeção para aproximar o Brasil
        #     title='Sindicâncias por Cidade no Brasil'
        # )

        # # Ajustar limites do mapa para o Brasil
        # fig_map.update_geos(
        #     fitbounds="locations",  # Ajusta os limites ao Brasil
        #     visible=False
        # )
        # st.plotly_chart(fig_map, use_container_width=True)










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
        st.markdown("---")
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
     
        st.header("Detalhamento de uma Sindicância Específica")

        # Selecionar um processo específico
        processos_disponiveis = filtered_df['processInstanceId'].unique()
        processo_selecionado = st.selectbox("Selecione o ID do Processo", processos_disponiveis)

        # Obter os dados do processo selecionado
        dados_processo = filtered_df[filtered_df['processInstanceId'] == processo_selecionado].iloc[0]

        # Exibir os dados de forma organizada
        st.markdown(f"### Dados do Processo {processo_selecionado}")

        st.markdown(f"""
    <div class="containerum">
        <div class="box">
            <h3>Informações Gerais</h3>
            <p><strong>Data Início:</strong> {dados_processo['startDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['startDate']) else 'N/A'}</p>
            <p><strong>Data Fim:</strong> {dados_processo['endDate'].strftime('%d/%m/%Y') if pd.notnull(dados_processo['endDate']) else 'N/A'}</p>
            <p><strong>Lead Time:</strong> {dados_processo['lead_time']} dias</p>
            <p><strong>Status:</strong> {dados_processo['status']}</p>
            <p><strong>Status SLA:</strong> {dados_processo['slaStatus']}</p>
            <p><strong>Unidade:</strong> {dados_processo['unidade']}</p>
            <p><strong>Cidade:</strong> {dados_processo['cidadeFato']}</p>
            <p><strong>Região:</strong> {dados_processo['regiaoUnidade']}</p>
        </div>
        <div class="box">
            <h3>Detalhes do Caso</h3>
            <p><strong>Irregularidade:</strong> {dados_processo['irregularidade']}</p>
            <p><strong>Gravidade:</strong> {dados_processo['gravidadeMaxima']}</p>
            <p><strong>Investigado:</strong> {dados_processo['nmInvestigado']}</p>
            <p><strong>Solicitante:</strong> {dados_processo['solicitante']}</p>
            <p><strong>Prejuízo Financeiro:</strong> R${dados_processo['prejFinanc']:.2f} if pd.notnull(dados_processo['prejFinanc']) else "N/A"</p>
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
        cols_relevantes = ['processInstanceId', 'startDate', 'endDate', 'lead_time', 'status', 'slaStatus', 'cidadeFato', 'unidade', 'regiaoUnidade', 'irregularidade', 'gravidadeMaxima', 'nmInvestigado', 'solicitante', 'conclusao', 'prejFinanc']
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
        # 7. Novo Painel para Visualização Detalhada de uma Sindicância
        st.markdown("---")
     
   

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
