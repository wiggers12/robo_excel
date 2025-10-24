# /pages/funil_precatorio.py

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
import json
import numpy as np

# =======================================================
# 📊 PÁGINA: FUNIL DE PRECATÓRIOS (V8.2 - FILTROS LOCAIS E INDEPENDENTES)
# Funcionalidade: Possui seus próprios Dropdowns de filtro.
# =======================================================

# ---------------- CONFIGURAÇÕES LOCAIS ----------------
TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"
ABA_DEDICADA = "Funil de precatorio" 
ABA_PRINCIPAL = "Funil de precatorio" 

COLUNAS_MAP = {
    "col_uf": ["uf"],
    "col_status": ["status"],
    "col_cons": ["consultor"],
    "col_valor": ["valor", "valor_total", "total"],
    "col_ass": ["assinatura", "data_assinatura"],
    "col_dist": ["data_da_distribuicao"],
    "col_motivo": ["motivo"], 
    "col_mes": ["mes"], 
    "col_origem": ["origem", "campaign_name", "platform", "source"] 
}

# ---------------- REGISTRO DA PÁGINA ----------------
dash.register_page(
    __name__,
    path='/funil_precatorio',
    name='Funil de Precatórios',
    order=2, 
)

# ---------------- LAYOUT DA PÁGINA (COM FILTROS PRÓPRIOS) ----------------

def layout():
    return html.Div([
        html.Br(),
        html.H2("💰 Funil de Precatórios (Análise Isolada)", className="text-primary"),
        html.Hr(style={"borderColor": COR_CARD_BG}),
        
        # --- FILTROS LOCAIS ---
        dbc.Card(dbc.CardBody(
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='prec_filtro_uf', placeholder="UF/Município (Local)", multi=True), xs=12, md=4, lg=2),
                dbc.Col(dcc.Dropdown(id='prec_filtro_status', placeholder="Status Final (Local)", multi=True), xs=12, md=4, lg=3),
                dbc.Col(dcc.Dropdown(id='prec_filtro_cons', placeholder="Consultor (Local)", multi=True), xs=12, md=4, lg=3),
                dbc.Col(dcc.Dropdown(id='prec_filtro_motivo', placeholder="Motivo (Local)", multi=True), xs=12, md=4, lg=3),
            ], className="g-3 justify-content-start")
        ), style={"marginBottom": "20px"}),
       
 # --- FIM DOS FILTROS LOCAIS ---

        # Cards de KPI
        html.Div(id='precatorios_cards', style={"display": "flex", "justifyContent": "space-around", "flexWrap": "wrap"}),

        dbc.Row([
            dbc.Col(dcc.Graph(id='precatorios_eficiencia_cons', figure={}), xs=12, lg=6), 
            dbc.Col(dcc.Graph(id='precatorios_top_motivos', figure={}), xs=12, lg=6), 
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(id='precatorios_leads_mes', figure={}), xs=12, lg=6), 
            dbc.Col(dcc.Graph(id='precatorios_conversao_origem', figure={}), xs=12, lg=6), 
        ]),
        
        html.H4("Detalhe Operacional", style={"textAlign": "center"}),
        html.Div(id='precatorios_tabela')
    ])

# ---------------- CALLBACKS DE CONTROLE LOCAL ----------------

# 1. Popula Filtros Locais (Dispara apenas quando o data_store carrega)
@dash.callback(
    [Output('prec_filtro_uf', 'options'),
     Output('prec_filtro_status', 'options'),
     Output('prec_filtro_cons', 'options'),
     Output('prec_filtro_motivo', 'options')],
    [Input('data_store', 'data')] 
)
def popular_filtros_locais(dados_json_dump):
    if not dados_json_dump:
        raise PreventUpdate

    df = None
    try:
        dados_dict = json.loads(dados_json_dump)
        if ABA_DEDICADA in dados_dict:
            df = pd.read_json(dados_dict[ABA_DEDICADA], orient="split")
        if df is None or df.empty:
            df = pd.read_json(dados_dict[ABA_PRINCIPAL], orient="split")
    except Exception:
        return [[]] * 4

    def detectar(key): return next((c for c in df.columns if any(p in c for p in COLUNAS_MAP[key])), None)
    
    col_uf = detectar("col_uf")
    col_status = detectar("col_status")
    col_cons = detectar("col_cons")
    col_motivo = detectar("col_motivo")

    def get_options(col):
        if col:
            unique_values = df[col].dropna().astype(str).unique()
            return [{"label": str(x), "value": str(x)} for x in sorted(unique_values)]
        return []

    return get_options(col_uf), get_options(col_status), get_options(col_cons), get_options(col_motivo)


# 2. Callback Principal (Renderiza o conteúdo com base nos filtros LOCAIS)
@dash.callback(
    [Output('precatorios_cards', 'children'),
     Output('precatorios_eficiencia_cons', 'figure'),
     Output('precatorios_top_motivos', 'figure'),
     Output('precatorios_leads_mes', 'figure'),
     Output('precatorios_conversao_origem', 'figure'),
     Output('precatorios_tabela', 'children')],
    [Input("data_store", "data"), 
     Input('prec_filtro_uf', 'value'), 
     Input('prec_filtro_status', 'value'),
     Input('prec_filtro_cons', 'value'),
     Input('prec_filtro_motivo', 'value')] 
)
def update_precatorios_page(dados_json_dump, filtro_uf, filtro_status, filtro_cons, filtro_motivo):
    if not dados_json_dump:
        raise PreventUpdate

    df = None
    try:
        dados_dict = json.loads(dados_json_dump)
        if ABA_DEDICADA in dados_dict:
            df = pd.read_json(dados_dict[ABA_DEDICADA], orient="split")
        if df is None or df.empty:
            df = pd.read_json(dados_dict[ABA_PRINCIPAL], orient="split")
    except Exception as e:
        msg = f"Erro ao carregar dados: {e}"
        fig_vazia = px.bar(title=msg)
        return [html.Div("ERRO")], fig_vazia, fig_vazia, fig_vazia, fig_vazia, html.Div(msg)
    
    
    df_filtrado = df.copy() 
    
    # ------------------ DETECÇÃO E APLICAÇÃO DE FILTROS LOCAIS ------------------
    def detectar(key): return next((c for c in df.columns if any(p in c for p in COLUNAS_MAP[key])), None)
    
    col_status = detectar("col_status")
    col_cons = detectar("col_cons")
    col_uf = detectar("col_uf")
    col_motivo = detectar("col_motivo")
    
    # Aplicação dos Filtros Locais
    if filtro_uf and col_uf:
        df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str).isin(map(str, filtro_uf))]
    if filtro_status and col_status:
        df_filtrado = df_filtrado[df_filtrado[col_status].astype(str).isin(map(str, filtro_status))]
    if filtro_cons and col_cons:
        df_filtrado = df_filtrado[df_filtrado[col_cons].astype(str).isin(map(str, filtro_cons))]
    if filtro_motivo and col_motivo:
        df_filtrado = df_filtrado[df_filtrado[col_motivo].astype(str).isin(map(str, filtro_motivo))]

    if df_filtrado.empty or col_status is None:
         fig_vazia = px.bar(title="Sem dados filtrados")
         return [html.Div("0")], fig_vazia, fig_vazia, fig_vazia, fig_vazia, html.Div("...")

    # ------------------ CÁLCULOS E RENDERIZAÇÃO (Mantidos) ------------------

    # Colunas restantes
    col_mes = detectar("col_mes")
    col_valor = detectar("col_valor")
    col_origem = detectar("col_origem")

    # --- DEFINIÇÃO DE STATUS PARA CÁLCULO ---
    df_filtrado['is_encerrado'] = df_filtrado[col_status].astype(str).str.contains('encerrado|concluído|deferido|fechado', case=False, na=False)
    df_filtrado['is_convertido'] = df_filtrado[col_status].astype(str).str.contains('convertido|fechado|venda|sucesso', case=False, na=False)
    df_filtrado['is_perdido'] = df_filtrado[col_status].astype(str).str.contains('perdido|sem_viabilidade|sem_interesse|cancelado', case=False, na=False)
    
    
    # ------------------ KPIS (CARDS) ------------------
    total_leads = len(df_filtrado)
    leads_encerrados = df_filtrado['is_encerrado'].sum()
    leads_ativos = total_leads - leads_encerrados
    leads_convertidos = df_filtrado['is_convertido'].sum()
    leads_perdidos = df_filtrado['is_perdido'].sum()
    taxa_conversao = (leads_convertidos / total_leads) if total_leads > 0 else 0
    
    def card(titulo, valor, cor):
        valor_str = f"{int(valor):,}".replace(",", ".")
        if 'Taxa' in titulo: valor_str = f"{valor*100:.2f}%"
        
        return html.Div([
            html.H5(titulo, style={"color": cor}),
            html.H3(valor_str, style={"color": "#fff"}) 
        ], style={"background": COR_CARD_BG, "padding": "20px", "margin": "10px", 
                  "borderRadius": "10px", "textAlign": "center", "width": "180px"})

    cards = [
        card("Total de leads", total_leads, "#58a6ff"),
        card("Leads ativos", leads_ativos, "#d29922"),
        card("Leads encerrados", leads_encerrados, "#8b949e"),
        card("Leads convertidos", leads_convertidos, "#2ea043"),
        card("Leads perdidos", leads_perdidos, "#f85149"),
        card("Taxa de conversão", taxa_conversao, "#f0c929"),
    ]

    # ------------------ GRÁFICOS ------------------
    
    # 1. Eficiência por Consultor
    fig_eficiencia_cons = px.bar(title="Sem Consultor")
    if col_cons:
        df_eficiencia = df_filtrado.groupby(col_cons).agg(
            Total=('is_convertido', 'count'), Convertidos=('is_convertido', 'sum')
        ).reset_index()
        df_eficiencia['Taxa de Sucesso (%)'] = (df_eficiencia['Convertidos'] / df_eficiencia['Total']) * 100
        df_eficiencia = df_eficiencia.sort_values('Taxa de Sucesso (%)', ascending=True)

        fig_eficiencia_cons = px.bar(
            df_eficiencia, x='Taxa de Sucesso (%)', y=col_cons, orientation='h',
            title='Eficiência: Taxa de Sucesso por Consultor',
            color='Taxa de Sucesso (%)', color_continuous_scale=px.colors.sequential.Plotly3
        )
        fig_eficiencia_cons.update_traces(hovertemplate=f"Consultor: %{{y}}<br>Taxa: %{{x:.2f}}%<extra></extra>")

    # 2. Top Motivos
    fig_motivos = px.bar(title="Sem Motivos")
    if col_motivo and col_status:
        df_motivos = df_filtrado.groupby([col_motivo, col_status]).size().reset_index(name='Contagem')
        top_motivos_list = df_motivos.groupby(col_motivo)['Contagem'].sum().nlargest(5).index
        df_motivos_top = df_motivos[df_motivos[col_motivo].isin(top_motivos_list)]
        
        fig_motivos = go.Figure()
        status_cores = {'ENCERRADO': '#2ea043', 'PENDENTE': '#d29922'} 
        df_motivos_top['STATUS_CAT'] = df_motivos_top[col_status].astype(str).str.upper().apply(
            lambda x: 'ENCERRADO' if 'ENCERRADO' in x or 'CONVERTIDO' in x else 'PENDENTE'
        )
        
        for status_val in ['PENDENTE', 'ENCERRADO']:
            df_slice = df_motivos_top[df_motivos_top['STATUS_CAT'] == status_val]
            
            fig_motivos.add_trace(go.Bar(y=df_slice[col_motivo], x=df_slice['Contagem'], name=status_val, orientation='h', marker_color=status_cores.get(status_val, 'gray')))

        fig_motivos.update_layout(barmode='stack', title='Top 5 Motivos por Status', xaxis={'title': 'Contagem', 'tickformat': ',.0f'})

    # 3. Leads por Mês (Tendência)
    fig_tendencia = px.bar(title="Sem Tendência Mensal")
    if col_mes and col_status:
        df_filtrado[col_mes] = df_filtrado[col_mes].astype(str).str.title()
        df_filtrado['Status_Categoria'] = df_filtrado[col_status].apply(lambda x: 'Encerrados/Convertidos' if 'encerrado' in str(x).lower() or 'convertido' in str(x).lower() else 'Leads Ativos')
        df_tendencia = df_filtrado.groupby([col_mes, 'Status_Categoria']).size().reset_index(name='Contagem')

        ordem_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        df_tendencia[col_mes] = pd.Categorical(df_tendencia[col_mes], categories=ordem_meses, ordered=True)
        df_tendencia = df_tendencia.sort_values(col_mes)

        fig_tendencia = px.bar(df_tendencia, x=col_mes, y='Contagem', color='Status_Categoria', barmode='group', title='Leads por Status e Mês', labels={'Contagem': 'Qtd. Leads', col_mes: 'Mês'})

    # 4. Conversão por Origem
    fig_origem = px.bar(title="Sem Origem")
    if col_origem:
        df_origem = df_filtrado.groupby(col_origem).agg(Total=('is_convertido', 'count'), Convertidos=('is_convertido', 'sum')).reset_index()
        df_origem['Taxa Conversão (%)'] = (df_origem['Convertidos'] / df_origem['Total']) * 100
        df_origem = df_origem.sort_values('Taxa Conversão (%)', ascending=False)
        
        fig_origem = px.bar(df_origem.head(10), x=col_origem, y='Taxa Conversão (%)', title='Taxa de Conversão por Origem do Lead (Top 10)', color='Taxa Conversão (%)', color_continuous_scale=px.colors.sequential.Oranges)

    # Tabela
    cols_tabela = [c for c in df_filtrado.columns if any(k in c for k in ["nome", "consultor", "status", "distribuicao", "motivo", "mês", "telefone", "origem"])]
    tabela = dash_table.DataTable(
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in cols_tabela],
        data=df_filtrado.to_dict("records"), page_size=10,
        style_table={"overflowX": "auto"}, style_header={"backgroundColor": COR_CARD_BG, "color": "#fff"},
        style_data={"backgroundColor": TEMA_DARK, "color": "#fff"}, filter_action="native", sort_action="native"
    )
    
    # Estilização final
    for fig in [fig_eficiencia_cons, fig_motivos, fig_tendencia, fig_origem]:
        fig.update_layout(template="plotly_dark", paper_bgcolor=TEMA_DARK, plot_bgcolor=TEMA_DARK)


    return cards, fig_eficiencia_cons, fig_motivos, fig_tendencia, fig_origem, html.Div(tabela)