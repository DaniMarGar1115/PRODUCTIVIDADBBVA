
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

BBVA_PRIMARY = "#072146"
BBVA_SECONDARY = "#00A1E0"
LOGO_URL = os.getenv("BBVA_LOGO_URL", "")
ADMIN_PIN = os.getenv("ADMIN_PIN", "bbva2025")
META_DIARIA = 12

st.set_page_config(page_title="BBVA | Panel Admin", page_icon="🛠️", layout="wide")
st.markdown('''
<style>
.stApp { background: #ffffff; }
.bbva-header { display:flex; align-items:center; gap:14px; }
.bbva-title { font-size: 28px; font-weight: 800; color: #072146; }
.badge-ok { background:#e6f4ea; color:#137333; padding:4px 8px; border-radius:999px; font-weight:600; }
.badge-ko { background:#fce8e6; color:#a50b0b; padding:4px 8px; border-radius:999px; font-weight:600; }
</style>
''', unsafe_allow_html=True)

DATA_PATH = "registro_empresarial2.csv"
TARIFAS_PATH = "tarifas_empresarial.csv"

def load_csv(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(path)
    return pd.DataFrame()

def format_cop(v):
    try:
        n = float(v)
    except Exception:
        return "0"
    s = f"{n:,.0f}"
    return "$ " + s.replace(",", ".") + " COP"

# Gate
st.sidebar.header("🔐 Acceso")
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if not st.session_state.is_admin:
    pin = st.sidebar.text_input("PIN", type="password", help="PIN por defecto: bbva2025")
    if st.sidebar.button("Entrar"):
        if pin == ADMIN_PIN:
            st.session_state.is_admin = True
            st.sidebar.success("Acceso concedido.")
        else:
            st.sidebar.error("PIN incorrecto")
else:
    st.sidebar.success("Modo administrador")

st.markdown('<div class="bbva-header">', unsafe_allow_html=True)
if LOGO_URL:
    st.image(LOGO_URL, width=110)
st.markdown('<div class="bbva-title">BBVA · Panel administrativo</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.is_admin:
    st.info("Ingresa el PIN en la barra lateral para ver el panel.")
else:
    df = load_csv(DATA_PATH)
    if df.empty:
        st.warning("Aún no hay datos registrados desde el link de empleados.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            f_mes = st.multiselect("Mes", sorted(df["Mes"].dropna().unique().tolist()))
        with c2:
            f_emp = st.multiselect("Empleado", sorted(df["Empleado"].dropna().unique().tolist()))
        with c3:
            f_lid = st.multiselect("Líder", sorted(df["Lider"].dropna().unique().tolist()))

        if f_mes: df = df[df["Mes"].isin(f_mes)]
        if f_emp: df = df[df["Empleado"].isin(f_emp)]
        if f_lid: df = df[df["Lider"].isin(f_lid)]

        st.subheader("1) Control por tipo y estado")
        pivot = df.pivot_table(index=["Tipo","Estado"], values="Numero_Caso", aggfunc="count", fill_value=0).reset_index().rename(columns={"Numero_Caso":"Cantidad"})
        st.dataframe(pivot, use_container_width=True)

        st.subheader("2) Cumplimiento diario (meta = 12 de Productividad)")
        prod = df[(df["Tipo"]=="Productividad") & (df["Numero_Caso"].astype(str).str.strip()!="")].copy()
        dia = prod.groupby(["Empleado","Fecha"], as_index=False).agg(Total_Casos=("Numero_Caso","count"))
        dia["Cumple"] = dia["Total_Casos"] >= META_DIARIA
        dia["Estado"] = dia["Cumple"].map(lambda x: "🟢 Cumplió" if x else "🔴 No cumplió")
        st.dataframe(dia.sort_values(["Fecha","Empleado"]), use_container_width=True)

        st.subheader("3) Estados por empleado y mes (Productividad vs Variable)")
        estado_det = df.copy()
        estado_det["Tiene_Caso"] = estado_det["Numero_Caso"].astype(str).str.strip() != ""
        estado_det = estado_det[estado_det["Tiene_Caso"]]
        tabla = estado_det.pivot_table(index=["Empleado","Mes","Tipo"], columns="Estado", values="Numero_Caso", aggfunc="count", fill_value=0)
        st.dataframe(tabla, use_container_width=True)
