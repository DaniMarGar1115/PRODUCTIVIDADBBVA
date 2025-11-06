
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="BBVA | Dashboard empresarial", page_icon="🏢", layout="wide")

# ---------------- Paths & constants ----------------
DATA_PATH = "registro_empresarial.csv"
TARIFAS_PATH = "tarifas_empresarial.csv"
ADMIN_PIN = os.getenv("ADMIN_PIN", "bbva2025")
META_CASOS = 12

LIDERES = ["Alejandra Puentes", "Carlos Sierra", "Edisson Ramirez", "Gabrielle Monroy"]
ESTADOS = ["Finalizado", "Defensoria", "Tutela"]

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

def parse_case_numbers(text):
    if not text:
        return []
    # Accept separators: comma, semicolon, newline, space
    for sep in [",", ";", "\n", "\r", "\t"]:
        text = text.replace(sep, " ")
    parts = [p.strip() for p in text.split(" ") if p.strip()]
    # Remove duplicates while preserving order
    seen = set()
    uniq = []
    for p in parts:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

# ---------------- Initialize storage ----------------
ensure_csv(
    DATA_PATH,
    [
        "Fecha","Empleado","Área","Lider","Numero_Caso","Estado","Casos_Adicionales","Horas_Extra","Mes","Año"
    ]
)
ensure_csv(
    TARIFAS_PATH,
    ["Concepto","Tarifa"],
    default_rows=[
        {"Concepto":"Caso_Adicional","Tarifa":10000.0},
        {"Concepto":"Hora_Extra","Tarifa":8000.0},
    ]
)

df_all = load_csv(DATA_PATH)
tarifas = load_csv(TARIFAS_PATH)

# backfill Mes/Año
if not df_all.empty:
    if "Mes" not in df_all.columns: df_all["Mes"] = ""
    if "Año" not in df_all.columns: df_all["Año"] = ""
    df_all["Mes"] = df_all.apply(lambda r: month_str(r.get("Fecha","")), axis=1)
    df_all["Año"] = pd.to_datetime(df_all["Fecha"], errors="coerce").dt.year

# ---------------- Admin access ----------------
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
        st.caption("Define los valores por caso adicional y hora extra.")
        tarifas_edit = st.data_editor(tarifas, use_container_width=True, num_rows="dynamic", key="tarifas_editor")
        if st.button("💾 Guardar tarifas", use_container_width=True):
            save_csv(tarifas_edit, TARIFAS_PATH)
            tarifas = tarifas_edit
            st.success("Tarifas guardadas")

# ---------------- Header ----------------
st.title("🏢 Dashboard empresarial — Registro de casos y cálculo mensual")

tab_reg, tab_mes = st.tabs(["➕ Registrar casos", "📈 Resumen mensual"])

# ---------------- Tab Registrar ----------------
with tab_reg:
    st.subheader("Ingreso por parte del empleado")
    with st.form("form_empresarial", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            empleado = st.text_input("Nombre del empleado")  # Usar nombre en vez de número
        with c2:
            area = st.text_input("Área (opcional)")
            lider = st.selectbox("Líder", LIDERES, index=0)
        with c3:
            estado = st.selectbox("Estado del caso", ESTADOS, index=0)
            horas = st.number_input("Horas Extra (diarias)", min_value=0, step=1, value=0)

        casos_txt = st.text_area("Números de caso (puedes pegar varios, separados por coma, espacio o salto de línea)")
        casos_adicionales = st.number_input("Casos adicionales (variables) — cantidad", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("✅ Guardar")
        if submitted:
            if not empleado.strip():
                st.error("El nombre del empleado es obligatorio.")
            else:
                case_list = parse_case_numbers(casos_txt)
                if not case_list and casos_adicionales == 0 and horas == 0:
                    st.error("Agrega al menos un número de caso, o casos adicionales, o horas extra.")
                else:
                    new_rows = []
                    if case_list:
                        for numero in case_list:
                            new_rows.append({
                                "Fecha": fecha.strftime("%Y-%m-%d"),
                                "Empleado": empleado.strip(),
                                "Área": area.strip(),
                                "Lider": lider,
                                "Numero_Caso": str(numero),
                                "Estado": estado,
                                "Casos_Adicionales": 0,
                                "Horas_Extra": int(horas),
                                "Mes": month_str(fecha),
                                "Año": fecha.year
                            })
                    else:
                        # Si no hay número de caso, guardamos una fila 'vacía' para trackear horas/variables
                        new_rows.append({
                            "Fecha": fecha.strftime("%Y-%m-%d"),
                            "Empleado": empleado.strip(),
                            "Área": area.strip(),
                            "Lider": lider,
                            "Numero_Caso": "",
                            "Estado": estado,
                            "Casos_Adicionales": 0,
                            "Horas_Extra": int(horas),
                            "Mes": month_str(fecha),
                            "Año": fecha.year
                        })

                    df_local = load_csv(DATA_PATH)
                    df_local = pd.concat([df_local, pd.DataFrame(new_rows)], ignore_index=True)
                    # Guardar una fila adicional para reflejar los Casos_Adicionales (variables) del día
                    if casos_adicionales > 0:
                        df_local = pd.concat([df_local, pd.DataFrame([{
                            "Fecha": fecha.strftime("%Y-%m-%d"),
                            "Empleado": empleado.strip(),
                            "Área": area.strip(),
                            "Lider": lider,
                            "Numero_Caso": "",
                            "Estado": estado,
                            "Casos_Adicionales": int(casos_adicionales),
                            "Horas_Extra": 0,
                            "Mes": month_str(fecha),
                            "Año": fecha.year
                        }])], ignore_index=True)

                    save_csv(df_local, DATA_PATH)
                    st.success(f"Guardado: {len(new_rows)} caso(s) + variables/horas correspondientes.")

# ---------------- Tab Resumen mensual ----------------
with tab_mes:
    st.subheader("Totales por Empleado x Mes")
    data = load_csv(DATA_PATH)
    if data.empty:
        st.info("Aún no hay registros.")
    else:
        # filters
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

        # aggregate
        # Total de casos = conteo de filas con Numero_Caso no vacío
        data["Tiene_Caso"] = data["Numero_Caso"].astype(str).str.strip().ne("")
        agg = data.groupby(["Empleado","Mes"], as_index=False).agg({
            "Tiene_Caso":"sum",
            "Casos_Adicionales":"sum",
            "Horas_Extra":"sum"
        }).rename(columns={"Tiene_Caso":"Total_Casos"})

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

        # cumplimiento meta = 12 casos por mes
        agg["Meta"] = META_CASOS
        agg["Cumple"] = agg["Total_Casos"] >= META_CASOS
        agg["Cumplimiento"] = agg["Cumple"].map(lambda x: "🟢 Cumplió" if x else "🔴 No cumplió")

        view = agg.copy()
        for col in ["Ingreso_Variable","Ingreso_Extras","Total_Mensual"]:
            view[col] = view[col].apply(format_cop)

        view = view[["Empleado","Mes","Total_Casos","Casos_Adicionales","Horas_Extra","Ingreso_Variable","Ingreso_Extras","Total_Mensual","Meta","Cumplimiento"]]
        st.dataframe(view.sort_values(["Mes","Empleado"]), use_container_width=True)

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
            file_name="resumen_mensual_empresarial.csv",
            mime="text/csv"
        )

st.caption("Empleados: registran nombre, líder, múltiples números de caso, estado y horas extra. Admin: fija tarifas. Cumplimiento de meta=12 casos/mes.")
