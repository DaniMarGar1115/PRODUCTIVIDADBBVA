import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(
    page_title="PRODUCTIVIDAD Y EXTRAS BBVA PQRS",
    layout="wide"
)

# Paleta de colores BBVA
BBVA_PRIMARY = "#0039A6"       # Azul BBVA
BBVA_PRIMARY_DARK = "#002B76"  # Azul BBVA más oscuro
BBVA_WHITE = "#FFFFFF"

# Rutas de archivos
CSV_PATH = "registro_empresarial2.csv"
SETTINGS_PATH = "config_productividad.csv"

# =========================
# ESTILOS GLOBALES
# =========================
st.markdown(
    f"""
    <style>
    /* Fondo general blanco */
    .stApp {{
        background-color: {BBVA_WHITE};
        font-family: "Segoe UI", "Roboto", sans-serif;
        color: #000000 !important;
    }}

    /* Contenedor principal */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
        margin: 0 auto;
    }}

    /* Encabezado con logo y línea azul */
    .bbva-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 10px 0 20px 0;
        border-bottom: 3px solid {BBVA_PRIMARY};
        margin-bottom: 24px;
    }}

    .bbva-title {{
        font-size: 30px;
        font-weight: 700;
        color: {BBVA_PRIMARY};
        margin: 0;
    }}

    .bbva-subtitle {{
        font-size: 15px;
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

    /* Inputs y selects blancos, texto negro */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input {{
        background-color: {BBVA_WHITE};
        color: #000000;
    }}

    .stDataFrame, .stDataEditor {{
        color: #000000 !important;
    }}

    /* Barra lateral blanca con borde azul */
    section[data-testid="stSidebar"] {{
        background-color: {BBVA_WHITE} !important;
        border-right: 2px solid {BBVA_PRIMARY};
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# ENCABEZADO CON LOGO
# =========================
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_bbva.png"):
        st.image("logo_bbva.png", use_container_width=False)
with col_title:
    st.markdown(
        """
        <div class="bbva-header">
            <div>
                <p class="bbva-title">PRODUCTIVIDAD Y EXTRAS BBVA PQRS</p>
                <p class="bbva-subtitle">Control de casos, metas diarias y análisis mensual por analista</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================
# FUNCIONES DE CONFIGURACIÓN (PERSISTENCIA)
# =========================
def cargar_config():
    """Lee la configuración desde CSV o crea una por defecto."""
    if os.path.exists(SETTINGS_PATH):
        try:
            cfg = pd.read_csv(SETTINGS_PATH, encoding="utf-8-sig")
            row = cfg.iloc[0].to_dict()
        except Exception:
            row = {}
    else:
        row = {}

    config = {
        "meta_dia": int(row.get("meta_dia", 20)),
        "meta_mes": int(row.get("meta_mes", 300)),
        "valor_prod": float(row.get("valor_prod", 3500.0)),
        "valor_adic": float(row.get("valor_adic", 4000.0)),
        "valor_sabado": float(row.get("valor_sabado", 5000.0)),
        "salario_base_mensual": float(row.get("salario_base_mensual", 1_500_000.0)),
    }

    guardar_config(config)
    return config


def guardar_config(config: dict):
    """Guarda la configuración actual en CSV."""
    df_cfg = pd.DataFrame([config])
    df_cfg.to_csv(SETTINGS_PATH, index=False, encoding="utf-8-sig")


# Cargamos configuración inicial
config = cargar_config()
meta_dia = config["meta_dia"]
meta_mes = config["meta_mes"]
valor_prod = config["valor_prod"]
valor_adic = config["valor_adic"]
valor_sabado = config["valor_sabado"]
salario_base_mensual = config["salario_base_mensual"]

# =========================
# CARGA DE DATOS PERSISTENTES (CASOS)
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
    "Duplicado",   # True/False
]

if df.empty:
    df = pd.DataFrame(columns=COLUMNAS)
else:
    for col in COLUMNAS:
        if col not in df.columns:
            if col == "ID":
                df[col] = range(1, len(df) + 1)
            elif col == "Duplicado":
                df[col] = False
            else:
                df[col] = None
    df = df[COLUMNAS]

if df["ID"].isnull().any():
    df["ID"] = range(1, len(df) + 1)
df["ID"] = df["ID"].astype(int)

# Recalcular duplicados globalmente (Empleado + Numero_caso)
if "Numero_caso" in df.columns and "Empleado" in df.columns:
    df["Duplicado"] = df.duplicated(
        subset=["Empleado", "Numero_caso"], keep=False
    )
else:
    df["Duplicado"] = False

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

# Salario base se puede ajustar siempre
salario_base_mensual = st.sidebar.number_input(
    "Salario base mensual ($)",
    min_value=0.0,
    value=float(salario_base_mensual),
    step=100_000.0,
)

# MODO LÍDER: puede cambiar metas y valores con clave (y quedan guardados)
if perfil == "Líder":
    clave = st.sidebar.text_input("Contraseña líderes", type="password")
    if clave != "BBVA2025":
        st.sidebar.warning("Contraseña incorrecta. Solo lectura.")
    else:
        st.sidebar.success("Acceso de líder habilitado.")
        meta_dia = st.sidebar.number_input(
            "Meta de casos por día",
            min_value=0,
            value=int(meta_dia),
            step=1,
        )
        meta_mes = st.sidebar.number_input(
            "Meta de casos por mes",
            min_value=0,
            value=int(meta_mes),
            step=5,
        )
        st.sidebar.markdown("---")
        st.sidebar.markdown("Tarifas por tipo de caso:")
        valor_prod = st.sidebar.number_input(
            "Valor por caso Productividad ($)",
            min_value=0.0,
            value=float(valor_prod),
            step=500.0,
        )
        valor_adic = st.sidebar.number_input(
            "Valor por caso Adicional ($)",
            min_value=0.0,
            value=float(valor_adic),
            step=500.0,
        )
        valor_sabado = st.sidebar.number_input(
            "Valor por caso Meta sábado ($)",
            min_value=0.0,
            value=float(valor_sabado),
            step=500.0,
        )

# Guardar SIEMPRE la configuración actual
config = {
    "meta_dia": int(meta_dia),
    "meta_mes": int(meta_mes),
    "valor_prod": float(valor_prod),
    "valor_adic": float(valor_adic),
    "valor_sabado": float(valor_sabado),
    "salario_base_mensual": float(salario_base_mensual),
}
guardar_config(config)

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
    """
    True solo si el analista ha cumplido la meta TODOS los días del rango donde tiene casos.
    """
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
    st.write(
        "Puede registrar sus casos en modo rápido (pegando una lista de números de caso) "
        "o en modo detallado (tabla editable)."
    )

    col_emp1, col_emp2 = st.columns(2)
    with col_emp1:
        nombre_empleado = st.text_input("Nombre del empleado")
    with col_emp2:
        lider = st.selectbox("Líder a cargo", LIDERES)

    hoy = date.today()

    modo_registro = st.radio(
        "Modo de registro de casos",
        ["Ingreso rápido (lista de números de caso)", "Ingreso detallado (tabla)"],
    )

    # ---------- MODO RÁPIDO ----------
    if modo_registro == "Ingreso rápido (lista de números de caso)":
        st.markdown("### Ingreso rápido de casos")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            fecha_casos = st.date_input("Fecha de los casos", value=hoy)
        with col_r2:
            tipo_caso_rapido = st.selectbox("Tipo de caso", TIPOS_CASO, key="tipo_rapido")
        with col_r3:
            categoria_rapida = st.selectbox("Categoría", CATEGORIAS, key="cat_rapida")

        lista_texto = st.text_area(
            "Ingrese los números de caso (uno por línea o separados por comas)",
            height=150,
            placeholder="Ejemplo:\n123456\n123457\n123458\n\nO:\n123456,123457,123458",
        )

        if st.button("Guardar casos rápidos", type="primary"):
            if nombre_empleado.strip() == "":
                st.warning("Por favor ingrese el nombre del empleado.")
            elif lista_texto.strip() == "":
                st.warning("Por favor ingrese al menos un número de caso.")
            else:
                # Separar por líneas y comas
                raw_items = []
                for linea in lista_texto.splitlines():
                    partes = [p.strip() for p in linea.replace(";", ",").split(",")]
                    raw_items.extend(p for p in partes if p)

                numeros_caso = [x for x in raw_items if x != ""]

                if not numeros_caso:
                    st.warning("No se encontraron números de caso válidos.")
                else:
                    df_nuevo = pd.DataFrame(
                        {
                            "Numero_caso": numeros_caso,
                            "Fecha": [fecha_casos] * len(numeros_caso),
                            "Tipo_caso": [tipo_caso_rapido] * len(numeros_caso),
                            "Categoria": [categoria_rapida] * len(numeros_caso),
                        }
                    )
                    df_nuevo["Empleado"] = nombre_empleado
                    df_nuevo["Lider"] = lider

                    if df.empty:
                        next_id = 1
                    else:
                        next_id = df["ID"].max() + 1
                    df_nuevo["ID"] = range(next_id, next_id + len(df_nuevo))
                    df_nuevo["Duplicado"] = False

                    df_nuevo = df_nuevo[
                        ["ID", "Empleado", "Lider", "Numero_caso",
                         "Fecha", "Tipo_caso", "Categoria", "Duplicado"]
                    ]

                    st.session_state["registros"] = pd.concat(
                        [st.session_state["registros"], df_nuevo],
                        ignore_index=True,
                    )
                    df = st.session_state["registros"]

                    # Recalcular duplicados globales
                    df["Duplicado"] = df.duplicated(
                        subset=["Empleado", "Numero_caso"], keep=False
                    )

                    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                    st.success(f"Se guardaron {len(numeros_caso)} caso(s) correctamente en modo rápido.")

    # ---------- MODO DETALLADO ----------
    else:
        st.markdown("### Ingreso detallado de casos (tabla editable)")
        st.write("Puede copiar/pegar filas completas desde Excel.")

        # Plantilla con varias filas vacías para facilitar el llenado
        plantilla = pd.DataFrame(
            [
                {
                    "Numero_caso": "",
                    "Fecha": hoy,
                    "Tipo_caso": "Productividad",
                    "Categoria": "Finalizado",
                }
                for _ in range(5)
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
            key="editor_detallado",
        )

        if st.button("Guardar todos los casos (modo detallado)", type="primary"):
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

                    edited["Duplicado"] = False

                    edited = edited[
                        ["ID", "Empleado", "Lider", "Numero_caso",
                         "Fecha", "Tipo_caso", "Categoria", "Duplicado"]
                    ]

                    st.session_state["registros"] = pd.concat(
                        [st.session_state["registros"], edited], ignore_index=True
                    )
                    df = st.session_state["registros"]

                    # Recalcular duplicados globales
                    df["Duplicado"] = df.duplicated(
                        subset=["Empleado", "Numero_caso"], keep=False
                    )

                    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                    st.success("Registros guardados correctamente en modo detallado.")

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
                cumple_meta_mes = casos_mes >= meta_mes

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
                    st.metric(
                        "Cumple meta mensual",
                        "Sí" if cumple_meta_mes else "No"
                    )
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

                # Gráfica por día y categoría
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
                df_emp_mes_view["Duplicado_flag"] = df_emp_mes_view["Duplicado"].map(
                    lambda x: "Sí" if x else "No"
                )

                edited_view = st.data_editor(
                    df_emp_mes_view[
                        ["ID", "Empleado", "Lider", "Numero_caso", "Fecha",
                         "Tipo_caso", "Categoria", "Duplicado_flag", "Eliminar"]
                    ],
                    key="editor_empleado",
                    column_config={
                        "Eliminar": st.column_config.CheckboxColumn("Eliminar"),
                        "Duplicado_flag": st.column_config.TextColumn("Duplicado"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                if st.button("Eliminar casos seleccionados"):
                    ids_a_borrar = edited_view.loc[edited_view["Eliminar"], "ID"].tolist()
                    if not ids_a_borrar:
                        st.warning("No seleccionó ningún caso para eliminar.")
                    else:
                        df = st.session_state["registros"]
                        df = df[~df["ID"].isin(ids_a_borrar)]
                        # Recalcular duplicados después de eliminar
                        df["Duplicado"] = df.duplicated(
                            subset=["Empleado", "Numero_caso"], keep=False
                        )
                        st.session_state["registros"] = df
                        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                        st.success(
                            f"Se eliminaron {len(ids_a_borrar)} caso(s). "
                            "Recargue la página para ver los cambios."
                        )

                # Tabla adicional solo con duplicados en ROJO
                df_dup_emp = df_emp_mes[df_emp_mes["Duplicado"]]
                st.markdown("#### Casos duplicados del mes (mismo empleado y número de caso)")
                if df_dup_emp.empty:
                    st.info("No se encontraron casos duplicados para este empleado en el mes.")
                else:
                    def color_duplicados(row):
                        return ['background-color: #f8d7da'] * len(row)

                    styled_dup = df_dup_emp.style.apply(color_duplicados, axis=1)
                    st.dataframe(styled_dup, use_container_width=True)

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

            # Racha perfecta por analista
            racha_flags = []
            for emp in resumen_emp["Empleado"]:
                df_emp = df_mes[df_mes["Empleado"] == emp]
                racha_flags.append(calcular_racha_meta(df_emp, meta_dia))
            resumen_emp["Racha_perfecta"] = racha_flags

            st.markdown("#### Resumen por empleado (mes actual)")

            # Colorear filas según cumpla meta mensual
            def color_por_meta(row):
                if row["Cumple_meta_mes"]:
                    color = "background-color: #d4edda"  # verde suave
                else:
                    color = "background-color: #f8d7da"  # rojo suave
                return [color] * len(row)

            styled_resumen = resumen_emp.style.apply(color_por_meta, axis=1)
            st.dataframe(styled_resumen, use_container_width=True)

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

            # Ranking de mejores analistas
            st.markdown("#### Mejores analistas del mes")

            ranking_casos = resumen_emp.sort_values("Casos_mes", ascending=False).head(5)
            ranking_valor = resumen_emp.sort_values("Valor_casos_mes", ascending=False).head(5)

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**Top 5 por número de casos**")
                st.dataframe(
                    ranking_casos[
                        ["Empleado", "Lider", "Casos_mes", "Cumple_meta_mes", "Racha_perfecta"]
                    ],
                    use_container_width=True,
                )
            with col_r2:
                st.markdown("**Top 5 por valor generado**")
                st.dataframe(
                    ranking_valor[
                        ["Empleado", "Lider", "Valor_casos_mes", "Total_mes_estimado"]
                    ],
                    use_container_width=True,
                )

            # Casos duplicados globales en rojo
            st.markdown("#### Casos duplicados (todos los empleados)")
            df_dup_global = df_mes[df_mes["Duplicado"]]
            if df_dup_global.empty:
                st.info("No se encontraron casos duplicados en el mes.")
            else:
                def color_duplicados(row):
                    return ['background-color: #f8d7da'] * len(row)

                styled_dup_global = df_dup_global.style.apply(color_duplicados, axis=1)
                st.dataframe(styled_dup_global, use_container_width=True)
