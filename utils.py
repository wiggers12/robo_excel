import pandas as pd
import unidecode
import dash_bootstrap_components as dbc
from dash import html

# ==========================================================
# 🔧 CONFIGURAÇÕES GLOBAIS
# ==========================================================
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1SEeX-g_Wdl0XpdXt90nDgDBPrjbS3zh_8yvAVpoxpPs/export?format=xlsx"
TEMA_DARK = "#0d1117"
COR_CARD_BG = "#161b22"

# ==========================================================
# 📥 FUNÇÃO DE CARREGAMENTO UNIVERSAL
# ==========================================================
def carregar_dados(sheet_name):
    """Carrega uma aba do Google Sheets e normaliza colunas (sem acento, sem símbolo)."""
    try:
        xls = pd.ExcelFile(SHEETS_URL)
        if sheet_name not in xls.sheet_names:
            raise Exception(f"Aba '{sheet_name}' não encontrada.")
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df.columns = [col.strip() for col in df.columns]

        # 🧹 Normaliza nomes de colunas (para evitar erro nos callbacks)
        df.columns = [
            unidecode.unidecode(c)
           .replace(":", "")
.replace("%", "")
.replace("/", "_")
.replace("?", "")
.replace("(", "")
.replace(")", "")
.replace(" ", "_")
.replace("-", "_")
.lower()

            for c in df.columns
        ]

        print(f"✅ Dados de '{sheet_name}' carregados com sucesso! {len(df)} linhas, {len(df.columns)} colunas")
        print(f"🔍 Colunas detectadas: {list(df.columns)[:10]}")
        return df

    except Exception as e:
        print(f"❌ Erro crítico ao carregar planilha '{sheet_name}': {e}")
        return pd.DataFrame()

# ==========================================================
# 📊 NOMES DE COLUNAS PADRÃO (PÓS-NORMALIZAÇÃO)
# ==========================================================
# Controle de Processos
CP_COL_AREA = "area_pasta"
CP_COL_STATUS = "status_final"
CP_COL_UF = "uf_municipio"
CP_COL_DATA_DIST = "data_distribuicao"
CP_COL_DISTRIBUIDO = "processo_distribuido"
CP_COL_MES_COMP = "mes_competencia"
CP_COL_RESPONSAVEL = "responsavel_juridico"
CP_COL_SLA = "status_sla_distribuicao"
CP_COL_CONSULTOR = "consultor"

# Funil x Metas
FM_COL_MES = "mes"
FM_COL_AREA_PASTA_PROXY = "consultor"
FM_COL_META_MENSAL = "meta_mensal_pasta"
FM_COL_META_ATINGIDA = "meta_mensal_atingida"
FM_COL_TAXA_CONVERSAO_META = "taxa_de_conversao_por_area_mes"
FM_COL_LEADS_RECEBIDOS = "leads_recebidos_por_area_mes"
FM_COL_TAXA_CONVERSAO_REAL = "taxa_de_conversao_por_area_mes"
FM_COL_CONTRATOS_REAL = "meta_mensal_atingida"

# Funil de Precatório
FP_COL_CONSULTOR = "consultor"
FP_COL_STATUS = "status"
FP_COL_MOTIVO = "motivo"
FP_COL_PLATFORM = "platform"
FP_COL_UF = "uf"
FP_COL_ORIGEM = "qual_e_a_origem_do_seu_precatorio"
FP_COL_MES = "mes"
FP_COL_NOME = "nome"
FP_COL_TELEFONE = "telefone"

# Ranking
RK_SHEET_NAME = "ranking"
RK_COL_CONSULTOR = "consultor"
RK_COL_MES = "mes"
RK_COL_PASTA = "pasta"
RK_COL_META = "meta_contratos_mes"
RK_COL_CONTRATOS = "total_contratos"
RK_COL_TAXA_CONVERSAO = "taxa_conversao_total"
RK_COL_ATINGIMENTO = "_atingimento_contratos_mes"
RK_COL_REUNIOES = "total_reunioes_realizadas_mes"

# Produção Diária
PD_SHEET_NAME = "producao_diaria"
PD_COL_CONSULTOR = "consultor"
PD_COL_DATA = "data"
PD_COL_LIGACOES = "ligacoes_contatos_dia"
PD_COL_NOTA_LIGACOES = "status_ligacoes"
PD_COL_COTACAO = "cotacoes"
PD_COL_NOTA_COTACAO = "status_cotacoes"
PD_COL_OBSERVACOES = "observacoes"

# Constantes para status
PD_STATUS_ATINGIDA = "meta_atingida"
PD_STATUS_NAO_ATINGIDA = "nao_atingida"
PD_STATUS_PARCIAL = "parcial"

# ==========================================================
# 💡 UI UTIL
# ==========================================================
def criar_card_kpi(titulo, valor, cor="text-light"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(titulo, className="text-center text-secondary"),
            html.H3(valor, className=f"text-center {cor}")
        ]),
        color=COR_CARD_BG,
        inverse=True,
        class_name="shadow-lg rounded-4"
    )
