import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# NOTE: Supondo que você criou o 'utils.py' na raiz do projeto.
from utils import carregar_dados, TEMA_DARK, COR_CARD_BG, FP_COL_CONSULTOR, FP_COL_STATUS, FP_COL_MOTIVO, FP_COL_PLATFORM, FP_COL_UF, FP_COL_ORIGEM, FP_COL_MES, FP_COL_NOME, FP_COL_TELEFONE

# ---------------- REGISTRO DA PÁGINA ----------------
register_page(
    __name__,
    name='📈 Funil de Precatório',
    path='/funil',
    order=2, # Segunda página na NavBar
    title='Funil de Precatório'
)

# ---------------- LAYOUT DA PÁGINA ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("📈 Dashboard - Funil de Precatório (Live Sheets)", 
            className="text-center text-warning mb-4"),

    # KPI Cards
    html.Div(id="fp-kpis"),

    html.Br(),
    html.H5("🎛️ Filtros Interativos"),
    # Linha de filtros
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="fp_filtro_consultor", placeholder=f"Filtrar por {FP_COL_CONSULTOR}"), md=3),
        dbc.Col(dcc.Dropdown(id="fp_filtro_platform", placeholder=f"Filtrar por {FP_COL_PLATFORM.title()}"), md=3),
        dbc.Col(dcc.Dropdown(id="fp_filtro_uf", placeholder=f"Filtrar por {FP_COL_UF}"), md=3),
        dbc.Col(dcc.Dropdown(id="fp_filtro_mes", placeholder=f"Filtrar por {FP_COL_MES}"), md=3),
    ], className="mb-4"),

    # Gráfico de Funil e Gráfico de Origem
    dbc.Row([
        dbc.Col(dcc.Graph(id="fp_grafico_funil_status", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="fp_grafico_origem", config={"displayModeBar": False}), lg=6, md=12),
    ]),
    
    # Gráfico de Motivos (Detalhamento)
    dbc.Row([
        dbc.Col(dcc.Graph(id="fp_grafico_motivos", config={"displayModeBar": False}), md=12),
    ]),


    html.Hr(),
    html.H4("📋 Tabela de Leads", className="text-center"),
    html.Div(id="fp_tabela_funil", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="fp_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="fp_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="fp_timer_auto", interval=90000, n_intervals=0)
], fluid=True)


# ---------------- CALLBACK DA PÁGINA ----------------
@dash.callback(
    [
        Output("fp_filtro_consultor", "options"),
        Output("fp_filtro_platform", "options"),
        Output("fp_filtro_uf", "options"),
        Output("fp_filtro_mes", "options"),
        Output("fp-kpis", "children"),
        Output("fp_grafico_funil_status", "figure"),
        Output("fp_grafico_origem", "figure"),
        Output("fp_grafico_motivos", "figure"),
        Output("fp_tabela_funil", "children"),
        Output("fp_status_recarregamento", "children")
    ],
    [
        Input("fp_btn_recarregar", "n_clicks"),
        Input("fp_timer_auto", "n_intervals"),
        Input("fp_filtro_consultor", "value"),
        Input("fp_filtro_platform", "value"),
        Input("fp_filtro_uf", "value"),
        Input("fp_filtro_mes", "value")
    ]
)
def atualizar_dashboard_funil(n_clicks, n_timer, filtro_consultor, filtro_platform, filtro_uf, filtro_mes):
    df = carregar_dados("Funil de precatorio")

    if df.empty:
        error_kpis = dbc.Row(dbc.Col(html.Div([html.H4("❌ Falha Crítica ao Carregar Dados do Funil", className="text-center text-danger mb-2")]), width=12), className="mb-4")
        empty_opts = []
        empty_fig = {}
        return empty_opts, empty_opts, empty_opts, empty_opts, error_kpis, empty_fig, empty_fig, empty_fig, html.Div(), "❌ Falha ao carregar dados"

    # 🔹 Limpeza de strings: Padronização
    cols_to_clean = [FP_COL_CONSULTOR, FP_COL_STATUS, FP_COL_MOTIVO, FP_COL_PLATFORM, FP_COL_UF, FP_COL_ORIGEM, FP_COL_MES]
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title().replace(["Nan", "Na", ""], "")
            
    # 🔹 Aplicação de filtros
    df_filtered = df.copy() 
    if filtro_consultor:
        df_filtered = df_filtered[df_filtered[FP_COL_CONSULTOR] == filtro_consultor]
    if filtro_platform:
        df_filtered = df_filtered[df_filtered[FP_COL_PLATFORM] == filtro_platform]
    if filtro_uf:
        df_filtered = df_filtered[df_filtered[FP_COL_UF] == filtro_uf]
    if filtro_mes:
        df_filtered = df_filtered[df_filtered[FP_COL_MES] == filtro_mes]

    df = df_filtered

    # 🔹 Dropdown options
    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    consultor_opts = get_options(FP_COL_CONSULTOR)
    platform_opts = get_options(FP_COL_PLATFORM)
    uf_opts = get_options(FP_COL_UF)
    mes_opts = get_options(FP_COL_MES)

    # === KPIs ===
    total_leads = len(df)
    leads_pendentes = df[df[FP_COL_STATUS] == "Pendente"].shape[0]
    leads_em_andamento = df[df[FP_COL_STATUS] == "Em Andamento"].shape[0]
    conversao_final = df[df[FP_COL_STATUS].isin(["Fechado", "Distribuído", "Processo Distribuído"])].shape[0]
    taxa_conversao = round((conversao_final / total_leads) * 100, 2) if total_leads > 0 else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Total de Leads", className="text-center text-secondary"), html.H3(f"{total_leads:,}", className="text-center text-primary")]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Leads Pendentes", className="text-center text-secondary"), html.H3(f"{leads_pendentes:,}", className="text-center text-info")]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Leads em Andamento", className="text-center text-secondary"), html.H3(f"{leads_em_andamento:,}", className="text-center text-warning")]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Taxa de Conversão", className="text-center text-secondary"), html.H3(f"{taxa_conversao}%", className="text-center text-success")]), color=COR_CARD_BG, inverse=True), md=3),
    ], className="mb-4")

    # === GRÁFICOS ===
    
    def create_chart_df(column, current_df):
        if column in current_df.columns and not current_df.empty:
            df_chart = current_df[current_df[column] != ""].copy()
            if not df_chart.empty:
                count_series = df_chart[column].value_counts().reset_index()
                count_series.columns = ['index', 'Quantidade']
                return count_series
        return pd.DataFrame() 

    # Gráfico 1: Funil de Status (Principal)
    graf_funil_status = {}
    df_funil_chart = create_chart_df(FP_COL_STATUS, df)
    if not df_funil_chart.empty:
        status_ordem = ["Pendente", "Follow-Up", "Em Andamento", "Negociação", "Fechado", "Perdido"]
        df_funil_chart['Status'] = pd.Categorical(df_funil_chart['index'], categories=status_ordem, ordered=True)
        df_funil_chart = df_funil_chart.sort_values('Status').dropna(subset=['Status'])
        
        graf_funil_status = px.funnel(df_funil_chart, x="Quantidade", y="Status", title="Funil de Leads por Status", template="plotly_dark")
        graf_funil_status.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # Gráfico 2: Distribuição por Origem
    graf_origem = {}
    df_origem_chart = create_chart_df(FP_COL_ORIGEM, df)
    if not df_origem_chart.empty:
        df_origem_chart.columns = ['Origem', 'Quantidade']
        graf_origem = px.pie(df_origem_chart, names="Origem", values="Quantidade", title="Distribuição por Origem do Precatório", template="plotly_dark")
        graf_origem.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # Gráfico 3: Motivos (Detalhamento)
    graf_motivos = {}
    df_motivos_chart = create_chart_df(FP_COL_MOTIVO, df)
    if not df_motivos_chart.empty:
        graf_motivos = px.bar(
            df_motivos_chart.head(10), 
            x="index", 
            y="Quantidade", 
            title="Motivos Mais Comuns (Top 10)", 
            labels={"index": "Motivo", "Quantidade": "Quantidade"},
            template="plotly_dark",
            color="index"
        )
        graf_motivos.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), xaxis={'categoryorder': 'total descending'})


    # TABELA
    colunas_tabela = [FP_COL_NOME, FP_COL_CONSULTOR, FP_COL_STATUS, FP_COL_MOTIVO, FP_COL_PLATFORM, FP_COL_UF, FP_COL_TELEFONE, FP_COL_MES]
    tabela_df = df[[col for col in colunas_tabela if col in df.columns]].head(30)

    tabela = html.Div()
    if not tabela_df.empty:
        tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (consultor_opts, platform_opts, uf_opts, mes_opts, kpis, 
            graf_funil_status, graf_origem, graf_motivos, tabela, f"🕒 Atualizado às {hora}")