import os
import base64
import json
from io import StringIO
from datetime import date

import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt

# ===========================
# Configuración / Branding
# ===========================
st.set_page_config(page_title="BBVA | Portal único (Empleado + Admin)", page_icon="💼", layout="wide")

BBVA_PRIMARY = "#072146"      # Azul BBVA
BBVA_SECONDARY = "#00A1E0"    # Celeste BBVA
LOGO_URL = st.secrets.get("BBVA_LOGO_URL", os.getenv("BBVA_LOGO_URL", ""))

ADMIN_PIN = st.secrets.get("ADMIN_PIN", os.getenv("ADMIN_PIN", "bbva2025"))

st.markdown(f"""
<style>
.stApp {{
  background-color: #ffffff;
}}
.bbva-header {{
  display:flex; align-items:center; gap:14px; margin-bottom: 10px;
}}
.bbva-title {{
  font-size: 28px; font-weight: 800; color: {BBVA_PRIMARY}; letter-spacing: .3px;
}}
.bbva-sub {{
  color:{BBVA_SECONDARY}; font-weight:600;
}}
.bbva-card {{
  border: 1px solid #e6e9ef; border-radius: 12px; padding: 1rem; background-color: #f8f9fa;
}}
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="bbva-header">', unsafe_allow_html=True)
if LOGO_URL:
    try:
        st.image(LOGO_URL, width=110)
    except Exception:
        pass
st.markdown('<div class="bbva-title">BBVA · Portal único <span class="bbva-sub"> Empleado + Admin </span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===========================
# Parámetros
# ===========================
LIDERES = ["Alejandra Puentes", "Carlos Sierra", "Edisson Ramirez", "Gabrielle Monroy"]
ESTADOS = ["Finalizado", "Defensoria", "Tutela"]
META_DIARIA = 12

# Guardado en GitHub si hay secrets; si no, local
USE_GH = ("GITHUB_TOKEN" in st.secrets) and ("GH_REPO" in st.secrets)
GH_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GH_REPO = st.secrets.get("GH_REPO", "")
GH_BRANCH = st.secrets.get("GH_BRANCH", "main")
GH_PATH_REG = st.secrets.get("GH_PATH_REG", "registro_portal.csv")
API_BASE = f"https://api.github.com/repos/{GH_REPO}/contents"
HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}

LOCAL_CSV = "registro_portal_local.csv"  # respaldo local si no hay GitHub

# ===========================
# Utilidades
# ===========================
def month_str(d):
    try:
        if isinstance(d, str):
            d = pd.to_datetime(d).date()
        return f"{d.year:04d}-{d.month:02d}"
    except Exception:
        return ""

def format_cop(v):
    try:
        n = float(v)
    except Exception:
        return "$ 0 COP"
    return "$ " + f"{n:,.0f}".replace(",", ".") + " COP"

def gh_get_file(path, ref):
    url = f"{API_BASE}/{path}"
    r = requests.get(url, headers=HEADERS, params={"ref": ref})
    if r.status_code == 200:
        info = r.json()
        content = base64.b64decode(info["content"]).decode("utf-8")
        return content, info["sha"]
    elif r.status_code == 404:
        return None, None
    else:
        st.error(f"Error leyendo GitHub: {r.status_code} - {r.text}")
        return None, None

def gh_put_file(path, content_str, message, branch, sha=None):
    url = f"{API_BASE}/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=HEADERS, data=json.dumps(payload))
    return r.status_code in (200, 201)

def load_data():
    """Carga el CSV (GitHub si está configurado; si no, local)."""
    if USE_GH:
        content, _ = gh_get_file(GH_PATH_REG, GH_BRANCH)
        if content is None:
            return pd.DataFrame(columns=["Fecha","Empleado","Área","Lider","Tipo","Numero_Caso","Estado","Horas_Extra","Mes","Año"])
        return pd.read_csv(StringIO(content))
    else:
        if os.path.exists(LOCAL_CSV):
            return pd.read_csv(LOCAL_CSV, encoding="utf-8-sig")
        return pd.DataFrame(columns=["Fecha","Empleado","Área","Lider","Tipo","Numero_Caso","Estado","Horas_Extra","Mes","Año"])

def append_rows(rows):
    """Agrega filas nuevas y guarda (GitHub o local)."""
    df = load_data()
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    # backfill Mes/Año
    if not df.empty:
        df["Mes"] = df["Mes"] if "Mes" in df.columns else ""
        df["Año"] = df["Año"] if "Año" in df.columns else ""
        df["Mes"] = df.apply(lambda r: month_str(r.get("Fecha","")), axis=1)
        df["Año"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.year

    if USE_GH:
        content, sha = gh_get_file(GH_PATH_REG, GH_BRANCH)
        ok = gh_put_file(GH_PATH_REG, df.to_csv(index=False), f"add registros {date.today()}", GH_BRANCH, sha)
        if not ok:
            st.error("No se pudo guardar en GitHub. Verifica GITHUB_TOKEN / GH_REPO.")
    else:
        df.to_csv(LOCAL_CSV, index=False, encoding="utf-8-sig")

def ensure_tariffs():
    """Crea tarifas locales si no existen (solo informativas para el panel)."""
    tar_path = "tarifas_portal.csv"
    if not os.path.exists(tar_path):
        pd.DataFrame([
            {"Concepto":"Caso_Adicional","Tarifa":10000.0},
            {"Concepto":"Hora_Extra","Tarifa":8000.0},
        ]).to_csv(tar_path, index=False, encoding="utf-8-sig")
    return pd.read_csv(tar_path, encoding="utf-8-sig")

# ===========================
# Sidebar: Admin
# ===========================
st.sidebar.header("🔐 Admin")
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    pin_try = st.sidebar.text_input("PIN de administración", type="password")
    if st.sidebar.button("Entrar"):
        if pin_try == ADMIN_PIN:
            st.session_state.is_admin = True
            st.sidebar.success("Acceso concedido.")
        else:
            st.sidebar.error("PIN incorrecto.")
else:
    st.sidebar.success("Modo administrador activo")

# ===========================
# Tabs
# ===========================
if st.session_state.is_admin:
    tab_reg, tab_admin = st.tabs(["🧾 Registrar (Empleado)", "📊 Panel Admin"])
else:
    tab_reg, = st.tabs(["🧾 Registrar (Empleado)"])

# ===========================
# TAB: Empleado
# ===========================
with tab_reg:
    st.subheader("Ingreso diario (Empleado)")
    st.markdown('<div class="bbva-card">', unsafe_allow_html=True)

    with st.form("form_portal", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            empleado = st.text_input("Nombre del empleado")
        with c2:
            area = st.text_input("Área (opcional)")
            lider = st.selectbox("Líder", ["— seleccionar —"] + LIDERES, index=0)
        with c3:
            horas_extra = st.number_input("Horas extra (del día)", min_value=0, step=1, value=0)

        st.markdown("### Casos de Productividad")
        prod_df = st.data_editor(
            pd.DataFrame(columns=["Numero_Caso","Estado"]),
            column_config={
                "Numero_Caso": st.column_config.TextColumn("Número de caso"),
                "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="prod_editor"
        )

        st.markdown("### Casos de Variable")
        var_df = st.data_editor(
            pd.DataFrame(columns=["Numero_Caso","Estado"]),
            column_config={
                "Numero_Caso": st.column_config.TextColumn("Número de caso (variable)"),
                "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS),
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
                mes = month_str(fecha); anio = fecha.year

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
                    append_rows(rows)
                    st.success(f"Se guardaron {len(rows)} registro(s). ¡Gracias!")

    st.markdown('</div>', unsafe_allow_html=True)

# ===========================
# TAB: Admin
# ===========================
if st.session_state.is_admin:
    with tab_admin:
        st.subheader("Panel administrativo (en vivo)")
        data = load_data()
        if data.empty:
            st.info("Aún no hay registros.")
        else:
            # Filtros
            c1, c2, c3 = st.columns(3)
            with c1:
                f_mes = st.multiselect("Mes", sorted(data["Mes"].dropna().unique().tolist()))
            with c2:
                f_emp = st.multiselect("Empleado", sorted(data["Empleado"].dropna().unique().tolist()))
            with c3:
                f_lid = st.multiselect("Líder", sorted(data["Lider"].dropna().unique().tolist()))
            if f_mes: data = data[data["Mes"].isin(f_mes)]
            if f_emp: data = data[data["Empleado"].isin(f_emp)]
            if f_lid: data = data[data["Lider"].isin(f_lid)]

            # 1) Control por tipo y estado
            st.markdown("### 1) Control por tipo y estado")
            pivot = data.pivot_table(index=["Tipo","Estado"], values="Numero_Caso", aggfunc="count", fill_value=0).reset_index().rename(columns={"Numero_Caso":"Cantidad"})
            st.dataframe(pivot, use_container_width=True)

            # 2) Cumplimiento diario (meta = 12 Productividad)
            st.markdown("### 2) Cumplimiento diario (meta = 12 de Productividad)")
            prod = data[(data["Tipo"]=="Productividad") & (data["Numero_Caso"].astype(str).str.strip()!="")].copy()
            dia = prod.groupby(["Empleado","Fecha"], as_index=False).agg(Total_Casos=("Numero_Caso","count"))
            dia["Cumple"] = dia["Total_Casos"] >= META_DIARIA
            dia["Cumplimiento"] = dia["Cumple"].map(lambda x: "🟢 Cumplió" if x else "🔴 No cumplió")
            st.dataframe(dia.sort_values(["Fecha","Empleado"]), use_container_width=True)

            # 3) Ingresos mensuales (Variables + Horas extra) usando tarifas locales
            st.markdown("### 3) Ingresos mensuales (Variables + Horas extra)")
            tarifas = ensure_tariffs()
            try:
                tarifa_caso = float(tarifas.loc[tarifas["Concepto"]=="Caso_Adicional","Tarifa"].iloc[0])
            except Exception:
                tarifa_caso = 0.0
            try:
                tarifa_hora = float(tarifas.loc[tarifas["Concepto"]=="Hora_Extra","Tarifa"].iloc[0])
            except Exception:
                tarifa_hora = 0.0

            var_cases = data[(data["Tipo"]=="Variable") & (data["Numero_Caso"].astype(str).str.strip()!="")]
            var_mes = var_cases.groupby(["Empleado","Mes"], as_index=False).agg(Casos_Variable=("Numero_Caso","count"))
            horas_mes = data.groupby(["Empleado","Mes"], as_index=False).agg(Horas_Extra=("Horas_Extra","sum"))
            resumen = pd.merge(var_mes, horas_mes, on=["Empleado","Mes"], how="outer").fillna(0)
            resumen["Ingreso_Variable"] = resumen["Casos_Variable"] * tarifa_caso
            resumen["Ingreso_Extras"]   = resumen["Horas_Extra"] * tarifa_hora
            resumen["Total_Mensual"]    = resumen["Ingreso_Variable"] + resumen["Ingreso_Extras"]

            view = resumen.copy()
            for c in ["Ingreso_Variable","Ingreso_Extras","Total_Mensual"]:
                view[c] = view[c].apply(format_cop)
            st.dataframe(view.sort_values(["Mes","Empleado"]), use_container_width=True)

            # Gráfico total mensual
            tot_mes = resumen.groupby("Mes", as_index=False)["Total_Mensual"].sum().sort_values("Mes")
            if not tot_mes.empty:
                fig = plt.figure()
                plt.plot(tot_mes["Mes"], tot_mes["Total_Mensual"])
                plt.title("Total mensual (Variables + Extras)")
                plt.xlabel("Mes"); plt.ylabel("Valor (COP)")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)

            # Descarga registros
            st.download_button(
                "⬇️ Descargar registros (CSV)",
                data=load_data().to_csv(index=False).encode("utf-8-sig"),
                file_name="registro_portal.csv", mime="text/csv"
            )
