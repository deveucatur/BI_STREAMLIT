import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# CONFIGURAÇÕES DO STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="BI - Cadeia de Valor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    st.markdown(""" 
    <div class="topo">
        <div class="logo">
            <img src="https://raw.githubusercontent.com/deveucatur/BI_STREAMLIT/refs/heads/main/src/Design%20sem%20nome%20(2).png">
            <span>{}</span>
        </div>
    </div>
""".format(nome), unsafe_allow_html=True)

# -------------------------------
# Exemplo de uso no aplicativo
# -------------------------------
menu_menu = "BI Comparativo - Cadeia de Valor"
cabEscala(menu_menu)


# ------------------------------------------------------------------------------
# 1) Ler duas abas do Excel e concatenar (Anterior / Nova)
# ------------------------------------------------------------------------------
def carregar_duas_planilhas(
    arquivo: str = "Cadeia de Valor_Operar.xlsx",
    sheet_anterior: str = "Cadeia de Valor_Anterior",
    sheet_nova: str = "Cadeia de Valor_Nova"
) -> pd.DataFrame:
    df_anter = pd.read_excel(arquivo, sheet_name=sheet_anterior)
    df_anter['Versao'] = 'Anterior'

    df_nova = pd.read_excel(arquivo, sheet_name=sheet_nova)
    df_nova['Versao'] = 'Nova'

    df_final = pd.concat([df_anter, df_nova], ignore_index=True)
    return df_final

# ------------------------------------------------------------------------------
# 2) Limpar e preparar dados
# ------------------------------------------------------------------------------
def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    df.dropna(subset=['Processo','Procedimento','Atividade'], how='any', inplace=True)
    return df

# ------------------------------------------------------------------------------
# 3) Gera métricas (contagem de Processos, Procedimentos, etc.) por Versão
# ------------------------------------------------------------------------------
def gerar_metricas_gerais(df: pd.DataFrame) -> pd.DataFrame:
    resumo = df.groupby('Versao').agg({
        'Processo': 'nunique',
        'Procedimento': 'nunique',
        'Atividade': 'nunique',
        'Tarefa': 'nunique'
    }).reset_index()

    resumo.columns = [
        'Versao',
        'Qtd_Processos',
        'Qtd_Procedimentos',
        'Qtd_Atividades',
        'Qtd_Tarefas'
    ]
    return resumo

# ------------------------------------------------------------------------------
# 4) Treemap
# ------------------------------------------------------------------------------
def treemap_cadeia(df: pd.DataFrame, titulo: str):
    grouped = df.groupby(['Processo','Procedimento','Atividade'])['Tarefa'].count().reset_index()
    grouped.rename(columns={'Tarefa': 'Qtd_Tarefas'}, inplace=True)

    fig = px.treemap(
        grouped,
        path=['Processo','Procedimento','Atividade'],
        values='Qtd_Tarefas',
        title=titulo
    )
    # Reduz margens (diminuir espaçamento)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig

# ------------------------------------------------------------------------------
# 5) Gráfico de barras comparando Anterior vs Nova
#    * Com cor vermelha para 'Anterior' e azul para 'Nova'
# ------------------------------------------------------------------------------
def grafico_comparacao_metricas(df_metricas: pd.DataFrame, coluna: str, titulo: str):
    """
    Cria um bar chart comparando a coluna (ex: 'Qtd_Processos')
    entre 'Anterior' e 'Nova', exibindo os valores dentro das barras.
    Usamos 'color_discrete_map' para forçar 'Anterior' = 'red', 'Nova' = 'blue'.
    """
    fig = px.bar(
        df_metricas,
        x='Versao',
        y=coluna,
        color='Versao',
        barmode='group',
        text=coluna,
        title=titulo,
        labels={'Versao': 'Versão', coluna: 'Quantidade'},
        color_discrete_map={"Anterior": "red", "Nova": "blue"}
    )
    # Colocar valores dentro das barras
    fig.update_traces(textposition='inside')
    # Remover/Reduzir margens
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ------------------------------------------------------------------------------
# 6) Análise Comparativa (Mantido, Removido, Novo)
# ------------------------------------------------------------------------------
def gerar_analise_comparativa(df: pd.DataFrame):
    """
    Gera uma comparação de quais 'componentes' (Processos, Procedimentos,
    Atividades, Tarefas) foram mantidos, removidos ou novos.
    """
    resultados = []
    colunas = ['Processo','Procedimento','Atividade','Tarefa']

    for coluna in colunas:
        set_anter = set(df.loc[df['Versao'] == 'Anterior', coluna].dropna())
        set_nova = set(df.loc[df['Versao'] == 'Nova', coluna].dropna())

        mantidos = set_anter.intersection(set_nova)
        removidos = set_anter.difference(set_nova)
        novos = set_nova.difference(set_anter)

        resultados.append({
            'Componente': coluna,
            'Mantidos': len(mantidos),
            'Removidos': len(removidos),
            'Novos': len(novos)
        })

    df_comp = pd.DataFrame(resultados)
    return df_comp

def gerar_gap_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna uma tabela (Gap Analysis) listando cada item (por coluna)
    e seu status (Mantido, Removido, Novo).
    """
    registros = []
    colunas = ['Processo','Procedimento','Atividade','Tarefa']

    for coluna in colunas:
        set_anter = set(df.loc[df['Versao'] == 'Anterior', coluna].dropna())
        set_nova = set(df.loc[df['Versao'] == 'Nova', coluna].dropna())

        # Gera uma lista unificada
        todos_valores = set_anter.union(set_nova)

        for val in todos_valores:
            if val in set_anter and val in set_nova:
                status = "Mantido"
            elif val in set_anter and val not in set_nova:
                status = "Removido"
            else:
                status = "Novo"

            registros.append({
                'Componente': coluna,
                'Valor': val,
                'Status': status
            })

    gap_df = pd.DataFrame(registros)
    return gap_df

# ------------------------------------------------------------------------------
# 7) CSS para os KPIs individualizados
# ------------------------------------------------------------------------------
KPI_CSS = """
<style>
.kpi-card {
  background-color: #F2F2F2; /* fundo padrão (cinza claro) */
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 10px;
  text-align: center;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}

.kpi-card-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
}

.kpi-card-value {
  font-size: 24px;
  font-weight: bold;
  color: #000;
}

/* Cores diferentes para a versão Anterior e Nova */
.ANTERIOR { background-color: #EC7063 !important; color: #fff !important; }
.NOVA { background-color: #5DADE2 !important; color: #fff !important; }

</style>
"""

# ------------------------------------------------------------------------------
# 8) Gera gráfico de colunas para cada componente na Análise Comparativa
# ------------------------------------------------------------------------------
def gerar_barra_componente(df_comparativo, componente):
    """
    Recebe df_comparativo (Componente, Mantidos, Removidos, Novos)
    e uma string 'Processo' ou 'Procedimento' etc.
    Retorna um Plotly bar chart com cores específicas (Mantidos=Azul, Removidos=Vermelho, Novos=Verde).
    """
    row = df_comparativo[df_comparativo["Componente"] == componente]
    if row.empty:
        return None

    row = row.iloc[0]
    data = {
        "Status": ["Mantidos", "Removidos", "Novos"],
        "Quantidade": [row["Mantidos"], row["Removidos"], row["Novos"]]
    }
    df_plot = pd.DataFrame(data)

    color_map = {
        "Mantidos": "blue",
        "Removidos": "red",
        "Novos": "green"
    }

    fig = px.bar(
        df_plot,
        x="Status",
        y="Quantidade",
        color="Status",
        title=componente,
        text="Quantidade",
        color_discrete_map=color_map
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        xaxis_title="",
        yaxis_title="Qtd"
    )
    return fig

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
def main():

    # Injetar CSS customizado (KPIs)
    st.markdown(KPI_CSS, unsafe_allow_html=True)

    # 1) Carregar / Preparar
    df = carregar_duas_planilhas()
    df = preparar_dados(df)

    # 2) Métricas
    metricas = gerar_metricas_gerais(df)

    # ---- METRICAS - ANTERIOR ----
    st.subheader("Métricas - Versão Anterior")
    row_anter = metricas[metricas['Versao'] == 'Anterior']
    if not row_anter.empty:
        r = row_anter.iloc[0]
        num_processos_anter    = r['Qtd_Processos']
        num_procedimentos_anter= r['Qtd_Procedimentos']
        num_atividades_anter   = r['Qtd_Atividades']
        num_tarefas_anter      = r['Qtd_Tarefas']

        colA1, colA2, colA3, colA4 = st.columns(4)
        with colA1:
            st.markdown(f"""
            <div class="kpi-card ANTERIOR">
              <div class="kpi-card-title">Nº de Processos</div>
              <div class="kpi-card-value">{num_processos_anter}</div>
            </div>
            """, unsafe_allow_html=True)

        with colA2:
            st.markdown(f"""
            <div class="kpi-card ANTERIOR">
              <div class="kpi-card-title">Nº de Procedimentos</div>
              <div class="kpi-card-value">{num_procedimentos_anter}</div>
            </div>
            """, unsafe_allow_html=True)

        with colA3:
            st.markdown(f"""
            <div class="kpi-card ANTERIOR">
              <div class="kpi-card-title">Nº de Atividades</div>
              <div class="kpi-card-value">{num_atividades_anter}</div>
            </div>
            """, unsafe_allow_html=True)

        with colA4:
            st.markdown(f"""
            <div class="kpi-card ANTERIOR">
              <div class="kpi-card-title">Nº de Tarefas</div>
              <div class="kpi-card-value">{num_tarefas_anter}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Não há dados para a versão Anterior.")

    # ---- METRICAS - NOVA ----
    st.subheader("Métricas - Versão Nova")
    row_nova = metricas[metricas['Versao'] == 'Nova']
    if not row_nova.empty:
        r = row_nova.iloc[0]
        num_processos_nova    = r['Qtd_Processos']
        num_procedimentos_nova= r['Qtd_Procedimentos']
        num_atividades_nova   = r['Qtd_Atividades']
        num_tarefas_nova      = r['Qtd_Tarefas']

        colN1, colN2, colN3, colN4 = st.columns(4)
        with colN1:
            st.markdown(f"""
            <div class="kpi-card NOVA">
              <div class="kpi-card-title">Nº de Processos</div>
              <div class="kpi-card-value">{num_processos_nova}</div>
            </div>
            """, unsafe_allow_html=True)

        with colN2:
            st.markdown(f"""
            <div class="kpi-card NOVA">
              <div class="kpi-card-title">Nº de Procedimentos</div>
              <div class="kpi-card-value">{num_procedimentos_nova}</div>
            </div>
            """, unsafe_allow_html=True)

        with colN3:
            st.markdown(f"""
            <div class="kpi-card NOVA">
              <div class="kpi-card-title">Nº de Atividades</div>
              <div class="kpi-card-value">{num_atividades_nova}</div>
            </div>
            """, unsafe_allow_html=True)

        with colN4:
            st.markdown(f"""
            <div class="kpi-card NOVA">
              <div class="kpi-card-title">Nº de Tarefas</div>
              <div class="kpi-card-value">{num_tarefas_nova}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Não há dados para a versão Nova.")

    # 3) Gráficos comparativos (4 gráficos lado a lado)
    st.subheader("Comparação de Quantidades (Anterior vs Nova)")
    fig_proc = grafico_comparacao_metricas(metricas, 'Qtd_Processos', 'Processos')
    fig_proced = grafico_comparacao_metricas(metricas, 'Qtd_Procedimentos', 'Procedimentos')
    fig_ativ = grafico_comparacao_metricas(metricas, 'Qtd_Atividades', 'Atividades')
    fig_tarefa = grafico_comparacao_metricas(metricas, 'Qtd_Tarefas', 'Tarefas')

    col1, col2, col3, col4 = st.columns(4)
    col1.plotly_chart(fig_proc, use_container_width=True)
    col2.plotly_chart(fig_proced, use_container_width=True)
    col3.plotly_chart(fig_ativ, use_container_width=True)
    col4.plotly_chart(fig_tarefa, use_container_width=True)

    # 4) Treemaps
    st.subheader("Treemap - Cadeia de Valor")
    df_anter = df[df['Versao'] == 'Anterior']
    df_nova = df[df['Versao'] == 'Nova']

    if not df_anter.empty:
        fig_treemap_anter = treemap_cadeia(df_anter, "Treemap - Versão Anterior")
        st.plotly_chart(fig_treemap_anter, use_container_width=True)
    else:
        st.write("Não há dados para a versão Anterior.")

    if not df_nova.empty:
        fig_treemap_nova = treemap_cadeia(df_nova, "Treemap - Versão Nova")
        st.plotly_chart(fig_treemap_nova, use_container_width=True)
    else:
        st.write("Não há dados para a versão Nova.")

    # 5) Análise Comparativa (mantidos, removidos, novos - contagem)
    st.subheader("Análise Comparativa")
    df_comparativo = gerar_analise_comparativa(df)
    # Exibe a tabela de contagem
    #st.dataframe(df_comparativo)

    # ---- 4 gráficos de barras (Processo, Procedimento, Atividade, Tarefa) ----
    st.markdown("**Gráficos de Coluna por Componente:** Mantidos (Azul), Removidos (Vermelho), Novos (Verde)")

    # 4 colunas para 4 componentes
    comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)

    with comp_col1:
        fig_proc_comp = gerar_barra_componente(df_comparativo, "Processo")
        if fig_proc_comp:
            st.plotly_chart(fig_proc_comp, use_container_width=True)
    with comp_col2:
        fig_proced_comp = gerar_barra_componente(df_comparativo, "Procedimento")
        if fig_proced_comp:
            st.plotly_chart(fig_proced_comp, use_container_width=True)
    with comp_col3:
        fig_ativ_comp = gerar_barra_componente(df_comparativo, "Atividade")
        if fig_ativ_comp:
            st.plotly_chart(fig_ativ_comp, use_container_width=True)
    with comp_col4:
        fig_tarefa_comp = gerar_barra_componente(df_comparativo, "Tarefa")
        if fig_tarefa_comp:
            st.plotly_chart(fig_tarefa_comp, use_container_width=True)

    # 6) Tabela de Gap Analysis fragmentada em 4 tabelas, lado a lado
    st.subheader("Gap Analysis")
    df_gap = gerar_gap_analysis(df)

    # Filtrar 4 DataFrames diferentes
    df_gap_processo = df_gap[df_gap['Componente'] == 'Processo']
    df_gap_procedimento = df_gap[df_gap['Componente'] == 'Procedimento']
    df_gap_atividade = df_gap[df_gap['Componente'] == 'Atividade']
    df_gap_tarefa = df_gap[df_gap['Componente'] == 'Tarefa']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**Processo**")
        st.dataframe(df_gap_processo)
    with c2:
        st.markdown("**Procedimento**")
        st.dataframe(df_gap_procedimento)
    with c3:
        st.markdown("**Atividade**")
        st.dataframe(df_gap_atividade)
    with c4:
        st.markdown("**Tarefa**")
        st.dataframe(df_gap_tarefa)

    # 7) Ao final, exibe as duas tabelas (Anterior, Nova) lado a lado
    st.subheader("Cadeia de Valor Completa (Anterior e Nova)")
    colTab1, colTab2 = st.columns(2)
    with colTab1:
        st.markdown("**Tabela - Anterior**")
        if not df_anter.empty:
            st.dataframe(df_anter)
        else:
            st.write("Sem dados para a versão Anterior.")
    with colTab2:
        st.markdown("**Tabela - Nova**")
        if not df_nova.empty:
            st.dataframe(df_nova)
        else:
            st.write("Sem dados para a versão Nova.")


if __name__ == "__main__":
    main()
