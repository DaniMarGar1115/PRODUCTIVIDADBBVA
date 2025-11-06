import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date
from io import StringIO

# ============= Branding BBVA =============
st.set_page_config(page_title="BBVA | Portal único (Empleado + Admin)", page_icon="💼", layout="wide")
BBVA_PRIMARY   = "#072146"  # Azul BBVA
BBVA_SECONDARY = "#00A1E0"
LOGO_URL = os.getenv("BBVA_LOGO_URL", "")  # opcional: Settings→Secrets: BBVA_LOGO_URL="https://..."
ADMIN_PIN = os.getenv("ADMIN_PIN", "bbva2025")  # Settings→Secrets para cambiar

st.markdown('''
<style>
.stApp { background: #ffffff; }
.bbva-header { display:flex; align-items:center; gap:14px; }
.bbva-title  { font-size: 28px; font-weight: 800; color: #072146; letter-spacing:.2px; }
.bbva-sub    { color:#00A1E0; font-weight:600; }
.bbva-card   { border:1px solid #e6e9ef; border-radius:12px; padding:1rem; }
</style>
''', unsafe_allow_html=True)

# ============= Constantes =============
LIDERES = ["Alejandra Puentes", "Carlos Sierra", "Edisson Ramirez", "Gabrielle Monroy"]
ESTADOS = ["Finalizado", "Defensoria", "Tutela"]
META_DIARIA = 12

# Archivos locales (mismo contenedor = misma app)
REG_PATH = "registro_portal.csv"
TAR_PATH = "tarifas_portal.csv"

# ============= Utilidades =============
def ensure_csv(path, columns, default_rows=None):
    if not os.path.exists(path):
        if default_rows is None:
            pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")
        else:
            pd.DataFrame(default_rows).to_csv(path, index=False, encoding="utf-8-sig")

def load_csv(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(path)
    return pd.DataFrame()

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

def month_str(d):
    try:
        if isinstance(d, str):
