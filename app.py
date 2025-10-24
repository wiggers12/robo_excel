# =======================================================
# 📊 ROBÔ POWER BI IA EDITION (V7.2 - CORREÇÃO DE IMPORTAÇÃO)
# Correção: Adicionado 'import dash' para resolver o NameError.
# Autor: Dionatan Wiggers
# =======================================================

import pandas as pd
import unidecode
import json 
import dash # <--- ADICIONADO AQUI
from dash import Dash, dcc, html, Input, Output, dash_table, State
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# ---------------- CONFIGURAÇÕES GLOBAIS ----------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1SEeX-g_Wdl0XpdXt90nDgDBPrjbS3zh_8yvAVpoxpPs/export?format=xlsx"
TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"
ABA_PRINCIPAL = "controle de processos"

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

# ---------------- DASH APP INICIALIZAÇÃO (Padrão Pages) ----------------
# use_pages=True é fundamental
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], use_pages=True)
server = app.server 
app.title = "Power BI IA Edition 7.1 (Multi-Page Fix)"

MAX_WIDTH_STYLE = {
    'maxWidth': '1400px', 
    'margin': 'auto',     
    'padding': '0 15px'   
}

# ---------------- LAYOUT RAIZ (ROOT LAYOUT) ----------------

app.layout = dbc.Container(
    style=MAX_WIDTH_STYLE,
    children=[
        html.Br(),
        
        # --- BARRA DE NAVEGAÇÃO E TÍTULO ---
        dbc.Row([
            dbc.Col(html.H2("📊 Dashboard Principal", style={"color": "#fff", "fontSize": "24px"}),
                    xs=12, md=6, className="mb-3 mb-md-0"),
            
            # --- ATENÇÃO: BOTÕES PERSONALIZADOS AQUI ---
            dbc.Col(dbc.Stack(direction="horizontal", gap=3, children=[
                
                # Botão para Funil de Precatórios
                # O 'href' deve coincidir com o 'path' que será registrado na página
                dbc.Button("Funil de Precatórios", color="primary", href="/funil_precatorio", className="me-2"),
                
                # Botão para Metas por Pasta
                # O 'href' deve coincidir com o 'path' que será registrado na página
                dbc.Button("Metas por Pasta", color="info", href="/metas_por_pasta", className="me-2"),
                
                # *Opcional: Mantenha o botão de Home/Principal caso precise de um link para o app.py*
                dbc.Button("Início/Visão Geral", color="secondary", href="/", className="me-2"),
                
            ]), xs=12, md=6, className="d-flex justify-content-md-end justify-content-start"),
        ], className="align-items-center mb-4"),
        
        # ... (Componentes Globais: dcc.Store, dcc.Interval)
        
        html.Hr(style={"borderColor": COR_CARD_BG}),
        
        # O dash.page_container renderiza a página ativa
        # Se a rota for '/', ele renderiza a página que tiver path='/' (geralmente app.py)
        html.Div(dash.page_container, id='page-wrapper'),
        
        # ... (ÁREA DE STATUS E RECARGA)
    ]
)
        
        # --- ÁREA DE STATUS E RECARGA ---
        html.Div([
            dbc.Button("🔄 Recarregar Dados Manualmente", id="btn_recarregar", n_clicks=0, 
                       color="success", className="me-2"),
            html.Span(id='status_recarregamento', style={'marginLeft': '20px', 'color': '#8b949e'})
        ], style={"textAlign": "center", "marginTop": "20px", "marginBottom": "40px"}),
        
    ]
)

# ---------------- CALLBACKS GLOBAIS DE DADOS ----------------

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


# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    # CORREÇÃO: Usamos app.run em vez de app.run_server
    app.run(debug=True)


