# /pages/crm_tempo_real.py

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json

# Registra a página
dash.register_page(
    __name__,
    path='/crm_tempo_real',  # Rota que o botão usará
    name='CRM - Tempo Real',
    order=3,
)
# ---------------- CONFIGURAÇÕES LOCAIS (Para reuso) ----------------
TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"

# ---------------- LAYOUT DA PÁGINA ----------------

def layout():
    return html.Div([
        html.Br(),
        html.H2("⏱️ CRM - Tempo Real", className="text-info"),
        html.Hr(style={"borderColor": COR_CARD_BG}),
        
        dbc.Row([
            dbc.Col(dbc.Alert("Dashboard de acompanhamento de Consultores e Performance.", color="info"), md=12),
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(id='crm_grafico_1', figure={}), xs=12, lg=6),
            dbc.Col(dcc.Graph(id='crm_grafico_2', figure={}), xs=12, lg=6),
        ]),
        
        html.H4("Tabela de Consultores", style={"textAlign": "center"}),
        html.Div(id='crm_tabela')
    ])

# ---------------- CALLBACKS DEDICADOS À PÁGINA ----------------

@dash.callback(
    [Output('crm_grafico_1', 'figure'),
     Output('crm_grafico_2', 'figure'),
     Output('crm_tabela', 'children')],
    [Input("data_store", "data"),
     Input("filtro_data_ass", "start_date"), Input("filtro_data_ass", "end_date"),
     Input("filtro_data_dist", "start_date"), Input("filtro_data_dist", "end_date"),
     Input("filtro_uf", "value"),
     Input("filtro_status", "value"),
     Input("filtro_consultor", "value")]
)
def update_crm_page(dados_json_dump, ass_i, ass_f, dist_i, dist_f, uf, status, consultor):
    if not dados_json_dump:
        raise PreventUpdate

    # 1. Carregamento e Filtragem (COPIAR A LÓGICA DO APP.PY AQUI!)
    try:
        dados_dict = json.loads(dados_json_dump)
        df = pd.read_json(dados_dict["Dados Originais"], orient="split")
        # Aplicar filtros (DATA, UF, STATUS, etc. - COPIAR A LÓGICA DE FILTRAGEM AQUI)
        df_filtrado = df # AQUI FICARIA O DF FILTRADO
    except:
        fig_vazia = px.bar(title="Aguardando Dados")
        return fig_vazia, fig_vazia, html.Div("Aguardando dados...")

    # 2. Geração de Conteúdo Específico
    
    # Exemplo: Ranking de Consultores
    col_cons = next((c for c in df_filtrado.columns if "consultor" in c), 'coluna_falsa')
    
    fig1 = px.bar(df_filtrado.groupby(col_cons).size().reset_index(name="Processos"), 
                  x="Processos", y=col_cons, orientation='h', title='Ranking de Processos por Consultor')
    
    # Exemplo 2: Eficiência
    fig2 = px.pie(df_filtrado, names='col_status', title='Status Atual dos Processos')
    
    for fig in [fig1, fig2]:
        fig.update_layout(template="plotly_dark", paper_bgcolor=TEMA_DARK, plot_bgcolor=TEMA_DARK)
        
    tabela = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df_filtrado.columns[:5]],
        data=df_filtrado.to_dict("records"), page_size=10,
    )

    return fig1, fig2, html.Div(tabela)