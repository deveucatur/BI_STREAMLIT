import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import json

# --------------------------------------------------
# CONFIGURAÇÕES DO STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="BI - Gestão de Ativos - Visão Geral",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def title(text):
    st.markdown(f"<p style='text-align: center; color: #143109; font-size: 26px;'><b>{text.upper()}</b></p>", unsafe_allow_html=True)

def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
 
def carregar_css(file_name):
    with open(file_name) as f:
        return f.read()        

# Aplicar o CSS personalizado
css_carregado = carregar_css("style.css")
local_css("style.css")

def cabEscala(nome):
    st.markdown(f""" 
    <div class="topo">
        <div class="left">
            <img class="logo" src="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/refs/heads/main/src/Design%20sem%20nome%20(2).png">
        </div>
        <div class="center">
            <span class="titulo">{nome}</span>
        </div>
        <div class="right"></div>
    </div>
    """, unsafe_allow_html=True)


# -------------------------------
# Exemplo de uso no aplicativo
# -------------------------------
menu_menu = "BI Estratégico - Cadeia de Valor"
cabEscala(menu_menu)

# -------------------------
# 1) Carregar dados
# -------------------------
load_dotenv()
def get_sheet_data():
    credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    SHEET_ID = os.getenv('SHEET_ID')
    SHEET_NAME = os.getenv('SHEET_NAME')
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    
    # Obtém todos os valores da planilha
    rows = sheet.get_all_values()
    headers = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=headers)
    df.columns = df.columns.str.strip()
    
    return df


st.write()

file_path = "Cadeia de Valor.xlsx"
sheet_name = "Operar Gestão de Ativos(NOVO)"
#df_original = pd.read_excel(file_path, sheet_name=sheet_name)
df_original = get_sheet_data()
df_original.columns = df_original.columns.str.strip()

# Verifique quais são as colunas carregadas
# st.write(df_original.columns)

# -------------------------
# 2) Definir Mapeamento de Frequência
# -------------------------
FREQ_MAP = {
    "Diário": 22,
    "Semanal": 4,
    "Mensal": 1,
    "Bimestral": 0.5,
    "Trimestral": 0.33,
    "Semestral" : 0.167,
    "Anual" : 0.083

}
def get_freq_multiplier(freq_str: str) -> float:
    if not isinstance(freq_str, str):
        return 1.0
    freq_str = freq_str.strip().title()  # "diário" => "Diário"
    return FREQ_MAP.get(freq_str, 1.0)

# -------------------------
# 3) Identificar as Unidades
#    A ideia é: se existe coluna "AT_FREQUÊNCIA Filial X",
#    a parte depois de "AT_FREQUÊNCIA " é o nome da unidade.
# -------------------------
lista_unidades = []
for col in df_original.columns:
    if col.startswith("AT_FREQUÊNCIA "):
        unidade = col.replace("AT_FREQUÊNCIA ", "")
        lista_unidades.append(unidade)

lista_unidades = sorted(list(set(lista_unidades)))

# -------------------------
# 4) Montar df_melt
#    - Para cada linha original
#    - Para cada unidade
#    - Gerar 2 linhas (Alta e Baixa)
#    - Preservar todos os campos originais
# -------------------------
melt_data = []

for idx, row in df_original.iterrows():
    # Convertemos a linha inteira em um dicionário
    row_dict = row.to_dict()
    
    # Para cada unidade encontrada
    for unidade in lista_unidades:
        # Criamos uma cópia do dicionário original, para não perder colunas extras
        row_alta = row_dict.copy()
        row_baixa = row_dict.copy()
        
        # Nome da colunas específicas
        col_at_freq = f"AT_FREQUÊNCIA {unidade}"
        col_at_vol  = f"AT_VOLUME {unidade}"
        col_bt_freq = f"BT_FREQUÊNCIA {unidade}"
        col_bt_vol  = f"BT_VOLUME {unidade}"
        col_tempo   = f"TEMPO (h) {unidade}"
        col_auto    = f"NÍVEL DE AUTOMAÇÃO {unidade}"
        
        # 4.1) Preparar dados "Alta Temporada"
        row_alta["Unidade"] = unidade
        row_alta["Temporada"] = "Alta"
        
        # Frequência (string)
        freq_alta_str = row_alta.get(col_at_freq, "")
        # Converter em fator mensal
        freq_alta_mult = get_freq_multiplier(freq_alta_str)
        
        # Volume
        at_volume = pd.to_numeric(row_alta.get(col_at_vol, 0), errors="coerce")
        if pd.isna(at_volume):
            at_volume = 0
        
        # Tempo (h)
        tempo_h = pd.to_numeric(row_alta.get(col_tempo, 0), errors="coerce")
        if pd.isna(tempo_h):
            tempo_h = 0
        
        # Nível de Automação
        nivel_auto = row_alta.get(col_auto, "nan")
        row_alta["NÍVEL DE AUTOMAÇÃO"] = nivel_auto
        
        # Cálculo Demanda
        demanda_alta = freq_alta_mult * at_volume * tempo_h
        row_alta["Frequência"] = freq_alta_str
        row_alta["Volume"] = at_volume
        row_alta["Tempo (h)"] = tempo_h
        row_alta["Demanda_Total_Horas"] = demanda_alta
        
        # 4.2) Preparar dados "Baixa Temporada"
        row_baixa["Unidade"] = unidade
        row_baixa["Temporada"] = "Baixa"
        
        # Frequência (string)
        freq_baixa_str = row_baixa.get(col_bt_freq, "")
        freq_baixa_mult = get_freq_multiplier(freq_baixa_str)
        
        bt_volume = pd.to_numeric(row_baixa.get(col_bt_vol, 0), errors="coerce")
        if pd.isna(bt_volume):
            bt_volume = 0
        
        tempo_h_baixa = pd.to_numeric(row_baixa.get(col_tempo, 0), errors="coerce")
        if pd.isna(tempo_h_baixa):
            tempo_h_baixa = 0
        
        nivel_auto_baixa = row_baixa.get(col_auto, "nan")
        row_baixa["NÍVEL DE AUTOMAÇÃO"] = nivel_auto_baixa
        
        demanda_baixa = freq_baixa_mult * bt_volume * tempo_h_baixa
        row_baixa["Frequência"] = freq_baixa_str
        row_baixa["Volume"] = bt_volume
        row_baixa["Tempo (h)"] = tempo_h_baixa
        row_baixa["Demanda_Total_Horas"] = demanda_baixa
        
        # Agora adicionamos ao "melt_data"
        melt_data.append(row_alta)
        melt_data.append(row_baixa)

df_melt = pd.DataFrame(melt_data)

#st.write(df_melt)

# --------------------------------------------------
# FILTROS 
# --------------------------------------------------
with st.expander("Filtros", expanded=False):
    # Podemos distribuir os filtros em colunas para otimizar espaço
    col_f1, col_f2, col_f3 = st.columns([1,1,1])
    
    with col_f1:
        # Filtro de Unidade
        unidades_selecionadas = st.multiselect(
            "Selecione Unidades",
            options=sorted(df_melt["Unidade"].unique()),
            default=sorted(df_melt["Unidade"].unique())
        )
        
        # Filtro de Processo
        processos_disponiveis = sorted(df_melt["Processo"].dropna().unique())
        processos_selecionados = st.multiselect(
            "Selecione Processos",
            options=processos_disponiveis,
            default=processos_disponiveis  # por padrão, todos
        )
        
    with col_f2:
        # Filtro de Temporada
        temporadas_disponiveis = ["Alta", "Baixa"]
        temporada_selecionada = st.multiselect(
            "Selecione Temporadas",
            options=temporadas_disponiveis,
            default=temporadas_disponiveis
        )
        
        # Filtro de Tipo de Procedimento
        procedimentos_disponiveis = sorted(df_melt["Tipo de Procedimento"].dropna().unique())
        procedimentos_selecionados = st.multiselect(
            "Tipo de Procedimento",
            options=procedimentos_disponiveis,
            default=procedimentos_disponiveis
        )
        
    with col_f3:
        # Filtro de Nível de Automação
        niveis_auto = sorted(df_melt["NÍVEL DE AUTOMAÇÃO"].dropna().unique())
        automacao_selecionada = st.multiselect(
            "Nível de Automação",
            options=niveis_auto,
            default=niveis_auto
        )

# Cria o DataFrame filtrado com base em todos os critérios
df_filtered = df_melt[
    (df_melt["Unidade"].isin(unidades_selecionadas)) &
    (df_melt["Temporada"].isin(temporada_selecionada)) &
    (df_melt["Processo"].isin(processos_selecionados)) &
    (df_melt["Tipo de Procedimento"].isin(procedimentos_selecionados)) &
    (df_melt["NÍVEL DE AUTOMAÇÃO"].isin(automacao_selecionada))
].copy()
# --------------------------------------------------
# CSS PARA DEIXAR AS MÉTRICAS MAIS ESTILOSAS
# --------------------------------------------------
st.markdown("""
<style>
.kpi-card {
  background-color: #fafafa;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  min-width: 140px;
  margin-bottom: 10px;
  /* Transições para suavizar transformações */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.kpi-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.kpi-title {
  font-size: 1rem;
  font-weight: bold;
  color: #143109;
  transition: color 0.3s ease;
}

.kpi-card:hover .kpi-title {
  color: #0e240a;
}

.kpi-value {
  font-size: 1.3rem;
  font-weight: bold;
  color: #AAAE7F;
  margin-top: 5px;
  transition: color 0.3s ease;
}

.kpi-card:hover .kpi-value {
  color: #8a8d6c;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CÁLCULO DOS INDICADORES (EXEMPLO)
# --------------------------------------------------
demanda_series = df_filtered["Demanda_Total_Horas"]

total_horas = demanda_series.sum()
num_unidades = df_filtered["Unidade"].nunique()
num_processos = df_filtered["Processo"].nunique()
num_procedimentos = df_filtered["Procedimento"].nunique()
num_atividades = df_filtered["Atividade"].nunique()
num_tarefas = df_filtered["Tarefa"].nunique()



# Exemplo de Razão (Alta vs Baixa)
soma_temp = df_filtered.groupby("Temporada", as_index=False)["Demanda_Total_Horas"].sum()
alta_total = soma_temp.loc[soma_temp["Temporada"] == "Alta", "Demanda_Total_Horas"].sum()
baixa_total = soma_temp.loc[soma_temp["Temporada"] == "Baixa", "Demanda_Total_Horas"].sum()
if baixa_total == 0:
    razao_alta_baixa = "N/A"
else:
    razao_alta_baixa = ((alta_total / baixa_total) - 1 ) * 100

# --------------------------------------------------
# EXIBIÇÃO DAS MÉTRICAS EM COLUNAS
# --------------------------------------------------
title("Indicadores Gerais e Avançados")

# 1ª LINHA (3 colunas)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Nº de Unidades</div>
      <div class="kpi-value">{num_unidades}</div>
    </div>
    """, unsafe_allow_html=True)


with col2:
    
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Demanda Total de Horas</div>
      <div class="kpi-value">{total_horas:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    razao_valor = f"{razao_alta_baixa:,.2f}" if isinstance(razao_alta_baixa, (int, float)) else razao_alta_baixa
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Razão (Alta / Baixa)</div>
      <div class="kpi-value">{razao_valor} %</div>
    </div>
    """, unsafe_allow_html=True)

# 2ª LINHA (3 colunas)
col4, col5, col6, col7 = st.columns(4)

with col4:
        st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Nº de Processos</div>
      <div class="kpi-value">{num_processos}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:        
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Nº de Procedimentos</div>
      <div class="kpi-value">{num_procedimentos}</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Nº de Atividades</div>
      <div class="kpi-value">{num_atividades}</div>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">Nº de Tarefas</div>
      <div class="kpi-value">{num_tarefas:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)




# -------------------------
# Gráfico de Colunas: Demanda de Horas total por Unidade
# -------------------------



# Agrupa por Unidade, somando a Demanda_Total_Horas
df_unidades = df_filtered.groupby("Unidade", as_index=False)["Demanda_Total_Horas"].sum()

# Ordena do maior para o menor (opcional)
df_unidades = df_unidades.sort_values("Demanda_Total_Horas", ascending=False)

# Cria o gráfico de colunas
fig_unidades = px.bar(
    df_unidades,
    x="Unidade",
    y="Demanda_Total_Horas",
    title="Demanda de Horas Total por Unidade",
    color_discrete_sequence=["#699B69"]
)

# Exibe no Streamlit
st.plotly_chart(fig_unidades, use_container_width=True)


col1, col2 = st.columns(2)

color_sequence = [
    "#B8E0A0",
    "#A9D18E",
    "#8FC47F",
    "#80B57F",
    "#76AC76",
    "#699B69"
]

with col1:
    # -------------------------
    # Gráfico de Pizza: Demanda de Horas por Tipo de Procedimento
    # -------------------------

    # Agrupa por Tipo de Procedimento
    df_tipo = df_filtered.groupby("Tipo de Procedimento", as_index=False)["Demanda_Total_Horas"].sum()

    # Cria o gráfico de pizza
    fig_tipo = px.pie(
        df_tipo,
        names="Tipo de Procedimento",
        values="Demanda_Total_Horas",
        title="Demanda de Horas por Tipo de Procedimento",
        color_discrete_sequence=color_sequence
    )

    st.plotly_chart(fig_tipo, use_container_width=True)



    # -------------------------
    # Gráfico de Barras: Demanda de Horas por Unidade e Tipo de Procedimento
    # -------------------------

    # Agrupa por Unidade e Tipo de Procedimento, somando as horas
    df_u_tp = df_filtered.groupby(["Unidade", "Tipo de Procedimento"], as_index=False)["Demanda_Total_Horas"].sum()

    # Gráfico de barras agrupadas (poderia usar barmode="stack" se preferir barras empilhadas)
    fig_u_tp = px.bar(
        df_u_tp,
        x="Unidade",
        y="Demanda_Total_Horas",
        color="Tipo de Procedimento",
        barmode="group",  # Troque para "stack" para barras empilhadas
        title="Demanda de Horas por Unidade e Tipo de Procedimento", 
        color_discrete_sequence=color_sequence
    )

    st.plotly_chart(fig_u_tp, use_container_width=True)


with col2:

    # -------------------------
    # GRÁFICO DE PIZZA: NÍVEL DE AUTOMAÇÃO (Excluindo 'nan')
    # (Se não quiser exibir automação, pode remover este bloco também.)
    # -------------------------
    df_pizza = df_filtered[df_filtered["NÍVEL DE AUTOMAÇÃO"].str.lower() != "nan"]
    if not df_pizza.empty:
        auto_count = df_pizza["NÍVEL DE AUTOMAÇÃO"].value_counts().reset_index()
        auto_count.columns = ["NívelAutomacao", "Count"]
        fig_auto = px.pie(
            auto_count,
            names="NívelAutomacao",
            values="Count",
            title="Nível de Automação",
            color_discrete_sequence=color_sequence
        )

        st.plotly_chart(fig_auto, use_container_width=True)
    else:
        st.info("Não há dados de automação (fora 'nan') após os filtros.")



    # st.markdown("### Comparação de Demanda por Nível de Automação")
    df_auto_comp = df_filtered.groupby("NÍVEL DE AUTOMAÇÃO", as_index=False)["Demanda_Total_Horas"].mean()
    fig_auto_comp = px.bar(
        df_auto_comp,
        x="NÍVEL DE AUTOMAÇÃO",
        y="Demanda_Total_Horas",
        title="Média de Horas x Nível de Automação", 
        color_discrete_sequence=["#699B69"]
    )
    st.plotly_chart(fig_auto_comp, use_container_width=True)







# -------------------------
# COMPARAÇÃO DE DEMANDA DE HORAS (ALTA VS. BAIXA)
# -------------------------


def plot_top_alta_ordenado(df: pd.DataFrame, coluna: str, top_n=10, titulo=""):
    """
    Cria um gráfico de barras agrupadas (Alta vs. Baixa) exibindo apenas os
    'top_n' itens com maior Demanda_Total_Horas na Alta Temporada,
    e mostra esses itens no eixo X em ordem decrescente (maior para menor).
    
    Parâmetros:
        df (pd.DataFrame): DataFrame filtrado, contendo pelo menos [coluna, "Temporada", "Demanda_Total_Horas"].
        coluna (str): Nome da coluna a analisar (ex.: "Processo", "Procedimento", etc.).
        top_n (int): Quantos itens exibir (com base na Alta Temporada).
        titulo (str): Título do gráfico (opcional).
    """
    # 1) Agrupa por [coluna, Temporada] e soma a Demanda_Total_Horas
    df_grp = df.groupby([coluna, "Temporada"], as_index=False)["Demanda_Total_Horas"].sum()
    
    # 2) Separa a Alta Temporada para descobrir quais são os top_n itens
    df_alta = df_grp[df_grp["Temporada"] == "Alta"].copy()
    df_alta = df_alta.sort_values("Demanda_Total_Horas", ascending=False)
    
    # 3) Pega o nome dos top_n itens em Alta
    top_items = df_alta.head(top_n)[coluna].unique()
    
    # 4) Filtra df_grp para incluir só esses itens (Alta e Baixa)
    df_final = df_grp[df_grp[coluna].isin(top_items)].copy()
    
    # 5) Ordenação do eixo X do maior para o menor com base na Alta
    #    Precisamos criar uma lista ordenada pelos valores de Alta
    #    e transformar a coluna em Categorical
    sorted_items = (
        df_alta.head(top_n)
        .sort_values("Demanda_Total_Horas", ascending=False)[coluna]
        .unique()
    )
    df_final[coluna] = pd.Categorical(
        df_final[coluna],
        categories=sorted_items,
        ordered=True
    )
    
    # 6) Cria o gráfico de barras agrupadas (Alta vs. Baixa)
    fig = px.bar(
        df_final,
        x=coluna,
        y="Demanda_Total_Horas",
        color="Temporada",
        barmode="group",
        title=titulo if titulo else f"Comparativo Alta vs. Baixa - {coluna}",
        labels={coluna: coluna, "Demanda_Total_Horas": "Demanda (h)"},
        color_discrete_sequence=color_sequence
    )
    
    # 7) Exibe o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)



    # Exemplo de uso


plot_top_alta_ordenado(
    df_filtered, 
    coluna="Processo", 
    top_n=6,
    titulo="Processos (Alta vs. Baixa)"
)


plot_top_alta_ordenado(
    df_filtered, 
    coluna="Procedimento", 
    top_n=6,
    titulo="Top Procedimentos (Alta vs. Baixa)"
)


plot_top_alta_ordenado(
    df_filtered, 
    coluna="Atividade", 
    top_n=10,
    titulo="Top Atividades (Alta vs. Baixa)"
)





def get_treemap_chart(df: pd.DataFrame):
    """
    Retorna um treemap com a hierarquia:
    Processo -> Procedimento -> Atividade -> Tarefa,
    usando Demanda_Total_Horas como valor.
    """
    # 1) Verificar se existem as colunas necessárias
    colunas_necessarias = ["Processo", "Procedimento", "Atividade", "Tarefa", "Demanda_Total_Horas"]
    for col in colunas_necessarias:
        if col not in df.columns:
            st.warning(f"Coluna '{col}' não encontrada no DataFrame. Verifique se existe.")
            return None
    
    # 2) Agrupar e somar Demanda_Total_Horas (caso existam linhas repetidas)
    #    Se seu df já estiver no nível de granularidade que precisa, pode pular este groupby.
    df_treemap = df.groupby(["Processo", "Procedimento", "Atividade", "Tarefa"], as_index=False)["Demanda_Total_Horas"].sum()
    
    # 3) Criar o Treemap
    fig = px.treemap(
        df_treemap,
        path=["Processo", "Procedimento", "Atividade", "Tarefa"],  # Hierarquia
        values="Demanda_Total_Horas",
        title="Treemap - Cadeia de Valor",
        color="Demanda_Total_Horas",  # Opcional: colorir de acordo com Demanda_Total_Horas
        color_continuous_scale="bugn",  # Exemplo de escala de cor
    )
    
    # Ajustar layout (margens)
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    
    return fig

# --------------------- USO DO TREEMAP ---------------------

# Exemplo de uso (supondo que df_filtered já foi definido e possui as colunas 
# [Processo, Procedimento, Atividade, Tarefa, Demanda_Total_Horas])
treemap_fig = get_treemap_chart(df_filtered)

if treemap_fig:
    st.plotly_chart(treemap_fig, use_container_width=True)
else:
    st.info("Não foi possível gerar o Treemap.")









# # 1) Agrupa Demanda por Unidade
# df_unidades = df_filtered.groupby("Unidade", as_index=False)["Demanda_Total_Horas"].sum()

# # 2) Calcula colaboradores
# df_unidades["Colaboradores_Necessarios"] = np.ceil(df_unidades["Demanda_Total_Horas"] / 200)

# # st.markdown("## Quadro Ideal de Colaboradores por Unidade")
# title("Quadro Ideal de Colaboradores por Unidade")

# # 3) Mostra tabela resumida (opcional, mas útil)
# st.write("Tabela de Demanda e Colaboradores Necessários (1 colaborador = 200h/mês)")
# st.dataframe(df_unidades)

# # 4) Visualização em Gráfico de Barras Agrupadas
# fig_colab = px.bar(
#     df_unidades.melt(
#         id_vars="Unidade",
#         value_vars=["Demanda_Total_Horas", "Colaboradores_Necessarios"],
#         var_name="Métrica", 
#         value_name="Valor"
#     ),
#     x="Unidade",
#     y="Valor",
#     color="Métrica",
#     barmode="group",
#     title="Demanda de Horas e Colaboradores Necessários por Unidade",
#     labels={"Unidade": "Unidade", "Valor": "Valor (h ou Colab)"},
#     color_discrete_sequence=["#2E93fA","#FF5733"]
# )
# st.plotly_chart(fig_colab, use_container_width=True)

# # 5) Ou, caso prefira mostrar apenas o número de colaboradores em um gráfico simples:
# fig_colab_simpl = px.bar(
#     df_unidades,
#     x="Unidade",
#     y="Colaboradores_Necessarios",
#     title="Colaboradores Necessários por Unidade (1 colab = 200h/mês)",
#     color_discrete_sequence=["#00CC96"]
# )
# st.plotly_chart(fig_colab_simpl, use_container_width=True)


# -------------------------
# TABELA DETALHADA
# -------------------------
st.markdown("---")
# st.markdown("## Dados Detalhados (Tabela Filtrada)")
title("Dados Detalhados")
st.dataframe(df_filtered.reset_index(drop=True))