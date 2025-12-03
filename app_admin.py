import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Portal de Productividad", layout="wide")
st.title("Panel de Productividad de la Empresa")

CSV_PATH = "registro_empresarial2.csv"

# ------------------------
# CARGA DE DATOS PERSISTENTES
# ------------------------
if os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    except Exception:
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

# Estructura base
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
    # Si el CSV viejo no tiene ID o alguna columna, la creamos
    for col in COLUMNAS:
        if col not in df.columns:
            if col == "ID":
                df[col] = range(1, len(df) + 1)
            else:
                df[col] = None
    df = df[COLUMNAS]

# Asegurar IDs únicos
if df["ID"].isnull().any():
    df["ID"] = range(1, len(df) + 1)
df["ID"] = df["ID"].astype(int)

st.session_state["registros"] = df
df = st.session_state["registros"]

# ------------------------
# CONSTANTES
# ------------------------
LIDERES = [
    "Alejandra Puentes",
    "Carlos Cierra",
    "Edisson Ramirez",
    "Gabrielle Monroy",
    "Melissa Rodriguez",
]

TIPOS_CASO = ["Productividad", "Adicional", "Meta sábado"]
CATEGORIAS = ["Finalizado", "Tutela", "Defensoría"]

# ------------------------
# BARRA LATERAL
# ------------------------
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

# MODO LÍDER: modifica metas y valores
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
            "Valor por caso de Productividad ($)",
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

# ------------------------
# PERFIL EMPLEADO
# ------------------------
if perfil == "Empleado":
    st.subheader("Registro de productividad (Empleado)")
    st.write("1. Escriba su nombre y seleccione su líder.")
    st.write("2. Registre los casos del día en la tabla (puede copiar/pegar varias filas desde Excel).")
    st.write("3. Presione 'Guardar todos los casos' para almacenar la información.")

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

    if st.button("Guardar todos los casos"):
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

                # Asignar IDs nuevos
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

    # --------- RESUMEN DEL EMPLEADO ---------
    df = st.session_state["registros"]

    if df.empty:
        st.info("Aún no hay registros para mostrar.")
    else:
        st.subheader("Resumen del empleado")

        empleados_disponibles = ["Seleccione..."] + sorted(df["Empleado"].unique().tolist())
        empleado_sel = st.selectbox("Seleccione su nombre para ver su resumen", empleados_disponibles)

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

                # Dinero por tipo de caso
                def valor_fila(f):
                    if f["Tipo_caso"] == "Productividad":
                        return valor_prod
                    elif f["Tipo_caso"] == "Adicional":
                        return valor_adic
                    else:
                        return valor_sabado

                df_emp_mes["Valor_caso"] = df_emp_mes.apply(valor_fila, axis=1)
                dinero_casos_mes = df_emp_mes["Valor_caso"].sum()
                dinero_total_mes = salario_base_mensual + dinero_casos_mes

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Casos hoy", int(casos_dia))
                col2.metric("Casos en el mes", int(casos_mes))
                col3.metric("¿Cumple meta diaria?", "Sí" if casos_dia >= meta_dia else "No")
                col4.metric("¿Cumple meta mensual?", "Sí" if casos_mes >= meta_mes else "No")

                st.markdown("#### Dinero acumulado en el mes")
                col5, col6 = st.columns(2)
                col5.metric("Valor por casos (mes)", f"${dinero_casos_mes:,.0f}")
                col6.metric("Total estimado mes", f"${dinero_total_mes:,.0f}")

                st.markdown("#### Gráfica de productividad (casos por día)")
                df_graf = (
                    df_emp_mes.groupby(pd.to_datetime(df_emp_mes["Fecha"]).dt.date)["ID"]
                    .count()
                    .reset_index()
                    .rename(columns={"Fecha": "Día", "ID": "Total_casos"})
                )
                st.bar_chart(df_graf.set_index("Día")["Total_casos"])

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

# ------------------------
# PERFIL ADMINISTRADOR / LÍDER
# ------------------------
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
            def valor_fila(f):
                if f["Tipo_caso"] == "Productividad":
                    return valor_prod
                elif f["Tipo_caso"] == "Adicional":
                    return valor_adic
                else:
                    return valor_sabado

            df_mes["Valor_caso"] = df_mes.apply(valor_fila, axis=1)

            resumen_emp = df_mes.groupby(["Empleado", "Lider"]).agg(
                Casos_mes=("ID", "count"),
                Valor_casos_mes=("Valor_caso", "sum"),
            ).reset_index()

            resumen_emp["Total_mes_estimado"] = salario_base_mensual + resumen_emp["Valor_casos_mes"]
            resumen_emp["Cumple_meta_mes"] = resumen_emp["Casos_mes"] >= meta_mes

            st.markdown("#### Resumen por empleado (mes actual)")
            st.dataframe(resumen_emp, use_container_width=True)
