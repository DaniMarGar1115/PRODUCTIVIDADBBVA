
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Registro & Variables", page_icon="🧾", layout="wide")

# ---------------- Config ----------------
REGISTRO_PATH = "registro.csv"
EMPLEADOS_PATH = "empleados.csv"
TARIFAS_PATH = "tarifas.csv"

TIPOS = ["Productividad", "Variable", "HorasExtra", "Bonificación"]

# ---------------- Helpers ----------------
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

# ---------------- Init storage ----------------
ensure_csv(REGISTRO_PATH, [
    "Fecha (YYYY-MM-DD)","Empleado","Área","Tipo_Caso","Variable_Tipo","Cantidad",
    "Descripción","Horas_Extra","Monto","Mes","Año","Observaciones"
])
ensure_csv(EMPLEADOS_PATH, [
    "Empleado","ID_Empleado","Área","Cargo",
    "Meta_Mensual_Casos_Productividad","Meta_Mensual_Variables_(Monto)","Meta_Mensual_Horas_Extra_(max)","Email"
])
ensure_csv(TARIFAS_PATH, [
    "Tipo_Caso","Concepto","Tarifa"
])

registro = load_csv(REGISTRO_PATH)
empleados = load_csv(EMPLEADOS_PATH)
tarifas = load_csv(TARIFAS_PATH)

# backfill Mes/Año
if not registro.empty:
    if "Mes" not in registro.columns:
        registro["Mes"] = ""
    if "Año" not in registro.columns:
        registro["Año"] = ""
    registro["Mes"] = registro.apply(lambda r: month_str(r.get("Fecha (YYYY-MM-DD)","")), axis=1)
    registro["Año"] = pd.to_datetime(registro["Fecha (YYYY-MM-DD)"], errors="coerce").dt.year

# ---------------- Sidebar (admin) ----------------
st.sidebar.header("⚙️ Administración")

with st.sidebar.expander("✏️ Tarifas (pago por caso / hora extra)", expanded=True):
    st.caption("Define cuánto se paga por cada tipo de caso de **Variable** y la tarifa de **Hora Extra**.")
    if tarifas.empty:
        tarifas = pd.DataFrame([
            {"Tipo_Caso":"Variable","Concepto":"Caso A","Tarifa":10000.0},
            {"Tipo_Caso":"Variable","Concepto":"Caso B","Tarifa":15000.0},
            {"Tipo_Caso":"HorasExtra","Concepto":"Hora Extra","Tarifa":8000.0},
        ])
    tarifas_edit = st.data_editor(tarifas, use_container_width=True, num_rows="dynamic", key="tarifas_editor")
    if st.button("💾 Guardar tarifas", use_container_width=True):
        save_csv(tarifas_edit, TARIFAS_PATH)
        st.success("Tarifas guardadas.")

with st.sidebar.expander("👥 Metas (opcional)", expanded=False):
    emp_edit = st.data_editor(empleados, use_container_width=True, num_rows="dynamic", key="empleados_editor")
    if st.button("💾 Guardar metas", use_container_width=True, key="save_metas"):
        save_csv(emp_edit, EMPLEADOS_PATH)
        st.success("Metas guardadas.")

st.sidebar.divider()
st.sidebar.caption("Archivos locales:")
st.sidebar.code(f"{REGISTRO_PATH}\n{TARIFAS_PATH}\n{EMPLEADOS_PATH}")

# ---------------- Main ----------------
st.title("🧾 Registro diario + 💸 Variables & Extras (mensual)")

tab_reg, tab_dash, tab_data = st.tabs(["➕ Registrar", "📈 Ingresos mensuales", "📜 Datos"])

# ---------- Tab Registrar ----------
with tab_reg:
    st.subheader("Captura diaria (simple y rápida)")
    with st.form("form_registro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            empleado = st.text_input("Empleado")
            area = st.text_input("Área")
        with c2:
            tipo = st.selectbox("Tipo de Caso", TIPOS, index=0)
            variable_tipo_choices = tarifas[tarifas["Tipo_Caso"]=="Variable"]["Concepto"].dropna().unique().tolist()
            variable_tipo = st.selectbox("Tipo de Variable (si aplica)", [""] + variable_tipo_choices)
            cantidad = st.number_input("Cantidad (para Variable)", min_value=0, step=1, value=0)
        with c3:
            horas_extra = st.number_input("Horas Extra", min_value=0, step=1, value=0)
            monto_manual = st.number_input("Monto manual (opcional)", min_value=0.0, step=100.0, value=0.0, format="%.2f")
        desc = st.text_area("Descripción (opcional)", placeholder="Detalle breve...")
        submitted = st.form_submit_button("✅ Guardar")
        if submitted:
            new = {
                "Fecha (YYYY-MM-DD)": fecha.strftime("%Y-%m-%d"),
                "Empleado": empleado.strip(),
                "Área": area.strip(),
                "Tipo_Caso": tipo,
                "Variable_Tipo": variable_tipo.strip(),
                "Cantidad": int(cantidad),
                "Descripción": desc.strip(),
                "Horas_Extra": int(horas_extra),
                "Monto": float(monto_manual),  # libre por si quieres registrar montos directos
                "Mes": month_str(fecha),
                "Año": fecha.year,
                "Observaciones": "",
            }
            registro = pd.concat([registro, pd.DataFrame([new])], ignore_index=True)
            save_csv(registro, REGISTRO_PATH)
            st.success("Registro guardado.")

# ---------- Tab Ingresos mensuales ----------
with tab_dash:
    st.subheader("Cálculo mensual de variables y horas extra")

    if registro.empty:
        st.info("Aún no hay registros.")
    else:
        # filtros
        c1, c2, c3 = st.columns(3)
        with c1:
            f_mes = st.multiselect("Mes", sorted(registro["Mes"].dropna().unique().tolist()))
        with c2:
            f_area = st.multiselect("Área", sorted(registro["Área"].dropna().unique().tolist()))
        with c3:
            f_emp = st.multiselect("Empleado", sorted(registro["Empleado"].dropna().unique().tolist()))

        df = registro.copy()
        if f_mes: df = df[df["Mes"].isin(f_mes)]
        if f_area: df = df[df["Área"].isin(f_area)]
        if f_emp: df = df[df["Empleado"].isin(f_emp)]

        # ----- Calcular ingresos por Variable -----
        # Merge con tarifas por (Tipo_Caso='Variable', Concepto=Variable_Tipo)
        vars_df = df[df["Tipo_Caso"]=="Variable"].copy()
        if not vars_df.empty:
            tarifas_var = tarifas[tarifas["Tipo_Caso"]=="Variable"][["Concepto","Tarifa"]].rename(columns={"Tarifa":"Tarifa_Variable"})
            vars_df = vars_df.merge(tarifas_var, left_on="Variable_Tipo", right_on="Concepto", how="left")
            vars_df["Tarifa_Variable"] = pd.to_numeric(vars_df["Tarifa_Variable"], errors="coerce").fillna(0.0)
            vars_df["Cantidad"] = pd.to_numeric(vars_df["Cantidad"], errors="coerce").fillna(0).astype(int)
            vars_df["Ingreso_Variable"] = vars_df["Cantidad"] * vars_df["Tarifa_Variable"]
        else:
            vars_df = pd.DataFrame(columns=df.columns.tolist() + ["Tarifa_Variable","Ingreso_Variable"])

        # ----- Calcular ingresos por Horas Extra -----
        he_rate = tarifas.loc[tarifas["Tipo_Caso"]=="HorasExtra", "Tarifa"]
        tarifa_hora = float(he_rate.iloc[0]) if not he_rate.empty else 0.0
        extras_df = df.copy()
        extras_df["Horas_Extra"] = pd.to_numeric(extras_df["Horas_Extra"], errors="coerce").fillna(0).astype(int)
        extras_df["Ingreso_Extras"] = extras_df["Horas_Extra"] * tarifa_hora

        # ----- Agregar por empleado/mes -----
        var_mes = vars_df.groupby(["Empleado","Mes"], as_index=False)["Ingreso_Variable"].sum()
        ext_mes = extras_df.groupby(["Empleado","Mes"], as_index=False)["Ingreso_Extras"].sum()

        resumen = pd.merge(var_mes, ext_mes, on=["Empleado","Mes"], how="outer").fillna(0)
        if not resumen.empty:
            resumen["Total_Mensual"] = resumen["Ingreso_Variable"] + resumen["Ingreso_Extras"]
            st.markdown("**Ingresos por Empleado x Mes**")
            st.dataframe(resumen.sort_values(["Mes","Empleado"]), use_container_width=True)

            # gráfico simple por mes (Total)
            tot_mes = resumen.groupby("Mes", as_index=False)["Total_Mensual"].sum().sort_values("Mes")
            if not tot_mes.empty:
                fig = plt.figure()
                plt.plot(tot_mes["Mes"], tot_mes["Total_Mensual"])
                plt.title("Total mensual (Variables + Extras)")
                plt.xlabel("Mes")
                plt.ylabel("Valor")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)
        else:
            st.info("No hay datos para calcular ingresos.")

        st.caption(f"Tarifa hora extra actual: ${tarifa_hora:,.2f}")

# ---------- Tab Datos ----------
with tab_data:
    st.subheader("Registros")
    st.dataframe(registro.sort_values("Fecha (YYYY-MM-DD)", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar registros (CSV)", data=registro.to_csv(index=False).encode("utf-8-sig"), file_name="registro.csv", mime="text/csv")

    st.subheader("Tarifas")
    st.dataframe(tarifas, use_container_width=True)
    st.download_button("⬇️ Descargar tarifas (CSV)", data=tarifas.to_csv(index=False).encode("utf-8-sig"), file_name="tarifas.csv", mime="text/csv")
