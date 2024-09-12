import streamlit as st
import pandas as pd
import plotly.express as px
from query import view_all_data
import numpy as np


st.set_page_config(page_title="Dashboard", page_icon="", layout="wide")

@st.cache_data
def load_data():
    result = view_all_data()
    df = pd.DataFrame(result, columns=["id", "temperatura", "pressao" , "altitude", "umidade", "co2", "tempo_registro"])
    return df

df = load_data()

if st.button("Atualizar Dados"):
    df = load_data()

st.sidebar.header("Selecione a Informação para Gráficos")

x_axis = st.sidebar.selectbox(
    "Eixo X",
    options=["umidade", "temperatura", "pressao", "altitude", "co2"],
    index=0
)

y_axis = st.sidebar.selectbox(
    "Eixo Y",
    options=["umidade", "temperatura", "pressao", "altitude", "co2"],
    index=1
)

def filtros(attribute):
    return attribute in [x_axis, y_axis]

st.sidebar.header("Selecione o Filtro")

if filtros("temperatura"):
    st.session_state.temperatura_range = st.sidebar.slider(
        "Temperatura (°C)",
        min_value=float(df["temperatura"].min()),
        max_value=float(df["temperatura"].max()),
        value=(float(df["temperatura"].min()), float(df["temperatura"].max())),
        step=0.1
    )

if filtros("pressao"):
    st.session_state.pressao_range = st.sidebar.slider(
        "Pressão (hPa)",
        min_value=float(df["pressao"].min()),
        max_value=float(df["pressao"].max()),
        value=(float(df["pressao"].min()), float(df["pressao"].max())),
        step=0.1
    )

if filtros("altitude"):
    st.session_state.altitude_range = st.sidebar.slider(
        "Altitude (m)",
        min_value=float(df["altitude"].min()),
        max_value=float(df["altitude"].max()),
        value=(float(df["altitude"].min()), float(df["altitude"].max())),
        step=1.0
    )

if filtros("umidade"):
    st.session_state.umidade_range = st.sidebar.slider(
        "Umidade (%)",
        min_value=float(df["umidade"].min()),
        max_value=float(df["umidade"].max()),
        value=(float(df["umidade"].min()), float(df["umidade"].max())),
        step=0.1
    )

if filtros("co2"):
    st.session_state.co2_range = st.sidebar.slider(
        "CO2 (ppm)",
        min_value=float(df["co2"].min()),
        max_value=float(df["co2"].max()),
        value=(float(df["co2"].min()), float(df["co2"].max())),
        step=1.0
    )

df_selection = df.copy()
if filtros("temperatura"):
    df_selection = df_selection[
        (df_selection["temperatura"] >= st.session_state.temperatura_range[0]) & 
        (df_selection["temperatura"] <= st.session_state.temperatura_range[1])
    ]

if filtros("pressao"):
    df_selection = df_selection[
        (df_selection["pressao"] >= st.session_state.pressao_range[0]) & 
        (df_selection["pressao"] <= st.session_state.pressao_range[1])
    ]

if filtros("altitude"):
    df_selection = df_selection[
        (df_selection["altitude"] >= st.session_state.altitude_range[0]) & 
        (df_selection["altitude"] <= st.session_state.altitude_range[1])
    ]

if filtros("umidade"):
    df_selection = df_selection[
        (df_selection["umidade"] >= st.session_state.umidade_range[0]) & 
        (df_selection["umidade"] <= st.session_state.umidade_range[1])
    ]

if filtros("co2"):
    df_selection = df_selection[
        (df_selection["co2"] >= st.session_state.co2_range[0]) & 
        (df_selection["co2"] <= st.session_state.co2_range[1])
    ]

def Home():
    with st.expander("Tabular"):
        showData = st.multiselect('Filter: ', df_selection.columns, default=[], key="showData_home")
        if showData:
            st.write(df_selection[showData])
        
    if not df_selection.empty:
        media_umidade = df_selection["umidade"].mean()
        media_temperatura = df_selection["temperatura"].mean()
        media_co2 = df_selection["co2"].mean()
        media_pressao = df_selection["pressao"].mean()

        total1, total2, total3, total4 = st.columns(4, gap='large')

        with total1:
            st.info('Média de Registros Umidade', icon='📌')
            st.metric(label="Média", value=f"{media_umidade:.2f}")

        with total2:
            st.info('Média de Registro CO2', icon='📌')
            st.metric(label="Média", value=f"{media_co2:.2f}")
        
        with total3:
            st.info('Média de Registros de Temperatura', icon='📌')
            st.metric(label="Média", value=f"{media_temperatura:.2f}")
            
        with total4:
            st.info('Média de Registros de Pressão', icon='📌')
            st.metric(label="Média", value=f"{media_pressao:.2f}")
            
        st.markdown("""-----""")

def graphs():
    # Define o título da página do dashboard
    st.title("Dashboard de Monitoramento")

    # Cria abas para diferentes seções do dashboard
    aba1, aba2, aba3, aba4 = st.tabs(["Gráficos de Média", "Registros Gerais", "Gráficos de Pizza", "Novos Gráficos"])
    
    with aba1:
        # Verifica se há dados disponíveis para gerar gráficos
        if df_selection.empty:
            st.write("Nenhum dado disponível para gerar gráficos.")
            return
        
        # Verifica se os eixos X e Y selecionados são diferentes para evitar gráficos inválidos
        if x_axis == y_axis:
            st.warning("Selecione uma opção diferente para os eixos X e Y.")
            return

        # Criação de um gráfico de barras horizontal para mostrar a contagem de registros por uma variável selecionada
        try:
            # Agrupa os dados pela variável escolhida para o eixo X e conta o número de registros em cada grupo
            grouped_data = df_selection.groupby(by=[x_axis]).size().reset_index(name='contagem')
            fig_valores = px.bar(
                grouped_data,
                x=x_axis,
                y='contagem',
                orientation='h',  # Define a orientação das barras como horizontal
                title=f"<b>Contagem de Registros por {x_axis.capitalize()}</b>",
                color_discrete_sequence=["#0083b8"],  # Define a cor das barras
                template="plotly_white"  # Define o tema do gráfico
            )
            
            fig_valores.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",  # Define o fundo do gráfico como transparente
                xaxis=dict(showgrid=False),  # Remove as linhas de grade do eixo X
                yaxis=dict(showgrid=False)   # Remove as linhas de grade do eixo Y
            )
        except Exception as e:
            # Mostra uma mensagem de erro caso ocorra algum problema ao criar o gráfico
            st.error(f"Erro ao criar o gráfico de valores: {e}")
            fig_valores = None
        
        # Criação de um gráfico de linha para mostrar a média de uma variável em função de outra
        try:
            # Agrupa os dados pela variável escolhida para o eixo X e calcula a média da variável do eixo Y
            grouped_data = df_selection.groupby(by=[x_axis]).agg({y_axis: 'mean'}).reset_index()
            fig_state = px.line(
                grouped_data,
                x=x_axis,
                y=y_axis,
                title=f"<b>Média de {y_axis.capitalize()} por {x_axis.capitalize()}</b>",
                color_discrete_sequence=["#0083b8"],  # Define a cor da linha
                template="plotly_white"  # Define o tema do gráfico
            )
            
            fig_state.update_layout(
                xaxis=dict(showgrid=False),  # Remove as linhas de grade do eixo X
                plot_bgcolor="rgba(0,0,0,0)",  # Define o fundo do gráfico como transparente
                yaxis=dict(showgrid=False)   # Remove as linhas de grade do eixo Y
            )
        except Exception as e:
            # Mostra uma mensagem de erro caso ocorra algum problema ao criar o gráfico
            st.error(f"Erro ao criar o gráfico de linha: {e}")
            fig_state = None
        
        # Exibe os gráficos criados lado a lado em duas colunas
        left, right = st.columns(2)
        if fig_state:
            with left:
                st.plotly_chart(fig_state, use_container_width=True)  # Exibe o gráfico de linha na coluna esquerda
        if fig_valores:
            with right:
                st.plotly_chart(fig_valores, use_container_width=True)  # Exibe o gráfico de barras na coluna direita

    with aba2:
        # Função para preparar os dados para o gráfico de linha geral
        def prepare_chart_data(df, columns):
            chart_data = pd.DataFrame()  # Cria um DataFrame vazio para armazenar os dados do gráfico
            for column in columns:
                if column in df.columns:
                    # Cria um DataFrame temporário com os valores da coluna e uma coluna de "registro" para identificação
                    temp_df = df[[column]].copy()
                    temp_df['registro'] = column
                    temp_df = temp_df.rename(columns={column: 'valor'})
                    chart_data = pd.concat([chart_data, temp_df])  # Concatena os dados temporários ao DataFrame principal
            return chart_data

        # Lista de colunas que serão incluídas no gráfico
        columns = ["temperatura", "umidade", "co2", "altitude", "pressao"]
        chart_data = prepare_chart_data(df_selection, columns)

        # Verifica se há dados para exibir
        if not chart_data.empty:
            # Cria um gráfico de linha para mostrar todos os registros gerais
            fig = px.line(
                chart_data,
                y="valor",
                color="registro",  # Diferencia as linhas no gráfico por cor
                title="Registros Gerais",
                labels={"valor": "Valor", "registro": "Tipo de Registro"}
            )
            fig.update_layout(
                xaxis_title="Índice",  # Define o título do eixo X
                yaxis_title="Valor",   # Define o título do eixo Y
                plot_bgcolor="rgba(0,0,0,0)"  # Define o fundo do gráfico como transparente
            )
            st.plotly_chart(fig, use_container_width=True)  # Exibe o gráfico
        else:
            st.write("Nenhum dado disponível para gerar gráficos.")
            
    with aba3:
        # Função para arredondar e agrupar dados em intervalos específicos
        def group_data(df, column, interval=None):
            if interval:
                df[column] = (df[column] // interval * interval).astype(int)  # Agrupa em intervalos específicos
            else:
                df[column] = df[column].astype(int)  # Arredonda para inteiros
            return df.groupby(by=column).size().reset_index(name='contagem')  # Conta a quantidade de registros em cada grupo

        # Lista de métricas para criar gráficos de pizza
        metrics = ['umidade', 'temperatura', 'co2', 'pressao', 'altitude']
        for metric in metrics:
            if metric in df_selection.columns:
                if metric in ['co2', 'pressao']:
                    # Agrupa CO2 e Pressão em intervalos específicos de 1000
                    pizza_data = group_data(df_selection, metric, interval=1000)
                else:
                    # Arredonda outras métricas para inteiros
                    pizza_data = group_data(df_selection, metric)
                
                if not pizza_data.empty:
                    # Cria um gráfico de pizza para a métrica selecionada
                    fig_pizza = px.pie(
                        pizza_data,
                        names=metric,
                        values='contagem',
                        title=f"<b>Distribuição dos Registros por {metric.capitalize()}</b>",
                        color_discrete_sequence=px.colors.sequential.Plasma  # Define a paleta de cores para o gráfico
                    )

                    fig_pizza.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)"  # Define o fundo do gráfico como transparente
                    )

                    st.plotly_chart(fig_pizza, use_container_width=True)  # Exibe o gráfico de pizza

    with aba4:
        # Prepara os dados para o gráfico de dispersão
        scatter_data = df_selection.copy()

        # Transforma o DataFrame para incluir uma coluna de "Variável" e valores "Valor"
        melted_data = pd.melt(
            scatter_data,
            id_vars=['umidade'],  # Inclua uma coluna para colorir os pontos
            value_vars=['temperatura', 'co2', 'altitude', 'pressao'],
            var_name='Variável',
            value_name='Valor'
        )

        # Verifica se há dados disponíveis para criar o gráfico
        if not melted_data.empty:
            # Cria um gráfico de dispersão com todas as variáveis, diferenciando por cor
            fig_scatter = px.scatter(
                melted_data,
                x='Valor',
                y='umidade',  # Usa 'umidade' como eixo Y para visualizar variação
                color='Variável',  # Diferencia os pontos por cor baseada na variável
                title="Dispersão de Variáveis com Cor Diferente",
                labels={'Valor': 'Valor', 'umidade': 'Umidade (%)'},
                color_discrete_map={  # Mapeia cores específicas para cada variável
                    'temperatura': 'blue',
                    'co2': 'red',
                    'altitude': 'green',
                    'pressao': 'orange'
                }
            )
            
            fig_scatter.update_layout(
                xaxis_title='Valor',  # Define o título do eixo X
                yaxis_title='Umidade (%)',  # Define o título do eixo Y
                plot_bgcolor="rgba(0,0,0,0)",  # Define o fundo do gráfico como transparente
                xaxis=dict(showgrid=False),  # Remove as linhas de grade do eixo X
                yaxis=dict(showgrid=False)   # Remove as linhas de grade do eixo Y
            )
            st.plotly_chart(fig_scatter, use_container_width=True)  # Exibe o gráfico de dispersão
        else:
            st.write("Nenhum dado disponível para gerar gráficos.")

# Chama a função para exibir os gráficos
Home()
graphs()
