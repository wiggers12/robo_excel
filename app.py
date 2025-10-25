import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
# Importa constantes globais (assumindo que utils.py existe)
from utils import TEMA_DARK 

# ---------------- DASH APP E CONFIGURAÇÃO DE PÁGINAS ----------------
# use_pages=True detecta automaticamente os arquivos na pasta 'pages'
# Isso garante que a navegação funcione.
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server
app.title = "ROBÔ POWER BI IA EDITION"

# Componente Navbar (O SEU BOTÃO JÁ EXISTENTE)
navbar = dbc.NavbarSimple(
    children=[
        # Cria um link para CADA página registrada
        dbc.NavItem(dbc.NavLink(page['name'], href=page['path'], active="exact"))
        for page in dash.page_registry.values()
    ],
    brand="ROBÔ POWER BI IA EDITION",
    brand_href="/",
    color="dark",
    dark=True,
    className="mb-4",
)

# ---------------- LAYOUT MESTRE ----------------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    # O componente page_container renderiza a página ativa
    # Ele buscará automaticamente o conteúdo de pages/controle.py na rota '/'
    dash.page_container 
])

# ---------------- EXECUÇÃO ----------------
if __name__ == '__main__':
    app.run(debug=True)