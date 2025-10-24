# =======================================================
# 📊 ROBÔ POWER BI IA EDITION (DASHBOARD FINAL E COMPLETO)
# =======================================================

import pandas as pd
import unidecode
import dash
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# ---------------- CONFIGURAÇÕES GLOBAIS ----------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1SEeX-g_Wdl0XpdXt90nDgDBPrjbS3zh_8yvAVpoxpPs/export?format=xlsx"

TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"

# ---------------- FUNÇÕES AUXILIARES ----------------
def normalizar(nome):
    """Função de normalização de nome."""
    return unidecode.unidecode(
        nome.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
    )

def carregar_dados():
    """Lê a aba 'controle de processos', limpa espaços e mantem o formato original."""
    try:
        xls = pd.ExcelFile(SHEETS_URL)
        if "controle de processos" not in xls.sheet_names:
            raise Exception("Aba 'controle de processos' não encontrada.")
        df = pd.read_excel(xls, sheet_name="controle de processos")
        
        # Apenas remove espaços extras de cada nome de coluna (CRÍTICO)
        df.columns = [col.strip() for col in df.columns]
        
        print("✅ Dados carregados com sucesso do Google Sheets!")
        return df
    except Exception as e:
        print(f"❌ Erro crítico ao carregar planilha do Google Sheets: {e}")
        return pd.DataFrame()

# ---------------- NOMES ORIGINAIS DAS COLUNAS ----------------
# Estes são os nomes EXATOS, em MAIÚSCULO E COM ACENTO
COL_AREA = "ÁREA/PASTA"
COL_STATUS = "STATUS FINAL"
COL_UF = "UF/MUNICÍPIO"
COL_DATA_DIST = "DATA DISTRIBUIÇÃO"
COL_DISTRIBUIDO = "PROCESSO DISTRIBUÍDO"
COL_MES_COMP = "MÊS COMPETÊNCIA"
COL_RESPONSAVEL = "RESPONSÁVEL JURÍDICO"
COL_SLA = "STATUS SLA DISTRIBUIÇÃO"
COL_CONSULTOR = "CONSULTOR"


# ---------------- DASH APP ----------------
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "Power BI IA Edition - Controle de Processos Aprimorado"

# ---------------- LAYOUT ----------------
app.layout = dbc.Container([
    html.Br(),
    html.H1("🚀 Dashboard Master - Controle de Processos (FINAL)", 
            className="text-center text-info mb-4"),

    # KPI Cards 
    html.Div(id="controle-processos-kpis"),

    html.Br(),
    html.H5("🎛️ Filtros Interativos"),
    # Linha de filtros 1
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="filtro_area", placeholder=f"Filtrar por {COL_AREA}"), md=3),
        dbc.Col(dcc.Dropdown(id="filtro_status", placeholder=f"Filtrar por {COL_STATUS}"), md=3),
        dbc.Col(dcc.Dropdown(id="filtro_uf", placeholder=f"Filtrar por {COL_UF}"), md=3),
        dbc.Col(dcc.Dropdown(id="filtro_mes", placeholder=f"Filtrar por {COL_MES_COMP}"), md=3),
    ], className="mb-3"),
    # Linha de filtros 2: Inclui o CONSULTOR
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="filtro_responsavel", placeholder=f"Filtrar por {COL_RESPONSAVEL}"), md=6),
        dbc.Col(dcc.Dropdown(id="filtro_consultor", placeholder=f"Filtrar por {COL_CONSULTOR}"), md=6),
    ], className="mb-4"),

    # GRÁFICOS ATIVOS
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_area", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="grafico_status", config={"displayModeBar": False}), lg=6, md=12),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_tempo", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="grafico_responsavel", config={"displayModeBar": False}), lg=6, md=12),
    ]),

    # GRÁFICO DE SLA
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_sla", config={"displayModeBar": False}), md=12),
    ]),

    html.Hr(),
    html.H4("📋 Tabela de Processos (Amostra)", className="text-center"),
    html.Div(id="tabela_processos", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="timer_auto", interval=90000, n_intervals=0)
], fluid=True)


# ---------------- CALLBACK ----------------
@app.callback(
    [
        Output("filtro_area", "options"),
        Output("filtro_status", "options"),
        Output("filtro_uf", "options"),
        Output("filtro_mes", "options"),
        Output("filtro_responsavel", "options"), 
        Output("filtro_consultor", "options"), 
        Output("controle-processos-kpis", "children"),
        Output("grafico_area", "figure"), 
        Output("grafico_status", "figure"),
        Output("grafico_tempo", "figure"), 
        Output("grafico_responsavel", "figure"),
        Output("grafico_sla", "figure"),
        Output("tabela_processos", "children"),
        Output("status_recarregamento", "children")
    ],
    [Input("btn_recarregar", "n_clicks"),
     Input("timer_auto", "n_intervals"),
     Input("filtro_area", "value"),
     Input("filtro_status", "value"),
     Input("filtro_uf", "value"),
     Input("filtro_mes", "value"),
     Input("filtro_responsavel", "value"), 
     Input("filtro_consultor", "value")]
)
def atualizar_dashboard(n_clicks, n_timer, filtro_area, filtro_status, filtro_uf, filtro_mes, filtro_responsavel, filtro_consultor):
    df = carregar_dados()

    # 🚨 TRATAMENTO DE ERRO DE DADOS (Visual) 🚨
    if df.empty:
        error_kpis = dbc.Row(dbc.Col(html.Div([
            html.H4("❌ Falha Crítica ao Carregar Dados do Google Sheets", className="text-center text-danger mb-2"),
            html.P("Verifique o terminal para o erro de carregamento.", className="text-center")
        ]), width=12), className="mb-4")
        
        empty_opts = []
        empty_fig = {}
        
        return empty_opts, empty_opts, empty_opts, empty_opts, empty_opts, empty_opts, error_kpis, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, html.Div(), "❌ Falha ao carregar dados"

    # 🔹 Limpeza de strings: Tratamento seguro (Mantendo MAIÚSCULO/ACENTO)
    cols_to_clean = [COL_AREA, COL_STATUS, COL_UF, COL_MES_COMP, COL_RESPONSAVEL, COL_SLA, COL_DISTRIBUIDO, COL_CONSULTOR]
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")
            df[col] = df[col].str.strip()
            df[col] = df[col].replace(["NAN", "Na", ""], "")
            
    # 🔹 Aplicar filtros
    df_filtered = df.copy() 
    if filtro_area:
        df_filtered = df_filtered[df_filtered[COL_AREA] == filtro_area]
    if filtro_status:
        df_filtered = df_filtered[df_filtered[COL_STATUS] == filtro_status]
    if filtro_uf:
        df_filtered = df_filtered[df_filtered[COL_UF] == filtro_uf]
    if filtro_mes:
        df_filtered = df_filtered[df_filtered[COL_MES_COMP] == filtro_mes]
    if filtro_responsavel:
        df_filtered = df_filtered[df_filtered[COL_RESPONSAVEL] == filtro_responsavel]
    if filtro_consultor:
        df_filtered = df_filtered[df_filtered[COL_CONSULTOR] == filtro_consultor]

    df = df_filtered

    # 🔹 Dropdown options
    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    area_opts = get_options(COL_AREA)
    status_opts = get_options(COL_STATUS)
    uf_opts = get_options(COL_UF)
    mes_opts = get_options(COL_MES_COMP)
    responsavel_opts = get_options(COL_RESPONSAVEL) 
    consultor_opts = get_options(COL_CONSULTOR) 

    # === KPIs ===
    total = len(df)
    distribuidos = df[df[COL_DISTRIBUIDO].isin(["SIM", "CASO_ASTREA"])].shape[0]
    nao_distribuidos = total - distribuidos
    percentual = round((distribuidos / total) * 100, 2) if total > 0 else 0
    em_andamento = df[df[COL_STATUS] == "EM ANDAMENTO"].shape[0]
    sla_atrasado = df[df[COL_SLA].isin(["ATRASADO", "Atrasado"])].shape[0] if COL_SLA in df.columns else 0

    # Layout dos KPIs (6 colunas)
    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total Processos", className="text-center text-secondary"),
            html.H3(f"{total:,}", className="text-center text-primary"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total Distribuídos", className="text-center text-secondary"),
            html.H3(f"{distribuidos:,}", className="text-center text-success"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Não Distribuídos", className="text-center text-secondary"),
            html.H3(f"{nao_distribuidos:,}", className="text-center text-danger"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("% Distribuídos", className="text-center text-secondary"),
            html.H3(f"{percentual}%", className="text-center text-warning"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Em Andamento", className="text-center text-secondary"),
            html.H3(f"{em_andamento:,}", className="text-center text-info"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("SLA Atrasado", className="text-center text-secondary"),
            html.H3(f"{sla_atrasado:,}", className="text-center text-danger"),
        ]), color=COR_CARD_BG, inverse=True), md=2),
    ], className="mb-4")

    # === GRÁFICOS ===
    
    # Função auxiliar para criar DataFrame do gráfico (segura contra empty DataFrames)
    def create_chart_df(column):
        if column in df.columns and not df.empty:
            df_chart = df[df[column] != ""].copy()
            if not df_chart.empty:
                count_series = df_chart[column].value_counts().reset_index()
                count_series.columns = ['index', 'Quantidade']
                return count_series
        return pd.DataFrame() 

    # Gráfico 1: Processos por Área/Pasta (Barra)
    graf_area = {}
    df_area_chart = create_chart_df(COL_AREA)
    if not df_area_chart.empty:
        graf_area = px.bar(
            df_area_chart, x="index", y="Quantidade", title=f"Processos por {COL_AREA}", color="index",
            labels={"index": COL_AREA, "Quantidade": "Quantidade"}, template="plotly_dark"
        )
        graf_area.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), xaxis={'categoryorder': 'total descending'})
    
    # Gráfico 2: Distribuição por Status Final (Pizza)
    graf_status = {}
    df_status_chart = create_chart_df(COL_STATUS)
    if not df_status_chart.empty:
        graf_status = px.pie(
            df_status_chart, names="index", values="Quantidade", title=f"Distribuição por {COL_STATUS}",
            template="plotly_dark"
        )
        graf_status.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # Gráfico 3: Evolução Mensal de Distribuições (Linha)
    graf_tempo = {}
    try:
        if COL_DATA_DIST in df.columns:
            df[COL_DATA_DIST] = pd.to_datetime(df[COL_DATA_DIST], errors="coerce")
            df_dist = df.dropna(subset=[COL_DATA_DIST]).copy()
            
            if not df_dist.empty:
                serie = df_dist.groupby(df_dist[COL_DATA_DIST].dt.to_period("M")).size().reset_index(name="qtd")
                serie[COL_DATA_DIST] = serie[COL_DATA_DIST].astype(str)
                graf_tempo = px.line(
                    serie, x=COL_DATA_DIST, y="qtd", markers=True,
                    title="📅 Evolução Mensal de Distribuições",
                    labels={COL_DATA_DIST: "Mês", "qtd": "Distribuições"}, template="plotly_dark"
                )
                graf_tempo.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    except Exception:
        graf_tempo = {}

    # Gráfico 4: Processos por Responsável Jurídico (Top 10)
    graf_responsavel = {}
    df_resp_chart = create_chart_df(COL_RESPONSAVEL)
    if not df_resp_chart.empty and len(df_resp_chart) > 0:
        graf_responsavel = px.bar(
            df_resp_chart.head(10), y="index", x="Quantidade",
            title=f"Processos por {COL_RESPONSAVEL} (Top 10)",
            labels={"index": COL_RESPONSAVEL, "Quantidade": "Quantidade"},
            template="plotly_dark", orientation='h' 
        )
        graf_responsavel.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), yaxis={'categoryorder': 'total ascending'})

    # Gráfico 5: Distribuição do Status SLA
    graf_sla = {}
    df_sla_chart = create_chart_df(COL_SLA)
    if not df_sla_chart.empty:
        graf_sla = px.pie(
            df_sla_chart, names="index", values="Quantidade", title=f"Distribuição do {COL_SLA}",
            template="plotly_dark"
        )
        graf_sla.update_layout(margin=dict(l=20, r=20, t=40, b=20))

    # === TABELA ===
    colunas_tabela = [
        COL_MES_COMP, COL_RESPONSAVEL, COL_CONSULTOR, COL_AREA, COL_UF,
        COL_DISTRIBUIDO, COL_STATUS, COL_SLA
    ]
    tabela_df = df[[col for col in colunas_tabela if col in df.columns]].head(30)

    # CORREÇÃO CRÍTICA: Removendo o argumento `dark=True`
    tabela = html.Div()
    if not tabela_df.empty:
        tabela = dbc.Table.from_dataframe(
            tabela_df, striped=True, bordered=True, hover=True # ARGUMENTO dark=True REMOVIDO
        )

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (area_opts, status_opts, uf_opts, mes_opts, responsavel_opts, consultor_opts, 
            kpis, graf_area, graf_status, graf_tempo, graf_responsavel, graf_sla, 
            tabela, f"🕒 Atualizado às {hora}")


# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    app.run(debug=True)
