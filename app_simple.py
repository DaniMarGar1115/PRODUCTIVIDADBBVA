
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="BBVA | Registro simple mensual", page_icon="📑", layout="wide")

# ---------------- Paths ----------------
DATA_PATH = "registro_simple.csv"
TARIFAS_PATH = "tarifas_simple.csv"
ADMIN_PIN = os.getenv("ADMIN_PIN", "bbva2025")  # Cambiable en Secrets

# ---------------- Helpers ----------------
def ensure_csv(path, columns, default_rows=None):
    if not os.path.exists(path):
        if default_rows is not None:
            pd.DataFrame(default_rows).to_csv(path, index=False, encoding="utf-8-sig")
        else:
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

def format_cop(v):
    try:
        n = float(v)
    except Exception:
        return "0"
    s = f"{n:,.0f}"
    return "$ " + s.replace(",", ".") + " COP"

# ---------------- Initialize storage ----------------
ensure_csv(DATA_PATH, [
    "Fecha","Empleado","Área","Casos","Casos_Adicionales","Horas_Extra","Mes","Año"
])
ensure_csv(TARIFAS_PATH, ["Concepto","Tarifa"], default_rows=[
    {"Concepto":"Caso_Adicional","Tarifa":10000.0},
    {"Concepto":"Hora_Extra","Tarifa":8000.0},
])

df = load_csv(DATA_PATH)
tarifas = load_csv(TARIFAS_PATH)

# Backfill month/year
if not df.empty:
    if "Mes" not in df.columns: df["Mes"] = ""
    if "Año" not in df.columns: df["Año"] = ""
    df["Mes"] = df.apply(lambda r: month_str(r.get("Fecha","")), axis=1)
    df["Año"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.year

# ---------------- Admin access (sidebar) ----------------
st.sidebar.header("🔐 Admin")
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

if st.session_state.is_admin:
    with st.sidebar.expander("💵 Tarifas", expanded=True):
        st.caption("Define los valores que TÚ actualizas:")
        tarifas_edit = st.data_editor(tarifas, use_container_width=True, num_rows="dynamic", key="tarifas_editor")
        if st.button("💾 Guardar tarifas", use_container_width=True):
            save_csv(tarifas_edit, TARIFAS_PATH)
            tarifas = tarifas_edit
            st.success("Tarifas guardadas")

# ---------------- Header ----------------
st.title("📑 Registro diario (empleados) + 💸 Cálculo mensual (automático)")

tab_reg, tab_mes = st.tabs(["➕ Registrar", "📈 Resumen mensual"])

# ---------------- Tab Registrar ----------------
with tab_reg:
    st.subheader("Captura rápida")
    with st.form("form_simple", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            empleado = st.text_input("Empleado")
        with c2:
            area = st.text_input("Área (opcional)")
            casos = st.number_input("Casos realizados (diarios)", min_value=0, step=1, value=0)
        with c3:
            casos_ad = st.number_input("Casos adicionales (variables)", min_value=0, step=1, value=0)
            horas = st.number_input("Horas Extra (diarias)", min_value=0, step=1, value=0)
        submitted = st.form_submit_button("✅ Guardar")
        if submitted:
            if not empleado.strip():
                st.error("Empleado es obligatorio.")
            else:
                new = {
                    "Fecha": fecha.strftime("%Y-%m-%d"),
                    "Empleado": empleado.strip(),
                    "Área": area.strip(),
                    "Casos": int(casos),
                    "Casos_Adicionales": int(casos_ad),
                    "Horas_Extra": int(horas),
                    "Mes": month_str(fecha),
                    "Año": fecha.year,
                }
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                save_csv(df, DATA_PATH)
                st.success("Registro guardado.")

# ---------------- Tab Resumen mensual ----------------
with tab_mes:
    st.subheader("Totales por Empleado x Mes")
    data = load_csv(DATA_PATH)
    if data.empty:
        st.info("Aún no hay registros.")
    else:
        # filters
        c1, c2 = st.columns(2)
        with c1:
            f_mes = st.multiselect("Mes", sorted(data["Mes"].dropna().unique().tolist()))
        with c2:
            f_emp = st.multiselect("Empleado", sorted(data["Empleado"].dropna().unique().tolist()))
        if f_mes: data = data[data["Mes"].isin(f_mes)]
        if f_emp: data = data[data["Empleado"].isin(f_emp)]

        # aggregates
        agg = data.groupby(["Empleado","Mes"], as_index=False).agg({
            "Casos":"sum",
            "Casos_Adicionales":"sum",
            "Horas_Extra":"sum"
        })

        # rates
        try:
            tarifa_caso = float(tarifas.loc[tarifas["Concepto"]=="Caso_Adicional","Tarifa"].iloc[0])
        except Exception:
            tarifa_caso = 0.0
        try:
            tarifa_hora = float(tarifas.loc[tarifas["Concepto"]=="Hora_Extra","Tarifa"].iloc[0])
        except Exception:
            tarifa_hora = 0.0

        agg["Ingreso_Variable"] = agg["Casos_Adicionales"] * tarifa_caso
        agg["Ingreso_Extras"] = agg["Horas_Extra"] * tarifa_hora
        agg["Total_Mensual"] = agg["Ingreso_Variable"] + agg["Ingreso_Extras"]

        view = agg.copy()
        view["Ingreso_Variable"] = view["Ingreso_Variable"].apply(format_cop)
        view["Ingreso_Extras"] = view["Ingreso_Extras"].apply(format_cop)
        view["Total_Mensual"] = view["Total_Mensual"].apply(format_cop)

        st.dataframe(view.sort_values(["Mes","Empleado"]), use_container_width=True)
        st.caption(f"Tarifa por caso adicional: {format_cop(tarifa_caso)} · Tarifa por hora extra: {format_cop(tarifa_hora)}")

        # chart
        tot_mes = agg.groupby("Mes", as_index=False)["Total_Mensual"].sum().sort_values("Mes")
        if not tot_mes.empty:
            fig = plt.figure()
            plt.plot(tot_mes["Mes"], tot_mes["Total_Mensual"])
            plt.title("Total mensual (Variables + Extras)")
            plt.xlabel("Mes")
            plt.ylabel("Valor (COP)")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)

        # download
        st.download_button(
            "⬇️ Descargar resumen mensual (CSV)",
            data=agg.to_csv(index=False).encode("utf-8-sig"),
            file_name="resumen_mensual_simple.csv",
            mime="text/csv"
        )

st.caption("Modo empleado: solo registra cantidades. Modo admin: define tarifas y se calcula el total mensual.")
