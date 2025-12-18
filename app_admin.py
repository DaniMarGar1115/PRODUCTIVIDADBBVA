import streamlit as st
import pandas as pd
from datetime import datetime, date
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
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    gh_put_file(repo_path, csv_bytes, msg)

# =========================
# CONFIGURACIÓN (METAS)
# =========================
def cargar_config():
    try:
        cfg = cargar_df_desde_github(SETTINGS_PATH)
        row = cfg.iloc[0].to_dict() if not cfg.empty else {}
    except Exception:
        row = {}

    return {
        "meta_dia": int(row.get("meta_dia", 20)),
        "meta_mes": int(row.get("meta_mes", 300)),
        "valor_prod": float(row.get("valor_prod", 3500)),
        "valor_adic": float(row.get("valor_adic", 4000)),
        "valor_sabado": float(row.get("valor_sabado", 5000)),
        "salario_base_mensual": float(row.get("salario_base_mensual", 1500000)),
    }

def guardar_config(config):
    df_cfg = pd.DataFrame([config])
    guardar_df_a_github(SETTINGS_PATH, df_cfg, "Update config_productividad")

config = cargar_config()

# =========================
# CARGA DE REGISTROS
# =========================
try:
    df = cargar_df_desde_github(CSV_PATH)
    if not df.empty and "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
except Exception:
    df = pd.DataFrame()

COLUMNAS = [
    "ID","Empleado","Lider","Numero_caso",
    "Fecha","Tipo_caso","Categoria","Duplicado"
]

if df.empty:
    df = pd.DataFrame(columns=COLUMNAS)

st.session_state["registros"] = df
df = st.session_state["registros"]

# =========================
# UI SIMPLE (PRUEBA)
# =========================
st.title("PRODUCTIVIDAD Y EXTRAS BBVA PQRS")

nombre = st.text_input("Nombre del empleado")
caso = st.text_input("Número de caso")

if st.button("Guardar caso"):
    if nombre and caso:
        nuevo = {
            "ID": (df["ID"].max() + 1) if not df.empty else 1,
            "Empleado": nombre,
            "Lider": "N/A",
            "Numero_caso": caso,
            "Fecha": date.today(),
            "Tipo_caso": "Productividad",
            "Categoria": "Finalizado",
            "Duplicado": False
        }
        df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
        st.session_state["registros"] = df
        guardar_df_a_github(CSV_PATH, df, "Update registros productividad")
        st.success("Caso guardado correctamente")

st.dataframe(df)
