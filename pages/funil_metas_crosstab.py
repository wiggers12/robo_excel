# =======================================================
# 🎯 FUNIL X METAS (CRUZADO) - DASHBOARD OFICIAL
# =======================================================

import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Importa funções e constantes globais
# Substitua no início do arquivo, na importação:
from utils import (
    carregar_dados, COR_CARD_BG, TEMA_DARK,
    FM_COL_MES, FM_COL_AREA_PASTA_PROXY as FM_COL_AREA,
    FM_COL_META_MENSAL, FM_COL_META_ATINGIDA,
    FM_COL_TAXA_CONVERSAO_META, FM_COL_TAXA_CONVERSAO_REAL,
    FM_COL_LEADS_RECEBIDOS as FM_COL_TOTAL_LEADS,
    FM_COL_CONTRATOS_REAL as FM_COL_CONTRATOS_FECHADOS
)

# ---------------- CONFIGURAÇÕES ----------------
SHEET_NAME_CRUZADO = "funilxmetas"

register_page(
    __name__,
    name='🎯 Funil X Metas (Cruzado)',
    path='/cruzamento-metas-funil',
    order=4,
    title='Metas X Funil'
)

# ---------------- LAYOUT ----------------
layout = dbc.Container([
    html.Br(),
    html.H2("🎯 Cruzamento: Metas de Conversão vs. Funil Real",
            className="text-center text-danger mb-4"),

    html.Div(id="mf_kpis"),
    html.Br(),

    html.H5("🎛️ Filtros Interativos"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="mf_filtro_mes", placeholder="Filtrar por Mês"), md=6),
        dbc.Col(dcc.Dropdown(id="mf_filtro_pasta", placeholder="Filtrar por Área/Pasta"), md=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="mf_grafico_taxa_conversao", config={"displayModeBar": False}), md=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="mf_grafico_contratos", config={"displayModeBar": False}), md=12),
    ]),

    html.Hr(),
    html.H4("📋 Tabela de Dados Cruzados", className="text-center"),
    html.Div(id="mf_tabela_cruzamento", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="mf_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="mf_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="mf_timer_auto", interval=90000, n_intervals=0)
], fluid=True)

# ---------------- CALLBACK ----------------
@dash.callback(
    [
        Output("mf_filtro_mes", "options"),
        Output("mf_filtro_pasta", "options"),
        Output("mf_kpis", "children"),
        Output("mf_grafico_taxa_conversao", "figure"),
        Output("mf_grafico_contratos", "figure"),
        Output("mf_tabela_cruzamento", "children"),
        Output("mf_status_recarregamento", "children")
    ],
    [
        Input("mf_btn_recarregar", "n_clicks"),
        Input("mf_timer_auto", "n_intervals"),
        Input("mf_filtro_mes", "value"),
        Input("mf_filtro_pasta", "value")
    ]
)
def atualizar_dashboard_cruzamento(n_clicks, n_timer, filtro_mes, filtro_pasta):
    # 1️⃣ Carrega os dados
    df = carregar_dados(SHEET_NAME_CRUZADO)

    # 2️⃣ Validação de dados
    if df.empty:
        error_kpis = dbc.Row(
            dbc.Col(html.Div([
                html.H4(f"❌ Falha ao carregar a aba '{SHEET_NAME_CRUZADO}'", className="text-center text-danger mb-2")
            ]), width=12), className="mb-4"
        )
        return [], [], error_kpis, {}, {}, html.Div(), "❌ Erro ao carregar dados."

    # 3️⃣ Normalização
    for col in [FM_COL_MES, FM_COL_AREA]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title().replace(["Nan", "Na", ""], "")

    for col in [FM_COL_META_MENSAL, FM_COL_META_ATINGIDA, FM_COL_TOTAL_LEADS,
                FM_COL_CONTRATOS_FECHADOS, FM_COL_TAXA_CONVERSAO_META, FM_COL_TAXA_CONVERSAO_REAL]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 4️⃣ Aplicar filtros
    if filtro_mes:
        df = df[df[FM_COL_MES] == filtro_mes]
    if filtro_pasta:
        df = df[df[FM_COL_AREA] == filtro_pasta]

    # 5️⃣ Filtros dinâmicos
    def get_options(column):
        if column in df.columns:
            values = [v for v in df[column].unique() if v != ""]
            return [{"label": v, "value": v} for v in sorted(values)]
        return []

    mes_opts = get_options(FM_COL_MES)
    pasta_opts = get_options(FM_COL_AREA)

    # 6️⃣ KPIs principais
    total_contratos_real = df[FM_COL_CONTRATOS_FECHADOS].sum()
    total_meta_contratos = df[FM_COL_META_ATINGIDA].sum()
    taxa_conversao_real_media = df[FM_COL_TAXA_CONVERSAO_REAL].mean()
    atingimento_total = round((total_contratos_real / total_meta_contratos) * 100, 2) if total_meta_contratos > 0 else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Contratos Fechados (Real)", className="text-center text-secondary"),
            html.H3(f"{total_contratos_real:,.0f}", className="text-center text-success"),
        ]), color=COR_CARD_BG), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Meta de Contratos (Alvo)", className="text-center text-secondary"),
            html.H3(f"{total_meta_contratos:,.0f}", className="text-center text-warning"),
        ]), color=COR_CARD_BG), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Taxa de Conversão Média (Real)", className="text-center text-secondary"),
            html.H3(f"{taxa_conversao_real_media*100:.2f}%", className="text-center text-info"),
        ]), color=COR_CARD_BG), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Atingimento Global", className="text-center text-secondary"),
            html.H3(f"{atingimento_total:.2f}%", className="text-center text-primary"),
        ]), color=COR_CARD_BG), md=3),
    ], className="mb-4")

    # 7️⃣ Gráfico de Taxa de Conversão
    df_taxa = df.groupby([FM_COL_AREA, FM_COL_MES]).mean(numeric_only=True).reset_index()
    df_plot_taxa = df_taxa.melt(
        id_vars=[FM_COL_AREA, FM_COL_MES],
        value_vars=[FM_COL_TAXA_CONVERSAO_REAL, FM_COL_TAXA_CONVERSAO_META],
        var_name="Tipo de Taxa",
        value_name="Taxa de Conversão"
    )
    df_plot_taxa["Tipo de Taxa"] = df_plot_taxa["Tipo de Taxa"].replace({
        FM_COL_TAXA_CONVERSAO_REAL: "Taxa Real (Funil)",
        FM_COL_TAXA_CONVERSAO_META: "Taxa Meta (Alvo)"
    })

    graf_taxa = px.line(
        df_plot_taxa, x=FM_COL_MES, y="Taxa de Conversão",
        color="Tipo de Taxa", facet_col=FM_COL_AREA,
        title="📊 Taxa de Conversão: Real vs Meta", template="plotly_dark", markers=True
    )

    # 8️⃣ Gráfico de Contratos
    df_contratos = df.groupby([FM_COL_AREA, FM_COL_MES]).sum(numeric_only=True).reset_index()
    df_plot_contratos = df_contratos.melt(
        id_vars=[FM_COL_AREA, FM_COL_MES],
        value_vars=[FM_COL_CONTRATOS_FECHADOS, FM_COL_META_ATINGIDA],
        var_name="Tipo",
        value_name="Total"
    )
    df_plot_contratos["Tipo"] = df_plot_contratos["Tipo"].replace({
        FM_COL_CONTRATOS_FECHADOS: "Contratos Fechados (Real)",
        FM_COL_META_ATINGIDA: "Meta Contratos (Alvo)"
    })

    graf_contratos = px.bar(
        df_plot_contratos, x=FM_COL_MES, y="Total", color="Tipo", barmode="group",
        facet_col=FM_COL_AREA, title="📈 Contratos Fechados vs Meta", template="plotly_dark"
    )

    # 9️⃣ Tabela
    cols_tabela = [
        FM_COL_MES, FM_COL_AREA, FM_COL_TOTAL_LEADS,
        FM_COL_CONTRATOS_FECHADOS, FM_COL_META_ATINGIDA,
        FM_COL_TAXA_CONVERSAO_REAL, FM_COL_TAXA_CONVERSAO_META
    ]
    tabela_df = df[[c for c in cols_tabela if c in df.columns]].head(30)
    tabela = dbc.Table.from_dataframe(tabela_df, striped=True, bordered=True, hover=True)

    # 🔟 Retorno final
    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return (
        mes_opts, pasta_opts, kpis,
        graf_taxa, graf_contratos,
        tabela, f"🕒 Atualizado às {hora}"
    )
