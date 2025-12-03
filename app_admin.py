import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(page_title="Portal de Productividad", layout="wide")

# Estilos tipo BBVA
BBVA_PRIMARY = "#0039A6"   # Azul BBVA
BBVA_DARK = "#00234F"
BBVA_LIGHT = "#E9EDF5"

BBVA_PRIMARY = "#0039A6"      # Azul BBVA
BBVA_PRIMARY_DARK = "#002B76" # Azul BBVA más oscuro
BBVA_WHITE = "#FFFFFF"

st.markdown(
    f"""
    <style>

    /* Fondo general */
    .stApp {{
        background-color: {BBVA_WHITE};
        font-family: "Segoe UI", "Roboto", sans-serif;
        color: #000000 !important;
    }}

    /* Contenedor principal */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
        background-color: {BBVA_WHITE};
        max-width: 1200px;
    }}

    /* Encabezado con logo */
    .bbva-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 10px 0 20px 0;
        border-bottom: 2px solid {BBVA_PRIMARY};
        margin-bottom: 20px;
    }}

    .bbva-title {{
        font-size: 32px;
        font-weight: 700;
        color: {BBVA_PRIMARY};
        margin: 0;
    }}

    .bbva-subtitle {{
        font-size: 16px;
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

    /* Select, input, tabla */
    .stSelectbox div[data-baseweb="select"] {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    .stTextInput input {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    .stNumberInput input {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    .stDateInput input {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    /* Estilos para la tabla */
    .stDataFrame, .stDataEditor {{
        color: #000000 !important;
    }}

    /* Barra lateral */
    .css-1d391kg, .css-1uixxvy, .css-1y4p8pa {{
        background-color: {BBVA_WHITE} !important;
        color: #000000 !important;
        border-right: 2px solid {BBVA_PRIMARY};
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


    /* Fondo de los contenedores principales */
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1200px;
        margin: 0 auto;
        background-color: #FFFFFFEE;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }}

    .bbva-header {{
        display:flex;
        align-items:center;
        gap:16px;
        padding:10px 0 20px 0;
    }}
    .bbva-title {{
        font-size:28px;
        font-weight:700;
        color:{BBVA_PRIMARY};
        margin:0;
    }}
    .bbva-subtitle {{
        font-size:14px;
        color:#444444;
        margin:0;
    }}
    .metric-card {{
        background:white;
        padding:16px;
        border-radius:10px;
        border:1px solid #D4DBE8;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }}

    /* Botón principal rojo → azul BBVA */
    button[kind="primary"] {{
        background-color: {BBVA_PRIMARY} !important;
        color: white !important;
        border-radius: 999px !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    button[kind="primary"]:hover {{
        background-color: {BBVA_DARK} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Encabezado con logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_bbva.png"):
        st.image("logo_bbva.png", use_container_width=False)
with col_title:
    st.markdown(
        """
        <div class="bbva-header">
            <div>
                <p class="bbva-title">Panel de Productividad de la Empresa</p>
                <p class="bbva-subtitle">Control de casos, metas diarias y análisis mensual</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

CSV_PATH = "registro_empresarial2.csv"

# =========================
# CARGA DE DATOS PERSISTENTES
# =========================
if os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    except Exception:
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

COLUMNAS = [
    "ID",
    "Empleado",
    "Lider",
    "Numero_caso",
    "Fecha",
    "Tipo_caso",   # Productividad / Adicional / Meta sábado
    "Categoria",   # Finalizado / Tutela / Defensoría
]

if df.empty:
    df = pd.DataFrame(columns=COLUMNAS)
else:
    for col in COLUMNAS:
        if col not in df.columns:
            if col == "ID":
                df[col] = range(1, len(df) + 1)
            else:
                df[col] = None
    df = df[COLUMNAS]

if df["ID"].isnull().any():
    df["ID"] = range(1, len(df) + 1)
df["ID"] = df["ID"].astype(int)

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

if "meta_dia" not in st.session_state:
    st.session_state["meta_dia"] = 20
if "meta_mes" not in st.session_state:
    st.session_state["meta_mes"] = 300

if "valor_prod" not in st.session_state:
    st.session_state["valor_prod"] = 3500.0
if "valor_adic" not in st.session_state:
    st.session_state["valor_adic"] = 4000.0
if "valor_sabado" not in st.session_state:
    st.session_state["valor_sabado"] = 5000.0

salario_base_mensual = st.sidebar.number_input(
    "Salario base mensual ($)", min_value=0.0, value=1_500_000.0, step=100_000.0
)

# MODO LÍDER: puede modificar metas y tarifas con clave
if perfil == "Líder":
    clave = st.sidebar.text_input("Contraseña líderes", type="password")
    if clave != "BBVA2025":
        st.sidebar.warning("Contraseña incorrecta. Solo lectura.")
    else:
        st.sidebar.success("Acceso de líder habilitado.")
        st.session_state["meta_dia"] = st.sidebar.number_input(
            "Meta de casos por día", min_value=0, value=st.session_state["meta_dia"], step=1
        )
        st.session_state["meta_mes"] = st.sidebar.number_input(
            "Meta de casos por mes", min_value=0, value=st.session_state["meta_mes"], step=5
        )
        st.sidebar.markdown("---")
        st.sidebar.markdown("Tarifas por tipo de caso:")
        st.session_state["valor_prod"] = st.sidebar.number_input(
            "Valor por caso Productividad ($)",
            min_value=0.0,
            value=st.session_state["valor_prod"],
            step=500.0,
        )
        st.session_state["valor_adic"] = st.sidebar.number_input(
            "Valor por caso Adicional ($)",
            min_value=0.0,
            value=st.session_state["valor_adic"],
            step=500.0,
        )
        st.session_state["valor_sabado"] = st.sidebar.number_input(
            "Valor por caso Meta sábado ($)",
            min_value=0.0,
            value=st.session_state["valor_sabado"],
            step=500.0,
        )

meta_dia = st.session_state["meta_dia"]
meta_mes = st.session_state["meta_mes"]
valor_prod = st.session_state["valor_prod"]
valor_adic = st.session_state["valor_adic"]
valor_sabado = st.session_state["valor_sabado"]

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
    """Devuelve True si el analista ha cumplido la meta TODOS los días del mes."""
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
    st.write("Complete la tabla con los casos del día y guarde todos los registros. Puede copiar/pegar varias filas desde Excel.")

    col_emp1, col_emp2 = st.columns(2)
    with col_emp1:
        nombre_empleado = st.text_input("Nombre del empleado")
    with col_emp2:
        lider = st.selectbox("Líder a cargo", LIDERES)

    hoy = date.today()

    plantilla = pd.DataFrame(
        [
            {
                "Numero_caso": "",
                "Fecha": hoy,
                "Tipo_caso": "Productividad",
                "Categoria": "Finalizado",
            }
        ]
    )

    edited = st.data_editor(
        plantilla,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Numero_caso": st.column_config.TextColumn("Número de caso"),
            "Fecha": st.column_config.DateColumn("Fecha"),
            "Tipo_caso": st.column_config.SelectboxColumn("Tipo de caso", options=TIPOS_CASO),
            "Categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS),
        },
        hide_index=True,
    )

    if st.button("Guardar todos los casos", type="primary"):
        if nombre_empleado.strip() == "":
            st.warning("Por favor ingrese el nombre del empleado.")
        else:
            edited["Numero_caso"] = edited["Numero_caso"].astype(str).str.strip()
            edited = edited[edited["Numero_caso"] != ""]
            edited = edited.dropna(subset=["Fecha", "Tipo_caso", "Categoria"])

            if edited.empty:
                st.warning("No hay casos válidos para guardar.")
            else:
                edited["Fecha"] = pd.to_datetime(edited["Fecha"]).dt.date
                edited["Empleado"] = nombre_empleado
                edited["Lider"] = lider

                if df.empty:
                    next_id = 1
                else:
                    next_id = df["ID"].max() + 1
                edited["ID"] = range(next_id, next_id + len(edited))

                edited = edited[["ID", "Empleado", "Lider", "Numero_caso", "Fecha", "Tipo_caso", "Categoria"]]

                st.session_state["registros"] = pd.concat(
                    [st.session_state["registros"], edited], ignore_index=True
                )
                df = st.session_state["registros"]
                df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                st.success("Registros guardados correctamente.")

    # ---------- RESUMEN DEL EMPLEADO ----------
    df = st.session_state["registros"]

    if df.empty:
        st.info("Aún no hay registros para mostrar.")
    else:
        st.subheader("Resumen del empleado")

        empleados_disponibles = ["Seleccione..."] + sorted(df["Empleado"].unique().tolist())
        empleado_sel = st.selectbox("Seleccione su nombre", empleados_disponibles)

        if empleado_sel != "Seleccione...":
            hoy = datetime.today()
            df_emp = df[df["Empleado"] == empleado_sel]

            df_emp_mes = df_emp[
                (pd.to_datetime(df_emp["Fecha"]).dt.month == hoy.month)
                & (pd.to_datetime(df_emp["Fecha"]).dt.year == hoy.year)
            ]

            if df_emp_mes.empty:
                st.info("No hay registros para este mes.")
            else:
                df_emp_hoy = df_emp_mes[pd.to_datetime(df_emp_mes["Fecha"]).dt.date == hoy.date()]

                casos_dia = len(df_emp_hoy)
                casos_mes = len(df_emp_mes)

                df_emp_mes["Valor_caso"] = df_emp_mes.apply(valor_fila, axis=1)
                dinero_casos_mes = df_emp_mes["Valor_caso"].sum()
                dinero_total_mes = salario_base_mensual + dinero_casos_mes

                racha_completa = calcular_racha_meta(df_emp_mes, meta_dia)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Casos hoy", int(casos_dia))
                    st.markdown("</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Casos en el mes", int(casos_mes))
                    st.markdown("</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Meta diaria", f"{meta_dia} casos", "Cumple" if casos_dia >= meta_dia else "No")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric(
                        "Racha perfecta del mes",
                        "Sí" if racha_completa else "No",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("#### Dinero acumulado en el mes")
                col5, col6 = st.columns(2)
                with col5:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Valor por casos (mes)", f"${dinero_casos_mes:,.0f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                with col6:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Total estimado mes", f"${dinero_total_mes:,.0f}")
                    st.markdown("</div>", unsafe_allow_html=True)

                # Gráfica por día + categoría
                st.markdown("#### Gráfica de productividad por día y categoría")
                df_graf = (
                    df_emp_mes.groupby(
                        [pd.to_datetime(df_emp_mes["Fecha"]).dt.date, "Categoria"]
                    )["ID"]
                    .count()
                    .reset_index()
                    .rename(columns={"Fecha": "Día", "ID": "Total_casos"})
                )
                df_pivot = df_graf.pivot(index="Día", columns="Categoria", values="Total_casos").fillna(0)
                st.bar_chart(df_pivot)

                st.markdown("#### Casos del mes (puede marcar para eliminar)")
                df_emp_mes_view = df_emp_mes.copy()
                df_emp_mes_view["Eliminar"] = False

                edited_view = st.data_editor(
                    df_emp_mes_view,
                    key="editor_empleado",
                    column_config={
                        "Eliminar": st.column_config.CheckboxColumn("Eliminar"),
                    },
                    use_container_width=True,
                )

                if st.button("Eliminar casos seleccionados"):
                    ids_a_borrar = edited_view.loc[edited_view["Eliminar"], "ID"].tolist()
                    if not ids_a_borrar:
                        st.warning("No seleccionó ningún caso para eliminar.")
                    else:
                        df = st.session_state["registros"]
                        df = df[~df["ID"].isin(ids_a_borrar)]
                        st.session_state["registros"] = df
                        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                        st.success(f"Se eliminaron {len(ids_a_borrar)} caso(s). Recargue la página para ver cambios.")

# =========================
# PERFIL ADMINISTRADOR / LÍDER
# =========================
if perfil in ["Administrador", "Líder"]:
    st.subheader("Vista global de productividad")

    df = st.session_state["registros"]

    if df.empty:
        st.info("Aún no hay registros para mostrar.")
    else:
        hoy = datetime.today()
        df_mes = df[
            (pd.to_datetime(df["Fecha"]).dt.month == hoy.month)
            & (pd.to_datetime(df["Fecha"]).dt.year == hoy.year)
        ]

        if df_mes.empty:
            st.info("No hay registros para el mes actual.")
        else:
            df_mes["Valor_caso"] = df_mes.apply(valor_fila, axis=1)

            # Resumen por empleado
            resumen_emp = df_mes.groupby(["Empleado", "Lider"]).agg(
                Casos_mes=("ID", "count"),
                Valor_casos_mes=("Valor_caso", "sum"),
            ).reset_index()

            resumen_emp["Total_mes_estimado"] = salario_base_mensual + resumen_emp["Valor_casos_mes"]
            resumen_emp["Cumple_meta_mes"] = resumen_emp["Casos_mes"] >= meta_mes

            # Cálculo de racha perfecta por analista
            racha_flags = []
            for emp in resumen_emp["Empleado"]:
                df_emp = df_mes[df_mes["Empleado"] == emp]
                racha_flags.append(calcular_racha_meta(df_emp, meta_dia))
            resumen_emp["Racha_perfecta"] = racha_flags

            st.markdown("#### Resumen por empleado (mes actual)")
            st.dataframe(resumen_emp, use_container_width=True)

            # Gráfica global por día y categoría
            st.markdown("#### Gráfica global por día y categoría")
            df_graf = (
                df_mes.groupby(
                    [pd.to_datetime(df_mes["Fecha"]).dt.date, "Categoria"]
                )["ID"]
                .count()
                .reset_index()
                .rename(columns={"Fecha": "Día", "ID": "Total_casos"})
            )
            df_pivot = df_graf.pivot(index="Día", columns="Categoria", values="Total_casos").fillna(0)
            st.bar_chart(df_pivot)

            # Ranking de mejores analistas (por casos y por valor)
            st.markdown("#### Mejores analistas del mes")

            ranking_casos = resumen_emp.sort_values("Casos_mes", ascending=False).head(5)
            ranking_valor = resumen_emp.sort_values("Valor_casos_mes", ascending=False).head(5)

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**Top 5 por número de casos**")
                st.dataframe(
                    ranking_casos[["Empleado", "Lider", "Casos_mes", "Cumple_meta_mes", "Racha_perfecta"]],
                    use_container_width=True,
                )
            with col_r2:
                st.markdown("**Top 5 por valor generado**")
                st.dataframe(
                    ranking_valor[["Empleado", "Lider", "Valor_casos_mes", "Total_mes_estimado"]],
                    use_container_width=True,
                )
