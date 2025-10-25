import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Importa as constantes e funções do arquivo utils.py
from utils import carregar_dados, CP_COL_AREA, CP_COL_STATUS, CP_COL_UF, CP_COL_DATA_DIST, CP_COL_DISTRIBUIDO, CP_COL_MES_COMP, CP_COL_RESPONSAVEL, CP_COL_SLA, CP_COL_CONSULTOR, COR_CARD_BG, TEMA_DARK

# ---------------- REGISTRO DA PÁGINA ----------------
register_page(
    __name__,
    name='📂 Controle de Processos',
    path='/', # Define como a página inicial (raiz)
    order=1,
    title='Controle de Processos'
)

# ---------------- LAYOUT DA PÁGINA ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("🚀 Dashboard Master - Controle de Processos (Live Sheets)", 
            className="text-center text-info mb-4"),

    # KPI Cards 
    html.Div(id="cp-kpis"),

    html.Br(),
    html.H5("🎛️ Filtros Interativos"),
    # Linha de filtros 1
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="cp_filtro_area", placeholder=f"Filtrar por {CP_COL_AREA}"), md=3),
        dbc.Col(dcc.Dropdown(id="cp_filtro_status", placeholder=f"Filtrar por {CP_COL_STATUS}"), md=3),
        dbc.Col(dcc.Dropdown(id="cp_filtro_uf", placeholder=f"Filtrar por {CP_COL_UF}"), md=3),
        dbc.Col(dcc.Dropdown(id="cp_filtro_mes", placeholder=f"Filtrar por {CP_COL_MES_COMP}"), md=3),
    ], className="mb-3"),
    # Linha de filtros 2
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="cp_filtro_responsavel", placeholder=f"Filtrar por {CP_COL_RESPONSAVEL}"), md=6),
        dbc.Col(dcc.Dropdown(id="cp_filtro_consultor", placeholder=f"Filtrar por {CP_COL_CONSULTOR}"), md=6),
    ], className="mb-4"),

    # GRÁFICOS
    dbc.Row([
        dbc.Col(dcc.Graph(id="cp_grafico_area", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="cp_grafico_status", config={"displayModeBar": False}), lg=6, md=12),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="cp_grafico_tempo", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="cp_grafico_responsavel", config={"displayModeBar": False}), lg=6, md=12),
    ]),

    # GRÁFICO DE SLA
    dbc.Row([
        dbc.Col(dcc.Graph(id="cp_grafico_sla", config={"displayModeBar": False}), md=12),
    ]),

    html.Hr(),
    html.H4("📋 Tabela de Processos (Amostra)", className="text-center"),
    html.Div(id="cp_tabela_processos", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="cp_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="cp_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="cp_timer_auto", interval=90000, n_intervals=0)
], fluid=True)


# ---------------- CALLBACK DA PÁGINA ----------------
@dash.callback(
    [
        Output("cp_filtro_area", "options"),
        Output("cp_filtro_status", "options"),
        Output("cp_filtro_uf", "options"),
        Output("cp_filtro_mes", "options"),
        Output("cp_filtro_responsavel", "options"), 
        Output("cp_filtro_consultor", "options"), 
        Output("cp-kpis", "children"),
        Output("cp_grafico_area", "figure"), 
        Output("cp_grafico_status", "figure"),
        Output("cp_grafico_tempo", "figure"), 
        Output("cp_grafico_responsavel", "figure"),
        Output("cp_grafico_sla", "figure"),
        Output("cp_tabela_processos", "children"),
        Output("cp_status_recarregamento", "children")
    ],
    [Input("cp_btn_recarregar", "n_clicks"),
     Input("cp_timer_auto", "n_intervals"),
     Input("cp_filtro_area", "value"),
     Input("cp_filtro_status", "value"),
     Input("cp_filtro_uf", "value"),
     Input("cp_filtro_mes", "value"),
     Input("cp_filtro_responsavel", "value"), 
     Input("cp_filtro_consultor", "value")]
)
def atualizar_dashboard_cp(n_clicks, n_timer, filtro_area, filtro_status, filtro_uf, filtro_mes, filtro_responsavel, filtro_consultor):
    df = carregar_dados("controle de processos")

    if df.empty:
        error_kpis = dbc.Row(dbc.Col(html.Div([html.H4("❌ Falha Crítica ao Carregar Dados", className="text-center text-danger mb-2")]), width=12), className="mb-4")
        empty_opts = []
        empty_fig = {}
        return empty_opts, empty_opts, empty_opts, empty_opts, empty_opts, empty_opts, error_kpis, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, html.Div(), "❌ Falha ao carregar dados"

    # 🔹 Limpeza de strings: Tratamento seguro (Mantendo MAIÚSCULO/ACENTO)
    cols_to_clean = [CP_COL_AREA, CP_COL_STATUS, CP_COL_UF, CP_COL_MES_COMP, CP_COL_RESPONSAVEL, CP_COL_SLA, CP_COL_DISTRIBUIDO, CP_COL_CONSULTOR]
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")
            df[col] = df[col].str.strip()
            df[col] = df[col].replace(["NAN", "Na", ""], "")
            
    # 🔹 Aplicar filtros
    df_filtered = df.copy() 
    if filtro_area:
        df_filtered = df_filtered[df_filtered[CP_COL_AREA] == filtro_area]
    if filtro_status:
        df_filtered = df_filtered[df_filtered[CP_COL_STATUS] == filtro_status]
    if filtro_uf:
        df_filtered = df_filtered[df_filtered[CP_COL_UF] == filtro_uf]
    if filtro_mes:
        df_filtered = df_filtered[df_filtered[CP_COL_MES_COMP] == filtro_mes]
    if filtro_responsavel:
        df_filtered = df_filtered[df_filtered[CP_COL_RESPONSAVEL] == filtro_responsavel]
    if filtro_consultor:
        df_filtered = df_filtered[df_filtered[CP_COL_CONSULTOR] == filtro_consultor]

    df = df_filtered

    # 🔹 Dropdown options
    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    area_opts = get_options(CP_COL_AREA)
    status_opts = get_options(CP_COL_STATUS)
    uf_opts = get_options(CP_COL_UF)
    mes_opts = get_options(CP_COL_MES_COMP)
    responsavel_opts = get_options(CP_COL_RESPONSAVEL) 
    consultor_opts = get_options(CP_COL_CONSULTOR) 

    # === KPIs ===
    total = len(df)
    distribuidos = df[df[CP_COL_DISTRIBUIDO].isin(["SIM", "CASO_ASTREA"])].shape[0]
    nao_distribuidos = total - distribuidos
    percentual = round((distribuidos / total) * 100, 2) if total > 0 else 0
    em_andamento = df[df[CP_COL_STATUS] == "EM ANDAMENTO"].shape[0]
    sla_atrasado = df[df[CP_COL_SLA].isin(["ATRASADO", "Atrasado"])].shape[0] if CP_COL_SLA in df.columns else 0

    # Layout dos KPIs (6 colunas)
    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Total Processos", className="text-center text-secondary"), html.H3(f"{total:,}", className="text-center text-primary")]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Total Distribuídos", className="text-center text-secondary"), html.H3(f"{distribuidos:,}", className="text-center text-success")]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Não Distribuídos", className="text-center text-secondary"), html.H3(f"{nao_distribuidos:,}", className="text-center text-danger")]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("% Distribuídos", className="text-center text-secondary"), html.H3(f"{percentual}%", className="text-center text-warning")]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Em Andamento", className="text-center text-secondary"), html.H3(f"{em_andamento:,}", className="text-center text-info")]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("SLA Atrasado", className="text-center text-secondary"), html.H3(f"{sla_atrasado:,}", className="text-center text-danger")]), color=COR_CARD_BG, inverse=True), md=2),
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

    graf_area, graf_status, graf_tempo, graf_responsavel, graf_sla = [{} for _ in range(5)]

    # Gráfico 1: Área
    df_area_chart = create_chart_df(CP_COL_AREA, df)
    if not df_area_chart.empty:
        graf_area = px.bar(df_area_chart, x="index", y="Quantidade", title=f"Processos por {CP_COL_AREA}", color="index", labels={"index": CP_COL_AREA, "Quantidade": "Quantidade"}, template="plotly_dark")
        graf_area.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), xaxis={'categoryorder': 'total descending'})
    
    # Gráfico 2: Status
    df_status_chart = create_chart_df(CP_COL_STATUS, df)
    if not df_status_chart.empty:
        graf_status = px.pie(df_status_chart, names="index", values="Quantidade", title=f"Distribuição por {CP_COL_STATUS}", template="plotly_dark")
        graf_status.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # Gráfico 3: Tempo
    try:
        if CP_COL_DATA_DIST in df.columns:
            df[CP_COL_DATA_DIST] = pd.to_datetime(df[CP_COL_DATA_DIST], errors="coerce")
            df_dist = df.dropna(subset=[CP_COL_DATA_DIST]).copy()
            if not df_dist.empty:
                serie = df_dist.groupby(df_dist[CP_COL_DATA_DIST].dt.to_period("M")).size().reset_index(name="qtd")
                serie[CP_COL_DATA_DIST] = serie[CP_COL_DATA_DIST].astype(str)
                graf_tempo = px.line(serie, x=CP_COL_DATA_DIST, y="qtd", markers=True, title="📅 Evolução Mensal de Distribuições", labels={CP_COL_DATA_DIST: "Mês", "qtd": "Distribuições"}, template="plotly_dark")
                graf_tempo.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    except Exception:
        pass

    # Gráfico 4: Responsável
    df_resp_chart = create_chart_df(CP_COL_RESPONSAVEL, df)
    if not df_resp_chart.empty and len(df_resp_chart) > 0:
        graf_responsavel = px.bar(df_resp_chart.head(10), y="index", x="Quantidade", title=f"Processos por {CP_COL_RESPONSAVEL} (Top 10)", labels={"index": CP_COL_RESPONSAVEL, "Quantidade": "Quantidade"}, template="plotly_dark", orientation='h')
        graf_responsavel.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), yaxis={'categoryorder': 'total ascending'})

    # Gráfico 5: SLA
    df_sla_chart = create_chart_df(CP_COL_SLA, df)
    if not df_sla_chart.empty:
        graf_sla = px.pie(df_sla_chart, names="index", values="Quantidade", title=f"Distribuição do {CP_COL_SLA}", template="plotly_dark")
        graf_sla.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # TABELA
    colunas_tabela = [CP_COL_MES_COMP, CP_COL_RESPONSAVEL, CP_COL_CONSULTOR, CP_COL_AREA, CP_COL_UF, CP_COL_DISTRIBUIDO, CP_COL_STATUS, CP_COL_SLA]
    tabela_df = df[[col for col in colunas_tabela if col in df.columns]].head(30)

    tabela = html.Div()
    if not tabela_df.empty:
        tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (area_opts, status_opts, uf_opts, mes_opts, responsavel_opts, consultor_opts, kpis, graf_area, graf_status, graf_tempo, graf_responsavel, graf_sla, tabela, f"🕒 Atualizado às {hora}")