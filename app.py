import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from utils import TEMA_DARK

# ---------------- DASH APP (RAIZ) ----------------
app = dash.Dash(
    __name__,
    use_pages=True,  # Detecta automaticamente os arquivos na pasta /pages
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

server = app.server  # Necessário para o Render rodar via gunicorn
app.title = "ROBÔ POWER BI IA EDITION"

# ---------------- NAVBAR DINÂMICA ----------------
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page["name"], href=page["path"], active="exact"))
        for page in dash.page_registry.values()
    ],
    brand="🤖 ROBÔ POWER BI IA EDITION",
    brand_href="/",
    color="primary",
    dark=True,
    class_name="mb-4",
)

# ---------------- LAYOUT PRINCIPAL ----------------
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    navbar,
    html.Div(dash.page_container, className="mt-4"),
], fluid=True)

# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
