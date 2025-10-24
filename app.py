# =======================================================
# 📊 ROBÔ POWER BI IA EDITION (V5.2 - MÁXIMA RESPONSIVIDADE & SINTAXE CORRIGIDA)
# Autor: Dionatan Wiggers
# =======================================================

import pandas as pd
import unidecode
import json 
from dash import Dash, dcc, html, Input, Output, dash_table, State
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# ---------------- CONFIGURAÇÕES GLOBAIS ----------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1SEeX-g_Wdl0XpdXt90nDgDBPrjbS3zh_8yvAVpoxpPs/export?format=xlsx"
TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"
ABA_PRINCIPAL = "Dados Originais"

COLUNAS_MAP = {
    "col_uf": ["uf", "munic", "local"],
    "col_status": ["status", "status_final", "situacao"],
    "col_cons": ["consultor", "responsavel", "comercial"],
    "col_ass": ["assinatura", "data_assinatura"],
    "col_dist": ["distribuicao", "data_distribuicao"],
    "col_mes": ["mes", "mes_competencia", "mes_ref"],
    "col_area": ["area", "pasta", "setor"]
}

def normalizar(nome):
    """Normaliza colunas."""
    return unidecode.unidecode(nome.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_"))

def carregar_abas():
    """Carrega todas as abas e retorna um dicionário de JSON strings."""
    try:
        xls = pd.ExcelFile(SHEETS_URL)
        abas = {}
        for aba in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=aba)
            df.columns = [normalizar(c) for c in df.columns]
            abas[aba] = df.to_json(date_format='iso', orient='split')
        print(f"✅ Recarga completa! {len(abas)} abas carregadas.")
        return json.dumps(abas)
    except Exception as e:
        print(f"❌ Erro ao carregar Google Sheets: {e}")
        return None

# ---------------- APP ----------------
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server 
app.title = "Power BI IA Edition 5.2 (Responsivo)"

app.layout = dbc.Container(fluid=True, children=[
    html.Br(),
    html.H2("📈 Controle de Processos (Google Sheets IA Edition 5.2)", 
             style={"textAlign": "center", "color": "#fff"}),
    html.Br(),
    
    dcc.Store(id="data_store", data=None), 
    
    # ---------- FILTROS (Sintaxe Corrigida e Responsiva) ----------
    dbc.Card(
        dbc.CardBody(
            dbc.Row([
                # Filtros de Data (xs=12, md=6, lg=3)
                dbc.Col(dcc.DatePickerRange(
                    id='filtro_data_ass', start_date_placeholder_text="Assinatura (Início)", 
                    end_date_placeholder_text="Assinatura (Fim)", display_format="DD/MM/YYYY"
                ), xs=12, md=6, lg=3),
                dbc.Col(dcc.DatePickerRange(
                    id='filtro_data_dist', start_date_placeholder_text="Distribuição (Início)",
                    end_date_placeholder_text="Distribuição (Fim)", display_format="DD/MM/YYYY"
                ), xs=12, md=6, lg=3),
                
                # Dropdowns (xs=12, sm=6, lg=2)
                dbc.Col(dcc.Dropdown(id='filtro_uf', placeholder="UF/Município", multi=True), xs=12, sm=6, lg=2),
                dbc.Col(dcc.Dropdown(id='filtro_status', placeholder="Status Final", multi=True), xs=12, sm=6, lg=2),
                dbc.Col(dcc.Dropdown(id='filtro_consultor', placeholder="Consultor/Responsável", multi=True), xs=12, sm=6, lg=2),

            ], className="g-3 justify-content-center") # FIM DO dbc.Row
        ), # FIM DO dbc.CardBody
        style={"marginBottom": "20px"} # FIM DO dbc.Card (Argumentos)
    ), # FIM DO dbc.Card
    # -----------------------------------------------------------

    # --- Layout Principal ---
    html.Div(id="cards", style={"display": "flex", "justifyContent": "space-around", "flexWrap": "wrap"}),
    html.Br(),
    
    # Gráficos (xs=12 para mobile, lg=6 para desktop)
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_barras"), xs=12, lg=6),
        dbc.Col(dcc.Graph(id="grafico_pizza"), xs=12, lg=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_linha"), xs=12, lg=6),
        dbc.Col(dcc.Graph(id="grafico_funil"), xs=12, lg=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_consultor"), xs=12, lg=6),
        dbc.Col(dcc.Graph(id="grafico_area"), xs=12, lg=6)
    ]),
    html.Br(),

    html.H4("📋 Tabela Completa", style={"textAlign": "center"}),
    html.Div(id="tabela_dinamica"),
    html.Br(),

    html.Div(id="insights_box", style={"textAlign": "center", "fontSize": "18px", "color": "#f0c929", "padding": "10px"}),
    
    # Controle de Atualização
    dcc.Interval(id="timer_periodico", interval=90000, n_intervals=0, max_intervals=-1), 
    dcc.Interval(id="timer_inicializacao", interval=1, n_intervals=0, max_intervals=1), 

    html.Div([
        dbc.Button("🔄 Recarregar Dados Manualmente", id="btn_recarregar", n_clicks=0, 
                   color="success", className="me-2"),
        html.Span(id='status_recarregamento', style={'marginLeft': '20px', 'color': '#8b949e'})
    ], style={"textAlign": "center", "marginTop": "20px", "marginBottom": "40px"})
])

# ---------------- CALLBACKS (Lógica de Dados Inalterada) ----------------

# 1. Recarrega dados brutos (Input: Botão/Timers; Output: data_store e status)
@app.callback(
    [Output('data_store', 'data'),
     Output('status_recarregamento', 'children')],
    [Input('btn_recarregar', 'n_clicks'),
     Input('timer_periodico', 'n_intervals'),
     Input('timer_inicializacao', 'n_intervals')],
    [State('data_store', 'data')]
)
def recarregar_dados_e_status(n_clicks, n_periodic, n_init, current_data):
    if n_init == 0 and n_clicks == 0:
        raise PreventUpdate

    dados_json_dump = carregar_abas()
    if dados_json_dump is None:
        return current_data, "Erro na Recarga. Verifique o link e o Sheets."
    
    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return dados_json_dump, f"Recarregado: {hora}"


# 2. Popula Opções dos Filtros (Input: data_store; Output: options dos Dropdowns)
@app.callback(
    [Output('filtro_uf', 'options'),
     Output('filtro_status', 'options'),
     Output('filtro_consultor', 'options')],
    [Input('data_store', 'data')]
)
def popular_filtros(dados_json_dump):
    if not dados_json_dump:
        return [[]] * 3
    
    try:
        dados_dict = json.loads(dados_json_dump)
        df = pd.read_json(dados_dict[ABA_PRINCIPAL], orient='split')
    except Exception:
        return [[]] * 3

    def get_options(candidatos):
        col = next((c for c in df.columns if any(p in c for p in candidatos)), None)
        if col:
            unique_values = df[col].dropna().astype(str).unique()
            return [{"label": str(x), "value": str(x)} for x in sorted(unique_values)]
        return []

    op_uf = get_options(COLUNAS_MAP["col_uf"])
    op_status = get_options(COLUNAS_MAP["col_status"])
    op_cons = get_options(COLUNAS_MAP["col_cons"])
    
    return op_uf, op_status, op_cons


# 3. Callback Principal (Filtra, Calcula Métricas e Renderiza)
@app.callback(
    [Output("cards", "children"),
     Output("grafico_barras", "figure"),
     Output("grafico_pizza", "figure"),
     Output("grafico_linha", "figure"),
     Output("grafico_funil", "figure"),
     Output("grafico_consultor", "figure"),
     Output("grafico_area", "figure"),
     Output("tabela_dinamica", "children"),
     Output("insights_box", "children")],
    [Input("data_store", "data"),
     Input("filtro_data_ass", "start_date"), Input("filtro_data_ass", "end_date"),
     Input("filtro_data_dist", "start_date"), Input("filtro_data_dist", "end_date"),
     Input("filtro_uf", "value"),
     Input("filtro_status", "value"),
     Input("filtro_consultor", "value")]
)
def atualizar_dashboard(dados_json_dump, ass_i, ass_f, dist_i, dist_f, uf, status, consultor):
    
    if not dados_json_dump:
        return [html.Div("Aguardando Recarga...")], px.bar(), px.pie(), px.line(), px.funnel(), px.bar(), px.bar(), html.Div(), ""

    try:
        dados_dict = json.loads(dados_json_dump)
        df = pd.read_json(dados_dict[ABA_PRINCIPAL], orient="split")
        df_uf = pd.read_json(dados_dict["Por UF"], orient="split") if "Por UF" in dados_dict else pd.DataFrame()
        df_area = pd.read_json(dados_dict["Por Área"], orient="split") if "Por Área" in dados_dict else pd.DataFrame()

    except Exception as e:
        erro_msg = html.Div(f"Erro ao processar dados. Verifique a Aba Principal: {e}", style={"color": "#f85149"})
        return [html.Div("ERRO")], px.bar(), px.pie(), px.line(), px.funnel(), px.bar(), px.bar(), html.Div(), erro_msg

    # ------------------ DETECÇÃO E FILTRAGEM ------------------
    def detectar(key): return next((c for c in df.columns if any(p in c for p in COLUNAS_MAP[key])), None)
    
    col_uf = detectar("col_uf")
    col_status = detectar("col_status")
    col_cons = detectar("col_cons")
    col_ass = detectar("col_ass")
    col_dist = detectar("col_dist")
    col_mes = detectar("col_mes")
    col_area = detectar("col_area")

    if col_ass: df[col_ass] = pd.to_datetime(df[col_ass], errors="coerce")
    if col_dist: df[col_dist] = pd.to_datetime(df[col_dist], errors="coerce")

    df_filtrado = df.copy()

    # Filtros de Data
    if ass_i and ass_f and col_ass:
        df_filtrado = df_filtrado[(df_filtrado[col_ass].dt.normalize() >= ass_i) & (df_filtrado[col_ass].dt.normalize() <= ass_f)]
    if dist_i and dist_f and col_dist:
        df_filtrado = df_filtrado[(df_filtrado[col_dist].dt.normalize() >= dist_i) & (df_filtrado[col_dist].dt.normalize() <= dist_f)]
    
    # Filtros de Dropdown
    if uf and col_uf:
        df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str).isin(map(str, uf))]
    if status and col_status:
        df_filtrado = df_filtrado[df_filtrado[col_status].astype(str).isin(map(str, status))]
    if consultor and col_cons:
        df_filtrado = df_filtrado[df_filtrado[col_cons].astype(str).isin(map(str, consultor))]

    if df_filtrado.empty:
        vazio = html.Div("Nenhum dado corresponde aos filtros selecionados.", style={"color": "#f85149"})
        return [html.Div("0")], px.bar(), px.pie(), px.line(), px.funnel(), px.bar(), px.bar(), html.Div(), vazio

    # ------------------ CÁLCULOS, CARDS E GRÁFICOS (mantidos) ------------------
    
    total = len(df_filtrado)
    concluidos = df_filtrado[col_status].astype(str).str.contains("conclu", case=False, na=False).sum() if col_status else 0
    pendentes = df_filtrado[col_status].astype(str).str.contains("pend", case=False, na=False).sum() if col_status else 0
    andamento = df_filtrado[col_status].astype(str).str.contains("andament", case=False, na=False).sum() if col_status else 0
    distribuidos = df_filtrado[col_dist].notna().sum() if col_dist else 0
    
    media_dias = 0
    if col_ass and col_dist:
        df_filtrado["dias"] = (df_filtrado[col_dist] - df_filtrado[col_ass]).dt.days
        media_dias = df_filtrado["dias"].mean(skipna=True)

    def card(titulo, valor, cor):
        return html.Div([
            html.H5(titulo, style={"color": cor}),
            html.H3(f"{valor:,.1f}".replace(",", ".").replace(".0", ""), style={"color": "#fff"}) 
        ], style={"background": COR_CARD_BG, "padding": "20px", "margin": "10px", 
                  "borderRadius": "10px", "textAlign": "center", "width": "230px"})

    cards = [
        card("Total", total, "#58a6ff"),
        card("Distribuídos", distribuidos, "#2ea043"),
        card("Concluídos", concluidos, "#f0c929"),
        card("Andamento", andamento, "#d29922"),
        card("Pendentes", pendentes, "#f85149"),
        card("Média Dias", media_dias, "#8b949e"),
    ]

    # Gráficos
    if not df_uf.empty and "uf" in df_uf.columns and "total" in df_uf.columns:
        grafico_barras = px.bar(df_uf, x="uf", y="total", color="total", title="📍 Processos por UF (Aba Por UF)")
    elif col_uf:
        dados_barras = df_filtrado.groupby(col_uf).size().reset_index(name="Total").sort_values("Total", ascending=False)
        grafico_barras = px.bar(dados_barras, x=col_uf, y="Total", color="Total", title="📍 Processos por UF/Município")
    else: grafico_barras = px.bar(title="Sem dados de UF/Município")
    
    grafico_pizza = px.pie(df_filtrado, names=col_status, title="🧩 Distribuição por Status", hole=.3) if col_status else px.pie(title="Sem Status Final")
    
    if col_mes:
        dados_linha = df_filtrado.groupby(col_mes).size().reset_index(name="Total")
        grafico_linha = px.line(dados_linha, x=col_mes, y="Total", markers=True, title="📆 Evolução Mensal")
    else: grafico_linha = px.line(title="Sem Mês Competência")
    
    grafico_funil = px.funnel(pd.DataFrame({
        "Etapa": ["Distribuídos", "Andamento", "Concluídos", "Pendentes"],
        "Qtd": [distribuidos, andamento, concluidos, pendentes]
    }), x="Qtd", y="Etapa", title="🔻 Funil de Processos")
    
    if col_cons:
        dados_cons = df_filtrado.groupby(col_cons).size().reset_index(name="Total").sort_values("Total", ascending=True)
        grafico_consultor = px.bar(dados_cons, x="Total", y=col_cons, orientation="h", title="🏆 Ranking de Consultores")
    else: grafico_consultor = px.bar(title="Sem Consultor/Responsável")
    
    if not df_area.empty and "area" in df_area.columns:
        cor_col = next((c for c in df_area.columns if "eficiencia" in c), None) 
        grafico_area = px.bar(df_area, x="area", y="total_processos", color=cor_col, title="🏢 Desempenho por Área (Aba Por Área)")
    elif col_area:
        dados_area = df_filtrado.groupby(col_area).size().reset_index(name="Total").sort_values("Total", ascending=False)
        grafico_area = px.bar(dados_area, x=col_area, y="Total", title="🏢 Processos por Área")
    else: grafico_area = px.bar(title="Sem Área/Pasta")

    for g in [grafico_barras, grafico_pizza, grafico_linha, grafico_funil, grafico_consultor, grafico_area]:
        g.update_layout(template="plotly_dark", paper_bgcolor=TEMA_DARK, plot_bgcolor=TEMA_DARK)

    # Insights e Tabela
    insight = "📊 Nenhum insight detectado."
    if concluidos > pendentes: insight = "✅ Ótimo! Mais processos concluídos do que pendentes."
    elif media_dias > 30: insight = "⚠️ Média de dias alta. Avaliar gargalos!"
    
    tabela = dash_table.DataTable(
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in df_filtrado.columns],
        data=df_filtrado.to_dict("records"), page_size=10,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": COR_CARD_BG, "color": "#fff"},
        style_data={"backgroundColor": TEMA_DARK, "color": "#fff"},
        filter_action="native", sort_action="native"
    )

    return cards, grafico_barras, grafico_pizza, grafico_linha, grafico_funil, grafico_consultor, grafico_area, html.Div(tabela), insight

# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    print("🚀 Power BI IA Edition v5.2 rodando! (Corrigido)")
    app.run(debug=True)