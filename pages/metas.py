import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from utils import carregar_dados, COR_CARD_BG, TEMA_DARK

# ---------------- NOMES COLUNAS NORMALIZADOS ----------------
MP_COL_MES = "mes"
MP_COL_META_MENSAL = "meta_mensal_pasta"
MP_COL_META_MINIMA = "meta_mensal_area_minimo_esperado"
MP_COL_META_ATINGIDA = "meta_mensal_atingida"
MP_COL_PERCENTUAL_ATINGIMENTO = "_atingimento_contratos"
MP_COL_LEADS_RECEBIDOS = "leads_recebidos_por_area_mes"
MP_COL_TAXA_CONVERSAO = "taxa_de_conversao_por_area_mes"
MP_COL_POTENCIAL_50 = "potencial_a_atingirse_cumprido_a_meta_mensal_individual_em_+_50"
MP_COL_POTENCIAL_100 = "potencial_a_atingirse_cumprido_a_meta_mensal_individual_em_100"
PASTA_COL_INDEX = 1  # Segunda coluna da planilha

# ---------------- REGISTRO DA PÁGINA ----------------
register_page(
    __name__,
    name='🏆 Metas por Pasta',
    path='/metas',
    order=3,
    title='Metas por Pasta'
)

# ---------------- LAYOUT ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("🏆 Dashboard - Metas por Pasta e Desempenho", className="text-center text-success mb-4"),

    html.Div(id="mp-kpis"),
    html.Br(),
    html.H5("🎛️ Filtros Interativos"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id="mp_filtro_mes", placeholder="Filtrar por Mês"), md=6),
        dbc.Col(dcc.Dropdown(id="mp_filtro_pasta", placeholder="Filtrar por Área/Pasta"), md=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="mp_grafico_atingimento", config={"displayModeBar": False}), lg=6, md=12),
        dbc.Col(dcc.Graph(id="mp_grafico_conversao", config={"displayModeBar": False}), lg=6, md=12),
    ]),

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

# ---------------- CALLBACK ----------------
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
    df = carregar_dados("Metas por pasta")

    if df.empty:
        error_kpis = dbc.Row(
            dbc.Col(html.Div([
                html.H4("❌ Falha Crítica ao Carregar Dados de Metas", className="text-center text-danger mb-2")
            ]), width=12), className="mb-4"
        )
        empty_opts, empty_fig = [], {}
        return empty_opts, empty_opts, error_kpis, empty_fig, empty_fig, empty_fig, html.Div(), "❌ Falha ao carregar dados"

    PASTA_COL = df.columns[PASTA_COL_INDEX]

    for col in [MP_COL_MES, PASTA_COL]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["Nan", "Na", ""], "")

    for col in [MP_COL_PERCENTUAL_ATINGIMENTO, MP_COL_TAXA_CONVERSAO]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in [MP_COL_META_MENSAL, MP_COL_META_ATINGIDA, MP_COL_LEADS_RECEBIDOS, MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if filtro_mes:
        df = df[df[MP_COL_MES] == filtro_mes]
    if filtro_pasta:
        df = df[df[PASTA_COL] == filtro_pasta]

    def get_options(column):
        if column in df.columns:
            valid_values = df[df[column] != ""][column].unique()
            return [{"label": v, "value": v} for v in sorted(valid_values)]
        return []

    mes_opts = get_options(MP_COL_MES)
    pasta_opts = get_options(PASTA_COL)

    total_metas_atingidas = df[MP_COL_META_ATINGIDA].sum()
    total_metas_esperadas = df[MP_COL_META_MENSAL].sum()
    taxa_conversao_media = df[MP_COL_TAXA_CONVERSAO].mean() * 100
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

    graf_atingimento, graf_conversao, graf_potencial = {}, {}, {}

    if not df.empty:
        df_atingimento = df.groupby(PASTA_COL).sum(numeric_only=True).reset_index()
        df_atingimento['Diferenca'] = df_atingimento[MP_COL_META_MENSAL] - df_atingimento[MP_COL_META_ATINGIDA]
        df_stack = pd.DataFrame({
            PASTA_COL: df_atingimento[PASTA_COL],
            'Atingida': df_atingimento[MP_COL_META_ATINGIDA],
            'Falta Atingir': df_atingimento['Diferenca'].clip(lower=0)
        })
        df_stack_melted = df_stack.melt(id_vars=PASTA_COL, var_name="Status", value_name="Quantidade")
        graf_atingimento = px.bar(
            df_stack_melted, x="Quantidade", y=PASTA_COL, color="Status",
            title="Atingimento de Metas por Área/Pasta",
            labels={"Quantidade": "Total de Metas", PASTA_COL: "Área/Pasta"},
            template="plotly_dark", orientation='h'
        )

    if not df.empty and MP_COL_TAXA_CONVERSAO in df.columns:
        df_conversao = df.groupby(MP_COL_MES).mean(numeric_only=True).reset_index()
        graf_conversao = px.line(
            df_conversao, x=MP_COL_MES, y=MP_COL_TAXA_CONVERSAO,
            title="Taxa de Conversão Média por Mês",
            labels={MP_COL_MES: "Mês", MP_COL_TAXA_CONVERSAO: "Taxa de Conversão"},
            template="plotly_dark", markers=True
        )
        graf_conversao.update_layout(yaxis={'tickformat': '.2f'})

    if not df.empty and MP_COL_POTENCIAL_50 in df.columns:
        df_potencial = df.groupby(PASTA_COL).sum(numeric_only=True).reset_index()
        df_melt = df_potencial.melt(
            id_vars=PASTA_COL,
            value_vars=[MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100],
            var_name="Cenario", value_name="Potencial de Metas"
        )
        graf_potencial = px.bar(
            df_melt, x=PASTA_COL, y="Potencial de Metas", color="Cenario",
            title="Potencial de Metas Atingíveis por Área",
            template="plotly_dark", barmode='group'
        )

    tabela_df = df.copy()
    cols_to_display = [col for col in tabela_df.columns if col not in [MP_COL_POTENCIAL_50, MP_COL_POTENCIAL_100, MP_COL_META_MINIMA]]
    tabela_df = tabela_df[cols_to_display].head(30)
    tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True) if not tabela_df.empty else html.Div()

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return mes_opts, pasta_opts, kpis, graf_atingimento, graf_conversao, graf_potencial, tabela, f"🕒 Atualizado às {hora}"
