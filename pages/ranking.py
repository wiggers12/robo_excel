import pandas as pd
import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from utils import carregar_dados, RK_SHEET_NAME

# ---------------- REGISTRO ----------------
register_page(
    __name__,
    name="🏆 Ranking Completo de Consultores",
    path="/ranking",
    order=5,
    title="Ranking Consultores Completo"
)

# ---------------- LAYOUT ----------------
layout = dbc.Container([
    html.Br(),
    html.H1("🏆 Ranking Completo de Consultores", className="text-center text-warning mb-4"),
    html.H5("📊 Pódio e métricas de desempenho consolidadas", className="text-center text-muted mb-4"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id="rk_filtro_mes", placeholder="Filtrar por Mês"), md=6),
        dbc.Col(dcc.Dropdown(id="rk_filtro_consultor", placeholder="Filtrar por Consultor"), md=6),
    ], className="mb-4"),

    html.Div(id="rk_kpis_gerais", className="mb-4"),

    html.Hr(),
    html.H3("🥇 Pódio - Top 3 Consultores", className="text-center text-light mb-4"),
    dcc.Graph(id="rk_podio", config={"displayModeBar": False}),

    html.Hr(),
    html.H3("📈 Rankings Detalhados", className="text-center text-info mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="rk_grafico_contratos"), md=6),
        dbc.Col(dcc.Graph(id="rk_grafico_conversao"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="rk_grafico_atingimento"), md=6),
        dbc.Col(dcc.Graph(id="rk_grafico_reunioes"), md=6),
    ]),

    html.Hr(),
    html.H4("📋 Tabela Detalhada", className="text-center text-light"),
    html.Div(id="rk_tabela_detalhada", className="mt-3"),

    html.Hr(),
    html.Div([
        dbc.Button("🔄 Atualizar Dados", id="rk_btn_recarregar", n_clicks=0, color="success"),
        html.Span(id="rk_status_recarregamento", style={"marginLeft": "15px", "color": "#8b949e"})
    ], className="text-center mt-3"),

    dcc.Interval(id="rk_timer_auto", interval=180000, n_intervals=0)
], fluid=True)

# ---------------- CALLBACK ----------------
@dash.callback(
    [
        Output("rk_filtro_mes", "options"),
        Output("rk_filtro_consultor", "options"),
        Output("rk_kpis_gerais", "children"),
        Output("rk_podio", "figure"),
        Output("rk_grafico_contratos", "figure"),
        Output("rk_grafico_conversao", "figure"),
        Output("rk_grafico_atingimento", "figure"),
        Output("rk_grafico_reunioes", "figure"),
        Output("rk_tabela_detalhada", "children"),
        Output("rk_status_recarregamento", "children"),
    ],
    [
        Input("rk_btn_recarregar", "n_clicks"),
        Input("rk_timer_auto", "n_intervals"),
        Input("rk_filtro_mes", "value"),
        Input("rk_filtro_consultor", "value"),
    ]
)
def atualizar_dashboard(n_clicks, n_timer, filtro_mes, filtro_consultor):
    df = carregar_dados(RK_SHEET_NAME)
    if df.empty:
        raise PreventUpdate

    df.columns = [c.strip().lower() for c in df.columns]

    # 🧩 Detecta e junta automaticamente as duas metades da planilha (consultor e consultor.1)
    if "consultor.1" in df.columns:
        metade1 = [c for c in df.columns if not c.endswith(".1")]
        metade2 = [c for c in df.columns if c.endswith(".1")]

        df1 = df[metade1].copy()
        df2 = df[metade2].copy()
        df2.columns = [c.replace(".1", "") for c in metade2]

        df = pd.concat([df1, df2], ignore_index=True)

    # Limpa e normaliza
    df = df.fillna(0)
    df["consultor"] = df["consultor"].astype(str).str.strip().str.title()
    df["mes"] = df["mes"].astype(str).str.strip()

    # Filtros
    if filtro_mes:
        df = df[df["mes"] == filtro_mes]
    if filtro_consultor:
        df = df[df["consultor"] == filtro_consultor]

    mes_opts = [{"label": m, "value": m} for m in sorted(df["mes"].unique())]
    cons_opts = [{"label": c, "value": c} for c in sorted(df["consultor"].unique())]

    # 🔹 KPIs principais
    total_contratos = df["total_contratos"].sum()
    media_conversao = df["taxa_conversao_total"].mean() * 100
    total_reunioes = df["total_reunioes_realizadas_mes"].sum()
    media_atingimento = df["_atingimento_contratos_mes"].mean() * 100

    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total de Contratos", className="text-center text-secondary"),
            html.H3(f"{total_contratos:,.0f}", className="text-center text-success")
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Taxa de Conversão Média", className="text-center text-secondary"),
            html.H3(f"{media_conversao:.2f}%", className="text-center text-info")
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Total de Reuniões", className="text-center text-secondary"),
            html.H3(f"{total_reunioes:,.0f}", className="text-center text-warning")
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Atingimento Médio", className="text-center text-secondary"),
            html.H3(f"{media_atingimento:.2f}%", className="text-center text-primary")
        ])), md=3)
    ], className="mb-4")

    # 🔹 Ranking consolidado
    df_ranking = df.groupby("consultor").agg({
        "total_contratos": "sum",
        "taxa_conversao_total": "mean",
        "_atingimento_contratos_mes": "mean",
        "total_reunioes_realizadas_mes": "sum"
    }).reset_index()

    df_ranking["taxa_conversao_total"] *= 100
    df_ranking["_atingimento_contratos_mes"] *= 100
    df_ranking = df_ranking.sort_values(by="total_contratos", ascending=False)

    # 🥇 Pódio
    podio = df_ranking.head(3)
    fig_podio = go.Figure(data=[
        go.Bar(
            x=podio["consultor"],
            y=podio["total_contratos"],
            text=[f"{v:,.0f}" for v in podio["total_contratos"]],
            textposition="outside",
            marker=dict(color=["#FFD700", "#C0C0C0", "#CD7F32"])
        )
    ])
    fig_podio.update_layout(
        title="🏅 Top 3 Consultores",
        template="plotly_dark",
        xaxis_title="Consultor",
        yaxis_title="Total de Contratos"
    )

    # 📊 Gráficos Detalhados
    graf_contratos = px.bar(df_ranking, x="total_contratos", y="consultor", orientation="h",
                            color="total_contratos", title="Ranking por Contratos", template="plotly_dark")
    graf_conversao = px.bar(df_ranking, x="taxa_conversao_total", y="consultor", orientation="h",
                            color="taxa_conversao_total", title="Ranking por Conversão (%)", template="plotly_dark")
    graf_atingimento = px.bar(df_ranking, x="_atingimento_contratos_mes", y="consultor", orientation="h",
                              color="_atingimento_contratos_mes", title="Ranking por Atingimento (%)", template="plotly_dark")
    graf_reunioes = px.bar(df_ranking, x="total_reunioes_realizadas_mes", y="consultor", orientation="h",
                           color="total_reunioes_realizadas_mes", title="Ranking por Reuniões", template="plotly_dark")

    tabela = dbc.Table.from_dataframe(df_ranking, striped=True, bordered=True, hover=True, class_name="table-dark")

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    return mes_opts, cons_opts, kpis, fig_podio, graf_contratos, graf_conversao, graf_atingimento, graf_reunioes, tabela, f"🕒 Atualizado às {hora}"
