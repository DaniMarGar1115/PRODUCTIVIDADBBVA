import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
import requests
from io import BytesIO

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(
    page_title="PRODUCTIVIDAD Y EXTRAS BBVA PQRS",
    layout="wide"
)

# Paleta de colores BBVA
BBVA_PRIMARY = "#0039A6"       # Azul BBVA
BBVA_PRIMARY_DARK = "#002B76"  # Azul BBVA más oscuro
BBVA_WHITE = "#FFFFFF"

# Rutas (en GitHub)
CSV_PATH = st.secrets.get("REGISTROS_PATH", "data/registro_empresarial2.csv")
SETTINGS_PATH = st.secrets.get("CONFIG_PATH", "data/config_productividad.csv")

# =========================
# GITHUB HELPERS (PERSISTENCIA)
# =========================
def _gh_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    }

def gh_get_file(repo_path: str):
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    r = requests.get(url, headers=_gh_headers())
    if r.status_code == 200:
        js = r.json()
        return base64.b64decode(js["content"]), js["sha"]
    if r.status_code == 404:
        return b"", None
    raise Exception(f"GitHub GET error {r.status_code}: {r.text}")

def gh_put_file(repo_path: str, content_bytes: bytes, message: str):
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    _, sha = gh_get_file(repo_path)

    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=_gh_headers(), json=payload)
    if r.status_code not in (200, 201):
        raise Exception(f"GitHub PUT error {r.status_code}: {r.text}")

def cargar_df_desde_github(repo_path: str) -> pd.DataFrame:
    content, _ = gh_get_file(repo_path)
    if not content:
        return pd.DataFrame()
    return pd.read_csv(BytesIO(content), encoding="utf-8-sig")

def guardar_df_a_github(repo_path: str, df: pd.DataFrame, msg: str):
    # ✅ CORREGIDO: sin recursión
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    gh_put_file(repo_path, csv_bytes, msg)

# =========================
# ESTILOS GLOBALES
# =========================
st.markdown(
    f"""
    <style>
    /* Fondo general blanco */
    .stApp {{
        background-color: {BBVA_WHITE};
        font-family: "Segoe UI", "Roboto", sans-serif;
        color: #000000 !important;
    }}

    /* Contenedor principal */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
        margin: 0 auto;
    }}

    /* Encabezado con logo y línea azul */
    .bbva-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 10px 0 20px 0;
        border-bottom: 3px solid {BBVA_PRIMARY};
        margin-bottom: 24px;
    }}

    .bbva-title {{
        font-size: 30px;
        font-weight: 700;
        color: {BBVA_PRIMARY};
        margin: 0;
    }}

    .bbva-subtitle {{
        font-size: 15px;
        font-weight: 400;
        color: #000000;
        margin: 0;
    }}

    /* Tarjetas de métricas */
    .metric-card {{
        background-color: {BBVA_WHITE};
        color: #000000;
        border: 1px solid #DCE3F0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }}

    /* Botón principal azul BBVA */
    button[kind="primary"] {{
        background-color: {BBVA_PRIMARY} !important;
        color: {BBVA_WHITE} !important;
        border-radius: 999px;
        font-weight: 600;
        border: none;
        padding: 10px 20px;
    }}

    button[kind="primary"]:hover {{
        background-color: {BBVA_PRIMARY_DARK} !important;
    }}

    /* Inputs y selects blancos, texto negro */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    .stDataFrame, .stDataEditor {{
        color: #000000 !important;
    }}

    /* Barra lateral blanca con borde azul */
    section[data-testid="stSidebar"] {{
        background-color: {BBVA_WHITE} !important;
        border-right: 2px solid {BBVA_PRIMARY};
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# ENCABEZADO CON LOGO
# =========================
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_bbva.png"):
        st.image("logo_bbva.png", use_container_width=False)
with col_title:
    st.markdown(
        """
        <div class="bbva-header">
            <div>
                <p class="bbva-title">PRODUCTIVIDAD Y EXTRAS BBVA PQRS</p>
                <p class="bbva-subtitle">Control de casos, metas diarias y análisis mensual por analista</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================
# CONFIGURACIÓN (PERSISTENCIA EN GITHUB)
# =========================
def cargar_config():
    """Lee la configuración desde GitHub (CSV) o crea una por defecto."""
    try:
        cfg = cargar_df_desde_github(SETTINGS_PATH)
        row = cfg.iloc[0].to_dict() if not cfg.empty else {}
    except Exception:
        row = {}

    return {
        "meta_dia": int(row.get("meta_dia", 20)),
        "meta_mes": int(row.get("meta_mes", 300)),
        "valor_prod": float(row.get("valor_prod", 3500.0)),
        "valor_adic": float(row.get("valor_adic", 4000.0)),
        "valor_sabado": float(row.get("valor_sabado", 5000.0)),
        "salario_base_mensual": float(row.get("salario_base_mensual", 1_500_000.0)),
    }

def guardar_config(config: dict):
    """Guarda la configuración actual en GitHub."""
    df_cfg = pd.DataFrame([config])
    guardar_df_a_github(SETTINGS_PATH, df_cfg, "Update config_productividad")

# Cargamos config
config = cargar_config()
meta_dia = config["meta_dia"]
meta_mes = config["meta_mes"]
valor_prod = config["valor_prod"]
valor_adic = config["valor_adic"]
valor_sabado = config["valor_sabado"]
salario_base_mensual = config["salario_base_mensual"]

# =========================
# CARGA DE DATOS PERSISTENTES (DESDE GITHUB)
# =========================
try:
    df = cargar_df_desde_github(CSV_PATH)
    if not df.empty and "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date
except Exception:
    df = pd.DataFrame()

COLUMNAS = [
    "ID", "Empleado", "Lider", "Numero_caso", "Fecha",
    "Tipo_caso", "Categoria", "Duplicado",
]

if df.empty:
    df = pd.DataFrame(columns=COLUMNAS)
else:
    for col in COLUMNAS:
        if col not in df.columns:
            if col == "ID":
                df[col] = range(1, len(df) + 1)
            elif col == "Duplicado":
                df[col] = False
            else:
                df[col] = None
    df = df[COLUMNAS]

if df["ID"].isnull().any():
    df["ID"] = range(1, len(df) + 1)
df["ID"] = df["ID"].astype(int)

# Recalcular duplicados
if "Numero_caso" in df.columns and "Empleado" in df.columns:
    df["Duplicado"] = df.duplicated(subset=["Empleado", "Numero_caso"], keep=False)
else:
    df["Duplicado"] = False

st.session_state["registros"] = df
df = st.session_state["registros"]

# =========================
# CONSTANTES
# =========================
LIDERES = [
    "Alejandra Puentes",
    "Carlos Cierra",
    "Edisson Ramirez",
    "Gabrielle Monroy",
    "Melissa Rodriguez",
]
TIPOS_CASO = ["Productividad", "Adicional", "Meta sábado"]
CATEGORIAS = ["Finalizado", "Tutela", "Defensoría"]

# =========================
# BARRA LATERAL
# =========================
st.sidebar.header("Configuración")
perfil = st.sidebar.selectbox("Perfil", ["Empleado", "Administrador", "Líder"])

salario_base_mensual = st.sidebar.number_input(
    "Salario base mensual ($)",
    min_value=0.0,
    value=float(salario_base_mensual),
    step=100_000.0,
)

clave = ""
if perfil == "Líder":
    clave = st.sidebar.text_input("Contraseña líderes", type="password")
    if clave != "BBVA2025":
        st.sidebar.warning("Contraseña incorrecta. Solo lectura.")
    else:
        st.sidebar.success("Acceso de líder habilitado.")
        meta_dia = st.sidebar.number_input("Meta de casos por día", min_value=0, value=int(meta_dia), step=1)
        meta_mes = st.sidebar.number_input("Meta de casos por mes", min_value=0, value=int(meta_mes), step=5)

        st.sidebar.markdown("---")
        st.sidebar.markdown("Tarifas por tipo de caso:")
        valor_prod = st.sidebar.number_input("Valor por caso Productividad ($)", min_value=0.0, value=float(valor_prod), step=500.0)
        valor_adic = st.sidebar.number_input("Valor por caso Adicional ($)", min_value=0.0, value=float(valor_adic), step=500.0)
        valor_sabado = st.sidebar.number_input("Valor por caso Meta sábado ($)", min_value=0.0, value=float(valor_sabado), step=500.0)

        # ✅ Guardar SOLO si líder decide
        if st.sidebar.button("Guardar configuración"):
            config_guardar = {
                "meta_dia": int(meta_dia),
                "meta_mes": int(meta_mes),
                "valor_prod": float(valor_prod),
                "valor_adic": float(valor_adic),
                "valor_sabado": float(valor_sabado),
                "salario_base_mensual": float(salario_base_mensual),
            }
            guardar_config(config_guardar)
            st.sidebar.success("Configuración guardada.")

st.markdown("---")

# =========================
# FUNCIONES AUXILIARES
# =========================
def valor_fila(fila):
    if fila["Tipo_caso"] == "Productividad":
        return valor_prod
    elif fila["Tipo_caso"] == "Adicional":
        return valor_adic
    else:
        return valor_sabado

def calcular_racha_meta(df_emp_mes, meta_diaria):
    if df_emp_mes.empty:
        return False
    fechas = pd.to_datetime(df_emp_mes["Fecha"]).dt.date
    primer_dia = fechas.min()
    ultimo_dia = fechas.max()
    rango = pd.date_range(primer_dia, ultimo_dia, freq="D").date
    df_por_dia = df_emp_mes.groupby(pd.to_datetime(df_emp_mes["Fecha"]).dt.date)["ID"].count()
    for d in rango:
        casos_dia = df_por_dia.get(d, 0)
        if casos_dia < meta_diaria:
            return False
    return True

# =========================
# PERFIL EMPLEADO
# =========================
if perfil == "Empleado":
    st.subheader("Registro de productividad (Empleado)")
    st.write(
        "Puede registrar sus casos en modo rápido (pegando una lista de números de caso) "
        "o en modo detallado (tabla editable)."
    )

    col_emp1, col_emp2 = st.columns(2)
    with col_emp1:
        nombre_empleado = st.text_input("Nombre del empleado")
    with col_emp2:
        lider = st.selectbox("Líder a cargo", LIDERES)

    hoy = date.today()

    modo_registro = st.radio(
        "Modo de registro de casos",
        ["Ingreso rápido (lista de números de caso)", "Ingreso detallado (tabla)"],
    )

    # ---------- MODO RÁPIDO ----------
    if modo_registro == "Ingreso rápido (lista de números de caso)":
        st.markdown("### Ingreso rápido de casos")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            fecha_casos = st.date_input("Fecha de los casos", value=hoy)
        with col_r2:
            tipo_caso_rapido = st.selectbox("Tipo de caso", TIPOS_CASO, key="tipo_rapido")
        with col_r3:
            categoria_rapida = st.selectbox("Categoría", CATEGORIAS, key="cat_rapida")

        lista_texto = st.text_area(
            "Ingrese los números de caso (uno por línea o separados por comas)",
            height=150,
        )

        if st.button("Guardar casos rápidos", type="primary"):
            if nombre_empleado.strip() == "":
                st.warning("Por favor ingrese el nombre del empleado.")
            elif lista_texto.strip() == "":
                st.warning("Por favor ingrese al menos un número de caso.")
            else:
                raw_items = []
                for linea in lista_texto.splitlines():
                    partes = [p.strip() for p in linea.replace(";", ",").split(",")]
                    raw_items.extend(p for p in partes if p)

                numeros_caso = [x for x in raw_items if x != ""]

                if not numeros_caso:
                    st.warning("No se encontraron números de caso válidos.")
                else:
                    df_nuevo = pd.DataFrame(
                        {
                            "Numero_caso": numeros_caso,
                            "Fecha": [fecha_casos] * len(numeros_caso),
                            "Tipo_caso": [tipo_caso_rapido] * len(numeros_caso),
                            "Categoria": [categoria_rapida] * len(numeros_caso),
                        }
                    )
                    df_nuevo["Empleado"] = nombre_empleado
                    df_nuevo["Lider"] = lider

                    next_id = 1 if df.empty else int(df["ID"].max()) + 1
                    df_nuevo["ID"] = range(next_id, next_id + len(df_nuevo))
                    df_nuevo["Duplicado"] = False

                    df_nuevo = df_nuevo[
                        ["ID","Empleado","Lider","Numero_caso","Fecha","Tipo_caso","Categoria","Duplicado"]
                    ]

                    st.session_state["registros"] = pd.concat([st.session_state["registros"], df_nuevo], ignore_index=True)
                    df = st.session_state["registros"]

                    df["Duplicado"] = df.duplicated(subset=["Empleado", "Numero_caso"], keep=False)

                    guardar_df_a_github(CSV_PATH, df, "Update registros productividad")

                    st.success(f"Se guardaron {len(numeros_caso)} caso(s) correctamente en modo rápido.")
