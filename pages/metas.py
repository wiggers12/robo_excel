import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Importa as constantes e funções do arquivo utils.py
# (Presume que utils.py existe na raiz do projeto)
from utils import carregar_dados, COR_CARD_BG, TEMA_DARK

# ---------------- NOMES COLUNAS - METAS POR PASTA (MP) ----------------
# Nomes das colunas da aba "Metas por pasta" (ajustados para serem lidos pelo código)
MP_COL_MES = "MÊS"
MP_COL_META_MENSAL = "META MENSAL/PASTA"
MP_COL_META_MINIMA = "META MENSAL ÁREA/MÍNIMO ESPERADO"
MP_COL_META_ATINGIDA = "META MENSAL ATINGIDA"
MP_COL_PERCENTUAL_ATINGIMENTO = "% Atingimento Contratos:"
MP_COL_LEADS_RECEBIDOS = "LEADS RECEBIDOS POR ÁREA/MÊS"
MP_COL_TAXA_CONVERSAO = "TAXA DE CONVERSÃO POR ÁREA/MÊS"
MP_COL_POTENCIAL_50 = "POTENCIAL A ATINGIR(se cumprido a meta mensal individual em + 50%)"
MP_COL_POTENCIAL_100 = "POTENCIAL A ATINGIR(se cumprido a meta mensal individual em 100%)"
PASTA_COL_INDEX = 1 # A coluna de Pasta/Área é a segunda (índice 1)


# ---------------- REGISTRO DA PÁGINA ----------------
register_page(
    __name__,
    name='🏆 Metas por Pasta',
    path='/metas',
    order=3, # Terceira página na NavBar
    title='Metas por Pasta'
)

# ---------------- LAYOUT DA PÁGINA ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("🏆 Dashboard - Metas por Pasta e Desempenho", 
            className="text-center text-success mb-4"),

    # KPI Cards (Total de Desempenho)
    html.Div(id="mp-kpis"),

    html.Br(),
    html.H5("🎛️ Filtros Interativos"),
    # Linha de filtros
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="mp_filtro_mes", placeholder=f"Filtrar por {MP_COL_MES}"), md=6),
        dbc.Col(dcc.Dropdown(id="mp_filtro_pasta", placeholder="Filtrar por Área/Pasta"), md=6),
    ], className="mb-4"),

    # Gráficos de Metas e Conversão
    dbc.Row([
        dbc.Col(dcc.Graph(id="mp_grafico_atingimento", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="mp_grafico_conversao", config={"displayModeBar": False}), lg=6, md=12),
    ]),
    
    # Gráfico de Potencial
    dbc.Row([
        dbc.Col(dcc.Graph(id="mp_grafico_potencial", config={"displayModeBar": False}), md=12),
    ]),

    html.Hr(),
    html.H4("📋 Tabela de Metas Detalhada", className="text-center"),
    html.Div(id="mp_tabela_metas", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="mp_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="mp_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="mp_timer_auto", interval=90000, n_intervals=0)
], fluid=True)


# ---------------- CALLBACK DA PÁGINA ----------------
@dash.callback(
    [
        Output("mp_filtro_mes", "options"),
        Output("mp_filtro_pasta", "options"),
        Output("mp-kpis", "children"),
        Output("mp_grafico_atingimento", "figure"),
        Output("mp_grafico_conversao", "figure"),
        Output("mp_grafico_potencial", "figure"),
        Output("mp_tabela_metas", "children"),
        Output("mp_status_recarregamento", "children")
    ],
    [
        Input("mp_btn_recarregar", "n_clicks"),
        Input("mp_timer_auto", "n_intervals"),
        Input("mp_filtro_mes", "value"),
        Input("mp_filtro_pasta", "value")
    ]
)
def atualizar_dashboard_metas(n_clicks, n_timer, filtro_mes, filtro_pasta):
    # Carrega os dados da aba "Metas por pasta" do link online
    df = carregar_dados("Metas por pasta")

    # 🚨 Tratamento de Erro Básico
    if df.empty:
        error_kpis = dbc.Row(dbc.Col(html.Div([html.H4("❌ Falha Crítica ao Carregar Dados de Metas", className="text-center text-danger mb-2")]), width=12), className="mb-4")
        empty_opts, empty_fig = [], {}
        # Retorna 8 saídas
        return empty_opts, empty_opts, error_kpis, empty_fig, empty_fig, empty_fig, html.Div(), "❌ Falha ao carregar dados"

    # Mapeamento de Coluna de Pasta (É a segunda coluna, índice 1)
    PASTA_COL = df.columns[PASTA_COL_INDEX] 

    # 🔹 Limpeza e Conversão
    cols_to_clean = [MP_COL_MES, PASTA_COL]
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip() # Remove espaços
            df[col] = df[col].replace(["Nan", "Na", ""], "") # Limpa nulos
    
    # Converte colunas percentuais e numéricas para float/int
    for col in [MP_COL_PERCENTUAL_ATINGIMENTO, MP_COL_TAXA_CONVERSAO]:
        if col in df.columns:
            # Multiplica por 100 aqui para trabalhar com porcentagens inteiras no código, mas o Plotly não precisa
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in [MP_COL_META_MENSAL, MP_COL_META_ATINGIDA, MP_COL_LEADS_RECEBIDOS, MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)


    # 🔹 Aplicação de filtros
    df_filtered = df.copy() 
    if filtro_mes:
        df_filtered = df_filtered[df_filtered[MP_COL_MES] == filtro_mes]
    if filtro_pasta:
        df_filtered = df_filtered[df_filtered[PASTA_COL] == filtro_pasta]

    df = df_filtered

    # 🔹 Dropdown options
    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    mes_opts = get_options(MP_COL_MES)
    pasta_opts = get_options(PASTA_COL)


    # === KPIs de Desempenho Total ===
    total_metas_atingidas = df[MP_COL_META_ATINGIDA].sum()
    total_metas_esperadas = df[MP_COL_META_MENSAL].sum()
    taxa_conversao_media = df[MP_COL_TAXA_CONVERSAO].mean() * 100 # Média em percentual (0-100)
    
    atingimento_geral = round((total_metas_atingidas / total_metas_esperadas) * 100, 2) if total_metas_esperadas > 0 else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total de Metas Atingidas", className="text-center text-secondary"),
            html.H3(f"{total_metas_atingidas:,.0f}", className="text-center text-primary"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Meta Mensal Total", className="text-center text-secondary"),
            html.H3(f"{total_metas_esperadas:,.0f}", className="text-center text-warning"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Atingimento Geral", className="text-center text-secondary"),
            html.H3(f"{atingimento_geral}%", className="text-center text-success"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Taxa de Conversão Média", className="text-center text-secondary"),
            html.H3(f"{taxa_conversao_media:.2f}%", className="text-center text-info"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
    ], className="mb-4")

    # === GRÁFICOS ===
    
    # Gráfico 1: Atingimento de Metas por Pasta
    graf_atingimento = {}
    if not df.empty:
        df_atingimento = df.groupby(PASTA_COL).sum(numeric_only=True).reset_index()
        df_atingimento['Diferença'] = df_atingimento[MP_COL_META_MENSAL] - df_atingimento[MP_COL_META_ATINGIDA]
        
        # Cria um DataFrame para Stacked Bar
        df_stack = pd.DataFrame({
            PASTA_COL: df_atingimento[PASTA_COL],
            'Atingida': df_atingimento[MP_COL_META_ATINGIDA],
            'Falta Atingir': df_atingimento['Diferença'].clip(lower=0) 
        })
        df_stack_melted = df_stack.melt(id_vars=PASTA_COL, var_name="Status", value_name="Quantidade")
        
        graf_atingimento = px.bar(
            df_stack_melted,
            x="Quantidade",
            y=PASTA_COL,
            color="Status",
            title="Atingimento de Metas por Área/Pasta",
            labels={"Quantidade": "Total de Metas", PASTA_COL: "Área/Pasta", "Status": "Status da Meta"},
            template="plotly_dark",
            orientation='h'
        )
        graf_atingimento.update_layout(margin=dict(l=20, r=20, t=40, b=20), legend_title_text='')

    # Gráfico 2: Taxa de Conversão por Mês (Linha)
    graf_conversao = {}
    if not df.empty and MP_COL_TAXA_CONVERSAO in df.columns:
        # Garante a ordenação temporal das médias
        df_conversao = df.groupby(MP_COL_MES).mean(numeric_only=True).reset_index()
        
        graf_conversao = px.line(
            df_conversao,
            x=MP_COL_MES,
            y=MP_COL_TAXA_CONVERSAO,
            title="Taxa de Conversão Média por Mês",
            labels={MP_COL_MES: "Mês", MP_COL_TAXA_CONVERSAO: "Taxa de Conversão"},
            template="plotly_dark",
            markers=True
        )
        # Formata o eixo Y para porcentagem
        graf_conversao.update_layout(margin=dict(l=20, r=20, t=40, b=20), yaxis={'tickformat': '.2%'})
        
    # Gráfico 3: Potencial de Atingimento (Comparação 50% vs 100%)
    graf_potencial = {}
    if not df.empty and MP_COL_POTENCIAL_50 in df.columns:
        df_potencial = df.groupby(PASTA_COL).sum(numeric_only=True).reset_index()
        
        # Seleciona as colunas de potencial e derrete
        df_melt = df_potencial.melt(
            id_vars=PASTA_COL, 
            value_vars=[MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100],
            var_name="Cenário", 
            value_name="Potencial de Metas"
        )
        
        graf_potencial = px.bar(
            df_melt,
            x=PASTA_COL,
            y="Potencial de Metas",
            color="Cenário",
            title="Potencial de Metas Atingíveis por Área",
            labels={PASTA_COL: "Área/Pasta", "Potencial de Metas": "Metas Potenciais"},
            template="plotly_dark"
        )
        graf_potencial.update_layout(margin=dict(l=20, r=20, t=40, b=20), barmode='group')


    # === TABELA ===
    tabela_df = df.copy()
    
    # Remove as colunas POTENCIAL do display da tabela para limpeza, mas mantém o restante
    cols_to_display = [col for col in tabela_df.columns if col not in [MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100, MP_COL_META_MINIMA]]
    tabela_df = tabela_df[cols_to_display].head(30)
    
    tabela = html.Div()
    if not tabela_df.empty:
        tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (mes_opts, pasta_opts, kpis, graf_atingimento, graf_conversao, graf_potencial, tabela, f"🕒 Atualizado às {hora}")