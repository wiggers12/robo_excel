import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Importa as constantes e funções do arquivo utils.py
from utils import carregar_dados, COR_CARD_BG, TEMA_DARK
from utils import (
    PD_SHEET_NAME, PD_COL_CONSULTOR, PD_COL_DATA, PD_COL_LIGACOES, PD_COL_NOTA_LIGACOES, 
    PD_COL_COTACAO, PD_COL_NOTA_COTACAO, PD_COL_OBSERVACOES,
    PD_STATUS_ATINGIDA, PD_STATUS_NAO_ATINGIDA, PD_STATUS_PARCIAL
)


# ---------------- REGISTRO DA PÁGINA ----------------
register_page(
    __name__,
    name='📊 Produção Diária',
    path='/producao-diaria',
    order=3, # Ordem no menu, ajuste se necessário
    title='Produção Diária'
)

# ---------------- LAYOUT DA PÁGINA ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("📊 Análise de Produção Diária", 
            className="text-center text-info mb-4"),

    # Filtros
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="pd_filtro_consultor", placeholder=f"Filtrar por {PD_COL_CONSULTOR}", multi=True), md=6),
        dbc.Col(dcc.Dropdown(id="pd_filtro_mes", placeholder="Filtrar por Mês"), md=6),
    ], className="mb-4"),

    # KPIs de Desempenho
    html.Div(id="pd_kpis_desempenho", className="mb-4"),

    # Gráfico de Barras por Consultor (Ligações e Cotações)
    dbc.Row([
        dbc.Col(dcc.Graph(id="pd_grafico_barras_consultor", config={"displayModeBar": False}), md=12),
    ], className="mb-4"),
    
    # Gráfico de Linha de Tendência (Ligações e Cotações)
    dbc.Row([
        dbc.Col(dcc.Graph(id="pd_grafico_tendencia", config={"displayModeBar": False}), md=12),
    ], className="mb-4"),

    html.Hr(),
    html.H4("📋 Tabela de Produção Detalhada", className="text-center"),
    html.Div(id="pd_tabela_detalhada", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Recarregar Dados", id="pd_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="pd_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="pd_timer_auto", interval=120000, n_intervals=0)
], fluid=True)


# ---------------- CALLBACK DA PÁGINA ----------------
@dash.callback(
    [
        Output("pd_filtro_consultor", "options"),
        Output("pd_filtro_mes", "options"),
        Output("pd_kpis_desempenho", "children"),
        Output("pd_grafico_barras_consultor", "figure"),
        Output("pd_grafico_tendencia", "figure"),
        Output("pd_tabela_detalhada", "children"),
        Output("pd_status_recarregamento", "children")
    ],
    [
        Input("pd_btn_recarregar", "n_clicks"),
        Input("pd_timer_auto", "n_intervals"),
        Input("pd_filtro_consultor", "value"),
        Input("pd_filtro_mes", "value")
    ]
)
def atualizar_dashboard_producao_diaria(n_clicks, n_timer, filtro_consultor, filtro_mes):
    # 1. Carregar Dados
    df = carregar_dados(PD_SHEET_NAME) 

    # 🚨 Tratamento de Erro Crítico
    if df.empty:
        error_kpis = dbc.Row(dbc.Col(html.Div([html.H4(f"❌ Falha Crítica: Aba '{PD_SHEET_NAME}' não encontrada.", className="text-center text-danger mb-2")]), width=12), className="mb-4")
        return [], [], error_kpis, {}, {}, html.Div(), "❌ Falha ao carregar dados"

    # 2. LIMPEZA E CONVERSÃO
    # Consultor
    if PD_COL_CONSULTOR in df.columns:
        df[PD_COL_CONSULTOR] = df[PD_COL_CONSULTOR].astype(str).str.strip().str.title().replace(["Nan", "Na", ""], "Não Atribuído")
    
    # Data (Converter para datetime e extrair Mês/Ano)
    if PD_COL_DATA in df.columns:
        df[PD_COL_DATA] = pd.to_datetime(df[PD_COL_DATA], errors='coerce')
        df = df.dropna(subset=[PD_COL_DATA]) # Remove linhas com data inválida
        df['MES_ANO'] = df[PD_COL_DATA].dt.strftime('%Y-%m') # Formato AAAA-MM
        df = df.sort_values(by=PD_COL_DATA) # Ordena por data para gráficos de tendência
    else:
        # Se a coluna de data não existir, saia com erro
        error_kpis = dbc.Row(dbc.Col(html.Div([html.H4(f"❌ Falha: Coluna '{PD_COL_DATA}' não encontrada.", className="text-center text-danger mb-2")]), width=12), className="mb-4")
        return [], [], error_kpis, {}, {}, html.Div(), "❌ Falha: Coluna de data não encontrada"

    # Métricas numéricas
    for col in [PD_COL_LIGACOES, PD_COL_COTACAO]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Status (padronizar strings)
    for col in [PD_COL_NOTA_LIGACOES, PD_COL_NOTA_COTACAO]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(["Nan", "Na", ""], "Indefinido")

    # 3. APLICAÇÃO DE FILTROS
    df_filtered = df.copy() 
    if filtro_consultor:
        df_filtered = df_filtered[df_filtered[PD_COL_CONSULTOR].isin(filtro_consultor)]
    if filtro_mes:
        df_filtered = df_filtered[df_filtered['MES_ANO'] == filtro_mes]
        
    df = df_filtered

    # 4. DROPDOWN OPTIONS
    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    consultor_opts = get_options(PD_COL_CONSULTOR)
    mes_opts = get_options('MES_ANO')

    # 5. KPIS DE DESEMPENHO
    total_ligacoes = df[PD_COL_LIGACOES].sum()
    total_cotacoes = df[PD_COL_COTACAO].sum()
    
    # Contagem de status
    meta_lig_atingida = df[df[PD_COL_NOTA_LIGACOES] == PD_STATUS_ATINGIDA].shape[0]
    meta_cot_atingida = df[df[PD_COL_NOTA_COTACAO] == PD_STATUS_ATINGIDA].shape[0]
    
    # Porcentagens de atingimento (considerando que cada linha é um registro diário)
    total_registros = df.shape[0]
    perc_lig_atingida = round((meta_lig_atingida / total_registros) * 100, 2) if total_registros > 0 else 0
    perc_cot_atingida = round((meta_cot_atingida / total_registros) * 100, 2) if total_registros > 0 else 0


    kpis_desempenho = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total de Ligações", className="text-center text-secondary"),
            html.H3(f"{total_ligacoes:,.0f}", className="text-center text-success"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total de Cotações", className="text-center text-secondary"),
            html.H3(f"{total_cotacoes:,.0f}", className="text-center text-info"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Ating. Meta Ligações (Registros)", className="text-center text-secondary"),
            html.H3(f"{perc_lig_atingida:.2f}%", className="text-center text-warning"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Ating. Meta Cotações (Registros)", className="text-center text-secondary"),
            html.H3(f"{perc_cot_atingida:.2f}%", className="text-center text-danger"),
        ]), color=COR_CARD_BG, inverse=True), md=3),
    ], className="mb-4")


    # 6. GRÁFICO DE BARRAS POR CONSULTOR (Ligações e Cotações)
    df_agrupado_consultor = df.groupby(PD_COL_CONSULTOR).agg(
        Total_Ligacoes=(PD_COL_LIGACOES, 'sum'),
        Total_Cotacoes=(PD_COL_COTACAO, 'sum')
    ).reset_index()
    
    # Melt para Plotly
    df_plot_consultor = df_agrupado_consultor.melt(id_vars=PD_COL_CONSULTOR, 
                                                value_vars=['Total_Ligacoes', 'Total_Cotacoes'], 
                                                var_name='Métrica', 
                                                value_name='Total')

    graf_barras_consultor = px.bar(
        df_plot_consultor,
        x=PD_COL_CONSULTOR,
        y='Total',
        color='Métrica',
        barmode='group',
        title='Ligações e Cotações por Consultor',
        template="plotly_dark",
        labels={'Total': 'Total Registrado', PD_COL_CONSULTOR: 'Consultor'},
        color_discrete_map={'Total_Ligacoes': '#636EFA', 'Total_Cotacoes': '#EF553B'} # Cores personalizadas
    )
    graf_barras_consultor.update_layout(margin=dict(t=80, b=20), yaxis={'tickformat': ',.0f'})


    # 7. GRÁFICO DE TENDÊNCIA (Linha - Ligações e Cotações ao longo do tempo)
    df_tendencia = df.groupby(PD_COL_DATA).agg(
        Total_Ligacoes=(PD_COL_LIGACOES, 'sum'),
        Total_Cotacoes=(PD_COL_COTACAO, 'sum')
    ).reset_index()

    # Melt para Plotly
    df_plot_tendencia = df_tendencia.melt(id_vars=PD_COL_DATA, 
                                          value_vars=['Total_Ligacoes', 'Total_Cotacoes'], 
                                          var_name='Métrica', 
                                          value_name='Total')

    graf_tendencia = px.line(
        df_plot_tendencia,
        x=PD_COL_DATA,
        y='Total',
        color='Métrica',
        title='Tendência Diária: Ligações e Cotações',
        template="plotly_dark",
        markers=True,
        labels={'Total': 'Total Registrado', PD_COL_DATA: 'Data'}
    )
    graf_tendencia.update_layout(margin=dict(t=80, b=20), yaxis={'tickformat': ',.0f'})

    # 8. TABELA DETALHADA
    cols_tabela = [PD_COL_DATA, PD_COL_CONSULTOR, PD_COL_LIGACOES, PD_COL_NOTA_LIGACOES, PD_COL_COTACAO, PD_COL_NOTA_COTACAO, PD_COL_OBSERVACOES]
    tabela_df = df[[col for col in cols_tabela if col in df.columns]]
    
    tabela = html.Div()
    if not tabela_df.empty:
        tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True, class_name="table-dark")

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (consultor_opts, mes_opts, kpis_desempenho, graf_barras_consultor, graf_tendencia, tabela, f"🕒 Atualizado às {hora}")