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
            d = pd.to_datetime(d).date()
        return f"{d.year:04d}-{d.month:02d}"
    except Exception:
        return ""

def format_cop(v):
    try:
        n = float(v)
    except Exception:
        return "$ 0 COP"
    s = f"{n:,.0f}".replace(",", ".")
    return f"$ {s} COP"

# ============= Inicialización =============
ensure_csv(
    REG_PATH,
    ["Fecha","Empleado","Área","Lider","Tipo","Numero_Caso","Estado","Horas_Extra","Mes","Año"]
)
ensure_csv(
    TAR_PATH,
    ["Concepto","Tarifa"],
    default_rows=[
        {"Concepto":"Caso_Adicional","Tarifa":10000.0},
        {"Concepto":"Hora_Extra","Tarifa":8000.0},
    ]
)
reg = load_csv(REG_PATH)
tar = load_csv(TAR_PATH)

# backfill Mes/Año
if not reg.empty:
    if "Mes" not in reg.columns: reg["Mes"] = ""
    if "Año" not in reg.columns: reg["Año"] = ""
    reg["Mes"] = reg.apply(lambda r: month_str(r.get("Fecha","")), axis=1)
    reg["Año"] = pd.to_datetime(reg["Fecha"], errors="coerce").dt.year
    save_csv(reg, REG_PATH)

# ============= Header =============
st.markdown('<div class="bbva-header">', unsafe_allow_html=True)
if LOGO_URL: st.image(LOGO_URL, width=110)
st.markdown('<div class="bbva-title">BBVA · Portal único <span class="bbva-sub"> Empleado + Admin </span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.write("")

# ============= Barra lateral: acceso Admin y Tarifas =============
st.sidebar.header("🔐 Admin")
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    pin_try = st.sidebar.text_input("PIN de administración", type="password", help="Por defecto: bbva2025 (cámbialo en Secrets)")
    if st.sidebar.button("Entrar"):
        if pin_try == ADMIN_PIN:
            st.session_state.is_admin = True
            st.sidebar.success("Acceso concedido.")
        else:
            st.sidebar.error("PIN incorrecto.")
else:
    st.sidebar.success("Modo administrador activo")

if st.session_state.is_admin:
    with st.sidebar.expander("💵 Tarifas (Admin)", expanded=True):
        st.caption("Define cuánto se paga por **Caso adicional (Variable)** y por **Hora extra**.")
        tar_edit = st.data_editor(tar, use_container_width=True, num_rows="dynamic", key="tar_editor")
        if st.button("💾 Guardar tarifas", use_container_width=True):
            save_csv(tar_edit, TAR_PATH)
            tar = tar_edit
            st.success("Tarifas guardadas.")

# ============= Tabs =============
if st.session_state.is_admin:
    tab_reg, tab_admin = st.tabs(["🧾 Registrar (Empleado)", "📊 Panel Admin"])
else:
    tab_reg, = st.tabs(["🧾 Registrar (Empleado)"])

# ============= TAB: Empleado (formulario) =============
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

                # Horas extra del día (fila separada para acumular)
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

                # Productividad
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

                # Variable
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
                    cur = load_csv(REG_PATH)
                    cur = pd.concat([cur, pd.DataFrame(rows)], ignore_index=True)
                    save_csv(cur, REG_PATH)
                    st.success(f"Se guardaron {len(rows)} registro(s). ¡Gracias!")

    st.markdown('</div>', unsafe_allow_html=True)

# ============= TAB: Panel Admin (en vivo) =============
if st.session_state.is_admin:
    with tab_admin:
        st.subheader("Panel administrativo (en vivo)")

        data = load_csv(REG_PATH)
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

            # 3) Ingresos mensuales (Variables + Horas extra) con tarifas
            st.markdown("### 3) Ingresos mensuales (Variables + Horas extra)")
            try:
                tarifa_caso = float(tar.loc[tar["Concepto"]=="Caso_Adicional","Tarifa"].iloc[0])
            except Exception:
                tarifa_caso = 0.0
            try:
                tarifa_hora = float(tar.loc[tar["Concepto"]=="Hora_Extra","Tarifa"].iloc[0])
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

            # Descargas
            st.download_button(
                "⬇️ Descargar registros (CSV)",
                data=load_csv(REG_PATH).to_csv(index=False).encode("utf-8-sig"),
                file_name="registro_portal.csv", mime="text/csv"
            )
