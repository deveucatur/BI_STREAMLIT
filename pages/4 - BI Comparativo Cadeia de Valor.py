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

# Exemplo de uso no aplicativo
menu_menu = "BI Comparativo - Cadeia de Valor"
cabEscala(menu_menu)

# ------------------------------------------------------------------------------
# 1) Ler as TRÊS abas do Excel e concatenar ("Anterior", "Nova", "Arquitetura")
# ------------------------------------------------------------------------------
def carregar_tres_planilhas(
    arquivo: str = "Cadeia de Valor_Operar.xlsx",
    sheet_anterior: str = "Cadeia de Valor_Anterior",
    sheet_nova: str = "Cadeia de Valor_Nova",
    sheet_arq: str = "Cadeia de Valor_Arquitetura"
) -> pd.DataFrame:
    """Lê 3 sheets do Excel e concatena, adicionando uma coluna 'Versao'."""
    df_anter = pd.read_excel(arquivo, sheet_name=sheet_anterior)
    df_anter['Versao'] = 'Anterior'

    df_nova = pd.read_excel(arquivo, sheet_name=sheet_nova)
    df_nova['Versao'] = 'Nova'

    df_arq = pd.read_excel(arquivo, sheet_name=sheet_arq)
    df_arq['Versao'] = 'Arquitetura'

    df_final = pd.concat([df_anter, df_nova, df_arq], ignore_index=True)
    return df_final

# ------------------------------------------------------------------------------
# 2) Limpar e preparar dados
# ------------------------------------------------------------------------------
def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    df.dropna(subset=['Processo','Procedimento','Atividade'], how='any', inplace=True)
    return df

# ------------------------------------------------------------------------------
# 3) Gera métricas (contagem de Processos, Procedimentos, Atividades, Tarefas) por Versão
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
    """
    Usa colunas ['Processo', 'Procedimento'] e conta Atividades (Qtd_Atividade).
    Ajuste se desejar outra hierarquia.
    """
    grouped = df.groupby(['Processo','Procedimento'])['Atividade'].count().reset_index()
    grouped.rename(columns={'Atividade': 'Qtd_Atividade'}, inplace=True)

    fig = px.treemap(
        grouped,
        path=['Processo','Procedimento'],
        values='Qtd_Atividade',
        title=titulo
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))  # reduzir margens
    return fig

# ------------------------------------------------------------------------------
# 5) Gráfico de barras comparando as versões (cor vermelha, azul, verde etc.)
# ------------------------------------------------------------------------------
def grafico_comparacao_metricas(df_metricas: pd.DataFrame, coluna: str, titulo: str):
    """
    Compara a coluna (ex: 'Qtd_Processos') entre as versões selecionadas.
    color_discrete_map define cores para 'Anterior', 'Nova', 'Arquitetura'.
    """
    color_map = {
        "Anterior": "red",
        "Nova": "blue",
        "Arquitetura": "green"
    }

    fig = px.bar(
        df_metricas,
        x='Versao',
        y=coluna,
        color='Versao',
        barmode='group',
        text=coluna,
        title=titulo,
        labels={'Versao': 'Versão', coluna: 'Quantidade'},
        color_discrete_map=color_map
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ------------------------------------------------------------------------------
# 6) Análise Comparativa (Mantido, Removido, Novo) - para exatamente 2 versões
# ------------------------------------------------------------------------------
def gerar_analise_comparativa(df: pd.DataFrame):
    """
    Gera uma comparação de quais 'componentes' (Processos, Procedimentos,
    Atividades, Tarefas) foram mantidos, removidos ou novos.

    Funciona APENAS para 2 versões no DataFrame (faz sets e intersec/diff).
    """
    # Verificar se há exatamente 2 versões
    versions_unique = df['Versao'].unique()
    if len(versions_unique) != 2:
        # Se for 1 ou 3 versões, não é compatível com a lógica de difference/intersection
        return pd.DataFrame(columns=['Componente','Mantidos','Removidos','Novos'])

    v1, v2 = versions_unique[0], versions_unique[1]

    resultados = []
    colunas = ['Processo','Procedimento','Atividade','Tarefa']

    for coluna in colunas:
        set_v1 = set(df.loc[df['Versao'] == v1, coluna].dropna())
        set_v2 = set(df.loc[df['Versao'] == v2, coluna].dropna())

        mantidos = set_v1.intersection(set_v2)
        removidos = set_v1.difference(set_v2)   # só no v1
        novos = set_v2.difference(set_v1)       # só no v2

        resultados.append({
            'Componente': coluna,
            'Mantidos': len(mantidos),
            'Removidos': len(removidos),
            'Novos': len(novos)
        })

    df_comp = pd.DataFrame(resultados)
    return df_comp

# ------------------------------------------------------------------------------
# 7) Gap Analysis (lista de cada item e status) - para 2 versões
# ------------------------------------------------------------------------------
def gerar_gap_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna uma tabela (Gap Analysis) listando cada item (por coluna)
    e seu status (Mantido, Removido, Novo), também somente para 2 versões.
    """
    versions_unique = df['Versao'].unique()
    if len(versions_unique) != 2:
        return pd.DataFrame(columns=['Componente','Valor','Status'])

    v1, v2 = versions_unique[0], versions_unique[1]

    registros = []
    colunas = ['Processo','Procedimento','Atividade','Tarefa']

    for coluna in colunas:
        set_v1 = set(df.loc[df['Versao'] == v1, coluna].dropna())
        set_v2 = set(df.loc[df['Versao'] == v2, coluna].dropna())
        todos_valores = set_v1.union(set_v2)

        for val in todos_valores:
            if val in set_v1 and val in set_v2:
                status = "Mantido"
            elif val in set_v1 and val not in set_v2:
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
# 8) CSS para os KPIs individualizados
# ------------------------------------------------------------------------------
KPI_CSS = """
<style>
.kpi-card {
  background-color: #F2F2F2;
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

/* Cores diferentes para a versão Anterior, Nova e Arquitetura */
.ANTERIOR { background-color: #EC7063 !important; color: #fff !important; }
.NOVA { background-color: #5DADE2 !important; color: #fff !important; }
.ARQUITETURA { background-color: #58D68D !important; color: #fff !important; }
</style>
"""

# ------------------------------------------------------------------------------
# 9) Gera gráfico de colunas para cada componente na Análise Comparativa
# ------------------------------------------------------------------------------
def gerar_barra_componente(df_comparativo, componente):
    """
    Gera bar chart (Mantidos=Azul, Removidos=Vermelho, Novos=Verde) para
    o componente (Processo/Procedimento/Atividade/Tarefa).
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
    # Carregar CSS customizado (KPIs)
    st.markdown(KPI_CSS, unsafe_allow_html=True)

    # 1) Ler as 3 planilhas (Anterior, Nova, Arquitetura)
    df_all = carregar_tres_planilhas()

    # 2) Selecionar quais 2 versões serão comparadas
    versoes_disponiveis = ["Anterior", "Nova", "Arquitetura"]
    escolha = st.multiselect("Selecione **2 versões** para comparar:", versoes_disponiveis, default=["Anterior","Nova"])

    # Verificar quantidade selecionada
    if len(escolha) < 2:
        st.warning("Por favor, selecione 2 versões para comparação.")
        st.stop()
    elif len(escolha) > 2:
        st.warning("Selecione apenas 2 versões para comparação.")
        st.stop()

    # Filtrar DF para apenas as 2 versões escolhidas
    df = df_all[df_all["Versao"].isin(escolha)].copy()

    # 3) Preparar dados
    df = preparar_dados(df)

    # 4) Gerar métricas
    metricas = gerar_metricas_gerais(df)

    # ---- Exibir MÉTRICAS: loop para cada versão selecionada ----
    for versao_escolhida in escolha:
        st.subheader(f"Métricas - Versão {versao_escolhida}")

        row_versao = metricas[metricas["Versao"] == versao_escolhida]
        if row_versao.empty:
            st.write(f"Não há dados para a versão {versao_escolhida}.")
        else:
            r = row_versao.iloc[0]
            num_proc  = r['Qtd_Processos']
            num_procD = r['Qtd_Procedimentos']
            num_ativ  = r['Qtd_Atividades']
            num_taref = r['Qtd_Tarefas']

            # Montamos 4 colunas com 4 cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="kpi-card {versao_escolhida.upper()}">
                  <div class="kpi-card-title">Nº de Processos</div>
                  <div class="kpi-card-value">{num_proc}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="kpi-card {versao_escolhida.upper()}">
                  <div class="kpi-card-title">Nº de Procedimentos</div>
                  <div class="kpi-card-value">{num_procD}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="kpi-card {versao_escolhida.upper()}">
                  <div class="kpi-card-title">Nº de Atividades</div>
                  <div class="kpi-card-value">{num_ativ}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="kpi-card {versao_escolhida.upper()}">
                  <div class="kpi-card-title">Nº de Tarefas</div>
                  <div class="kpi-card-value">{num_taref}</div>
                </div>
                """, unsafe_allow_html=True)

    # 5) Comparação de Quantidades
    st.subheader("Comparação de Quantidades entre as Versões Selecionadas")
    # Gráficos de barras (Processos, Procedimentos, Atividades, Tarefas)
    fig_proc = grafico_comparacao_metricas(metricas, 'Qtd_Processos', 'Processos')
    fig_proced = grafico_comparacao_metricas(metricas, 'Qtd_Procedimentos', 'Procedimentos')
    fig_ativ = grafico_comparacao_metricas(metricas, 'Qtd_Atividades', 'Atividades')
    fig_tarefas = grafico_comparacao_metricas(metricas, 'Qtd_Tarefas', 'Tarefas')

    cproc, cproc2, cproc3, cproc4 = st.columns(4)
    cproc.plotly_chart(fig_proc, use_container_width=True)
    cproc2.plotly_chart(fig_proced, use_container_width=True)
    cproc3.plotly_chart(fig_ativ, use_container_width=True)
    cproc4.plotly_chart(fig_tarefas, use_container_width=True)

    # 6) Treemaps
    st.subheader("Treemap - Cadeia de Valor (para as versões selecionadas)")
    # Dividir DF para cada versão selecionada
    for versao_escolhida in escolha:
        df_temp = df[df["Versao"] == versao_escolhida]
        if df_temp.empty:
            st.write(f"Não há dados para a versão {versao_escolhida}.")
        else:
            fig_tmap = treemap_cadeia(df_temp, f"Treemap - Versão {versao_escolhida}")
            st.plotly_chart(fig_tmap, use_container_width=True)

    # 7) Análise Comparativa (mantidos, removidos, novos)
    st.subheader("Análise Comparativa (Mantidos, Removidos, Novos)")

    # Se a função for aplicada em 2 versões, ela funciona. Caso contrário, retorna DF vazio
    df_comparativo = gerar_analise_comparativa(df)
    if df_comparativo.empty:
        st.warning("Análise Comparativa só funciona com 2 versões. Selecione 2 versões para comparar.")
    else:
        st.markdown("**Gráficos de Coluna por Componente:** Mantidos (Azul), Removidos (Vermelho), Novos (Verde)")
        # 4 gráficos
        col_comp1, col_comp2, col_comp3, col_comp4 = st.columns(4)
        with col_comp1:
            figp = gerar_barra_componente(df_comparativo, "Processo")
            if figp: st.plotly_chart(figp, use_container_width=True)
        with col_comp2:
            figp = gerar_barra_componente(df_comparativo, "Procedimento")
            if figp: st.plotly_chart(figp, use_container_width=True)
        with col_comp3:
            figp = gerar_barra_componente(df_comparativo, "Atividade")
            if figp: st.plotly_chart(figp, use_container_width=True)
        with col_comp4:
            figp = gerar_barra_componente(df_comparativo, "Tarefa")
            if figp: st.plotly_chart(figp, use_container_width=True)

        # Gap Analysis
        df_gap = gerar_gap_analysis(df)
        if df_gap.empty:
            st.warning("Gap Analysis também requer 2 versões exatas.")
        else:
            st.subheader("Gap Analysis (por Componente)")
            df_gap_processo = df_gap[df_gap['Componente'] == 'Processo']
            df_gap_procedimento = df_gap[df_gap['Componente'] == 'Procedimento']
            df_gap_atividade = df_gap[df_gap['Componente'] == 'Atividade']
            df_gap_tarefa = df_gap[df_gap['Componente'] == 'Tarefa']

            gap_col1, gap_col2, gap_col3, gap_col4 = st.columns(4)
            with gap_col1:
                st.markdown("**Processo**")
                st.dataframe(df_gap_processo)
            with gap_col2:
                st.markdown("**Procedimento**")
                st.dataframe(df_gap_procedimento)
            with gap_col3:
                st.markdown("**Atividade**")
                st.dataframe(df_gap_atividade)
            with gap_col4:
                st.markdown("**Tarefa**")
                st.dataframe(df_gap_tarefa)

    # 8) Tabelas Finais
    st.subheader("Tabelas de Cada Versão Selecionada")
    for versao_escolhida in escolha:
        df_temp = df[df["Versao"] == versao_escolhida]
        st.markdown(f"**Versão: {versao_escolhida}**")
        if df_temp.empty:
            st.write(f"Sem dados para {versao_escolhida}.")
        else:
            st.dataframe(df_temp)

if __name__ == "__main__":
    main()
