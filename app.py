# =======================================================
# 📊 ROBÔ POWER BI IA EDITION (DASHBOARD ÚNICO - CONTROLE DE PROCESSOS)
# =======================================================

import pandas as pd
import unidecode
import json
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
    """Normaliza nomes de colunas removendo acentos e caracteres especiais."""
    return unidecode.unidecode(
        nome.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
    )

def carregar_dados():
    """Lê a aba 'controle de processos' diretamente do Google Sheets."""
    try:
        xls = pd.ExcelFile(SHEETS_URL)
        if "controle de processos" not in xls.sheet_names:
            raise Exception("Aba 'controle de processos' não encontrada.")
        df = pd.read_excel(xls, sheet_name="controle de processos")
        df.columns = [col.strip() for col in df.columns]
        print("✅ Dados carregados com sucesso!")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar planilha: {e}")
        return pd.DataFrame()

# ---------------- DASH APP ----------------
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "Power BI IA Edition - Controle de Processos"

# ---------------- LAYOUT ----------------
app.layout = dbc.Container([
    html.Br(),
    html.H2("📂 Dashboard - Controle de Processos (Live Sheets)", 
            className="text-center text-info mb-4"),

    # KPI Cards
    html.Div(id="controle-processos-kpis"),

    html.Br(),
    html.H5("🎛️ Filtros Interativos"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="filtro_area", placeholder="Filtrar por Área/Pasta"), md=4),
        dbc.Col(dcc.Dropdown(id="filtro_status", placeholder="Filtrar por Status Final"), md=4),
        dbc.Col(dcc.Dropdown(id="filtro_uf", placeholder="Filtrar por UF/Município"), md=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_area", config={"displayModeBar": False}), md=6),
        dbc.Col(dcc.Graph(id="grafico_status", config={"displayModeBar": False}), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_tempo", config={"displayModeBar": False}), md=12),
    ]),

    html.Hr(),
    html.H4("📋 Tabela de Processos", className="text-center"),
    html.Div(id="tabela_processos", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="timer_auto", interval=90000, n_intervals=0)  # Atualiza a cada 90s
], fluid=True)


# ---------------- CALLBACK ----------------
@app.callback(
    [
        Output("filtro_area", "options"),
        Output("filtro_status", "options"),
        Output("filtro_uf", "options"),
        Output("controle-processos-kpis", "children"),
        Output("grafico_area", "figure"),
        Output("grafico_status", "figure"),
        Output("grafico_tempo", "figure"),
        Output("tabela_processos", "children"),
        Output("status_recarregamento", "children")
    ],
    [Input("btn_recarregar", "n_clicks"),
     Input("timer_auto", "n_intervals"),
     Input("filtro_area", "value"),
     Input("filtro_status", "value"),
     Input("filtro_uf", "value")]
)
def atualizar_dashboard(n_clicks, n_timer, filtro_area, filtro_status, filtro_uf):
    df = carregar_dados()

    if df.empty:
        raise PreventUpdate

    # 🔹 Mapeamento de colunas reais → nomes internos
    df = df.rename(columns={
        "ÁREA/PASTA": "area",
        "STATUS FINAL": "status",
        "UF/MUNICÍPIO": "uf",
        "DATA DISTRIBUIÇÃO": "data_distribuicao",
        "PROCESSO DISTRIBUÍDO": "distribuido",
        "MÊS COMPETÊNCIA": "mes_competencia"
    })

    # 🔹 Limpeza de strings
    for col in ["area", "status", "uf"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # 🔹 Aplicar filtros
    if filtro_area:
        df = df[df["area"] == filtro_area]
    if filtro_status:
        df = df[df["status"] == filtro_status]
    if filtro_uf:
        df = df[df["uf"] == filtro_uf]

    # 🔹 Dropdown options
    area_opts = [{"label": a, "value": a} for a in sorted(df["area"].dropna().unique())]
    status_opts = [{"label": s, "value": s} for s in sorted(df["status"].dropna().unique())]
    uf_opts = [{"label": u, "value": u} for u in sorted(df["uf"].dropna().unique())]

    # === KPIs ===
    total = len(df)
    distribuidos = df[df["distribuido"].astype(str).str.lower().str.contains("sim", na=False)].shape[0]
    percentual = round((distribuidos / total) * 100, 2) if total > 0 else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Total de Processos", className="text-center"),
            html.H3(f"{total:,}", className="text-center text-primary"),
        ])), md=4),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Distribuídos", className="text-center"),
            html.H3(f"{distribuidos:,}", className="text-center text-success"),
        ])), md=4),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("% Distribuídos", className="text-center"),
            html.H3(f"{percentual}%", className="text-center text-warning"),
        ])), md=4),
    ], className="mb-4")

    # === GRÁFICOS ===
    graf_area = px.bar(df, x="area", title="Processos por Área/Pasta", color="area") if "area" in df else {}
    graf_status = px.pie(df, names="status", title="Distribuição por Status Final") if "status" in df else {}

    try:
        df["data_distribuicao"] = pd.to_datetime(df["data_distribuicao"], errors="coerce")
        serie = df.groupby(df["data_distribuicao"].dt.to_period("M")).size().reset_index(name="qtd")
        serie["data_distribuicao"] = serie["data_distribuicao"].astype(str)
        graf_tempo = px.line(serie, x="data_distribuicao", y="qtd", markers=True,
                             title="📅 Evolução Mensal de Distribuições")
    except Exception:
        graf_tempo = {}

    # === TABELA ===
    tabela = dbc.Table.from_dataframe(df.head(30), striped=True, bordered=True, hover=True)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return area_opts, status_opts, uf_opts, kpis, graf_area, graf_status, graf_tempo, tabela, f"🕒 Atualizado às {hora}"


# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    app.run(debug=True)
