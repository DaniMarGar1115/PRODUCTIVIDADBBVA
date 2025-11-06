
import os
import pandas as pd
import streamlit as st
from datetime import date

BBVA_PRIMARY = "#072146"
BBVA_SECONDARY = "#00A1E0"
LOGO_URL = os.getenv("BBVA_LOGO_URL", "")

st.set_page_config(page_title="BBVA | Registro diario", page_icon="💼", layout="wide")
st.markdown('''
<style>
.stApp { background: #ffffff; }
.bbva-header { display:flex; align-items:center; gap:14px; }
.bbva-title { font-size: 28px; font-weight: 800; color: #072146; letter-spacing:.2px; }
.bbva-sub { color:#00A1E0; font-weight:600; }
.bbva-card { border:1px solid #e6e9ef; border-radius:12px; padding:1rem; }
</style>
''', unsafe_allow_html=True)

DATA_PATH = "registro_empresarial2.csv"

def ensure_csv(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")

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
            d = pd.to_datetime(d).date()
        return f"{d.year:04d}-{d.month:02d}"
    except Exception:
        return ""

ensure_csv(DATA_PATH, ["Fecha","Empleado","Área","Lider","Tipo","Numero_Caso","Estado","Horas_Extra","Mes","Año"])

st.markdown('<div class="bbva-header">', unsafe_allow_html=True)
if LOGO_URL:
    st.image(LOGO_URL, width=110)
st.markdown('<div class="bbva-title">BBVA · Registro diario</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.caption("Ingresa Productividad y Variable con su estado. También registra tus horas extra.")

with st.form("form_registro", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha = st.date_input("Fecha", value=date.today())
        empleado = st.text_input("Nombre del empleado")
    with c2:
        area = st.text_input("Área (opcional)")
        lider = st.selectbox("Líder", ["— seleccionar —"] + ["Alejandra Puentes", "Carlos Sierra", "Edisson Ramirez", "Gabrielle Monroy"], index=0)
    with c3:
        horas_extra = st.number_input("Horas extra (del día)", min_value=0, step=1, value=0)

    st.markdown("### Casos de Productividad")
    prod_df = st.data_editor(
        pd.DataFrame(columns=["Numero_Caso","Estado"]).astype({"Numero_Caso":"object","Estado":"object"}),
        column_config={
            "Numero_Caso": st.column_config.TextColumn("Número de caso", required=False),
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Finalizado", "Defensoria", "Tutela"], required=False),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="prod_editor"
    )

    st.markdown("### Casos de Variable")
    var_df = st.data_editor(
        pd.DataFrame(columns=["Numero_Caso","Estado"]).astype({"Numero_Caso":"object","Estado":"object"}),
        column_config={
            "Numero_Caso": st.column_config.TextColumn("Número de caso (variable)", required=False),
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Finalizado", "Defensoria", "Tutela"], required=False),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="var_editor"
    )

    submitted = st.form_submit_button("✅ Guardar")
    if submitted:
        if not empleado.strip():
            st.error("El nombre del empleado es obligatorio.")
        else:
            rows = []
            mes = month_str(fecha)
            anio = fecha.year
            if horas_extra and horas_extra > 0:
                rows.append({
                    "Fecha": fecha.strftime("%Y-%m-%d"),
                    "Empleado": empleado.strip(),
                    "Área": area.strip(),
                    "Lider": lider if lider != "— seleccionar —" else "",
                    "Tipo": "HorasExtra",
                    "Numero_Caso": "",
                    "Estado": "",
                    "Horas_Extra": int(horas_extra),
                    "Mes": mes, "Año": anio
                })
            for _, r in prod_df.dropna(how="all").iterrows():
                if str(r.get("Numero_Caso","")).strip():
                    rows.append({
                        "Fecha": fecha.strftime("%Y-%m-%d"),
                        "Empleado": empleado.strip(),
                        "Área": area.strip(),
                        "Lider": lider if lider != "— seleccionar —" else "",
                        "Tipo": "Productividad",
                        "Numero_Caso": str(r["Numero_Caso"]).strip(),
                        "Estado": r["Estado"] if pd.notna(r["Estado"]) else "",
                        "Horas_Extra": 0,
                        "Mes": mes, "Año": anio
                    })
            for _, r in var_df.dropna(how="all").iterrows():
                if str(r.get("Numero_Caso","")).strip():
                    rows.append({
                        "Fecha": fecha.strftime("%Y-%m-%d"),
                        "Empleado": empleado.strip(),
                        "Área": area.strip(),
                        "Lider": lider if lider != "— seleccionar —" else "",
                        "Tipo": "Variable",
                        "Numero_Caso": str(r["Numero_Caso"]).strip(),
                        "Estado": r["Estado"] if pd.notna(r["Estado"]) else "",
                        "Horas_Extra": 0,
                        "Mes": mes, "Año": anio
                    })
            if not rows:
                st.warning("No agregaste casos ni horas extra.")
            else:
                cur = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
                cur = pd.concat([cur, pd.DataFrame(rows)], ignore_index=True)
                cur.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
                st.success(f"Se guardaron {len(rows)} registro(s). ¡Gracias!")
