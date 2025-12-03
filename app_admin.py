import streamlit as st
import pandas as pd
from datetime import datetime

# ------------------------
# CONFIGURACIÓN GENERAL
# ------------------------
st.set_page_config(page_title="Portal de Productividad", layout="wide")
st.title("Panel de Productividad de la Empresa")

if "registros" not in st.session_state:
    st.session_state["registros"] = pd.DataFrame(
        columns=[
            "Empleado",
            "Lider",
            "Fecha",
            "Tipo_caso",       # Productividad / Adicional / Meta sábado
            "Categoria",       # Finalizado / Tutela / Defensoría
            "Casos",
            "Horas_extra",
            "Tipo_hora_extra", # Normal / Nocturna / Festiva
            "Valor_hora_extra",
            "Valor_por_caso",
            "Adicionales",
        ]
    )

df = st.session_state["registros"]

LIDERES = [
    "Alejandra Puentes",
    "Carlos Cierra",
    "Edisson Ramirez",
    "Gabrielle Monroy",
    "Melissa Rodriguez",
]

TIPOS_CASO = ["Productividad", "Adicional", "Meta sábado"]
CATEGORIAS = ["Finalizado", "Tutela", "Defensoría"]
TIPOS_HORA_EXTRA = ["Normal", "Nocturna", "Festiva"]

# ------------------------
# BARRA LATERAL
# ------------------------
st.sidebar.header("Configuración")

perfil = st.sidebar.selectbox("Perfil", ["Empleado", "Administrador", "Líder"])

# Parámetros base (se pueden modificar en modo Líder)
if "meta_dia" not in st.session_state:
    st.session_state["meta_dia"] = 20
if "meta_mes" not in st.session_state:
    st.session_state["meta_mes"] = 300

if "vh_normal" not in st.session_state:
    st.session_state["vh_normal"] = 8088.0
if "vh_nocturna" not in st.session_state:
    st.session_state["vh_nocturna"] = 9500.0
if "vh_festiva" not in st.session_state:
    st.session_state["vh_festiva"] = 12000.0

if "vp_productividad" not in st.session_state:
    st.session_state["vp_productividad"] = 3500.0
if "vp_adicional" not in st.session_state:
    st.session_state["vp_adicional"] = 4000.0
if "vp_meta_sabado" not in st.session_state:
    st.session_state["vp_meta_sabado"] = 5000.0

salario_base_mensual = st.sidebar.number_input(
    "Salario base mensual ($)", min_value=0.0, value=1_500_000.0, step=100_000.0
)

# MODO LÍDER: solo si pone la clave correcta
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
        st.sidebar.markdown("Valores por defecto de horas extra:")
        st.session_state["vh_normal"] = st.sidebar.number_input(
            "Valor hora extra normal ($)", min_value=0.0, value=st.session_state["vh_normal"], step=500.0
        )
        st.session_state["vh_nocturna"] = st.sidebar.number_input(
            "Valor hora extra nocturna ($)", min_value=0.0, value=st.session_state["vh_nocturna"], step=500.0
        )
        st.session_state["vh_festiva"] = st.sidebar.number_input(
            "Valor hora extra festiva ($)", min_value=0.0, value=st.session_state["vh_festiva"], step=500.0
        )
        st.sidebar.markdown("---")
        st.sidebar.markdown("Valores por defecto de casos:")
        st.session_state["vp_productividad"] = st.sidebar.number_input(
            "Valor por caso de productividad ($)",
            min_value=0.0,
            value=st.session_state["vp_productividad"],
            step=500.0,
        )
        st.session_state["vp_adicional"] = st.sidebar.number_input(
            "Valor por caso adicional ($)",
            min_value=0.0,
            value=st.session_state["vp_adicional"],
            step=500.0,
        )
        st.session_state["vp_meta_sabado"] = st.sidebar.number_input(
            "Valor por caso meta sábado ($)",
            min_value=0.0,
            value=st.session_state["vp_meta_sabado"],
            step=500.0,
        )

st.markdown("---")

meta_dia = st.session_state["meta_dia"]
meta_mes = st.session_state["meta_mes"]

# ------------------------
# PERFIL EMPLEADO
# ------------------------
if perfil == "Empleado":
    st.subheader("Registro de productividad (Empleado)")

    st.markdown("Complete la tabla con los casos del día y luego guarde todos los registros.")

    # Tabla editable para varios casos a la vez
    hoy = datetime.today().date()
    data_inicial = pd.DataFrame(
        [
            {
                "Empleado": "",
                "Lider": LIDERES[0],
                "Fecha": hoy,
                "Tipo_caso": TIPOS_CASO[0],
                "Categoria": CATEGORIAS[0],
                "Casos": 1,
                "Horas_extra": 0.0,
                "Tipo_hora_extra": TIPOS_HORA_EXTRA[0],
                "Valor_hora_extra": st.session_state["vh_normal"],
                "Valor_por_caso": st.session_state["vp_productividad"],
                "Adicionales": 0.0,
            }
        ]
    )

    edited = st.data_editor(
        data_inicial,
        num_rows="dynamic",
        use_container_width=True,
    )

    if st.button("Guardar todos los casos del día"):
        # Validar que el nombre del empleado no esté vacío
        if edited["Empleado"].str.strip().eq("").any():
            st.warning("Todos los registros deben tener el nombre del empleado.")
        else:
            # Convertir fecha a datetime
            edited["Fecha"] = pd.to_datetime(edited["Fecha"]).dt.date
            edited["Casos"] = edited["Casos"].fillna(0).astype(int)
            edited["Horas_extra"] = edited["Horas_extra"].fillna(0.0).astype(float)
            edited["Valor_hora_extra"] = edited["Valor_hora_extra"].fillna(0.0).astype(float)
            edited["Valor_por_caso"] = edited["Valor_por_caso"].fillna(0.0).astype(float)
            edited["Adicionales"] = edited["Adicionales"].fillna(0.0).astype(float)

            st.session_state["registros"] = pd.concat(
                [st.session_state["registros"], edited], ignore_index=True
            )
            df = st.session_state["registros"]
            st.success("Registros guardados correctamente.")

    if df.empty:
        st.info("Aún no hay registros para mostrar.")
    else:
        st.subheader("Resumen del empleado")

        empleados_disponibles = ["Seleccione..."] + sorted(df["Empleado"].unique().tolist())
        empleado_sel = st.selectbox("Seleccione su nombre para ver su resumen", empleados_disponibles)

        if empleado_sel != "Seleccione...":
            hoy = datetime.today()
            df_emp_mes = df[
                (df["Empleado"] == empleado_sel)
                & (pd.to_datetime(df["Fecha"]).dt.month == hoy.month)
                & (pd.to_datetime(df["Fecha"]).dt.year == hoy.year)
            ]

            if df_emp_mes.empty:
                st.info("No hay registros para este mes.")
            else:
                # Día actual
                df_emp_hoy = df_emp_mes[pd.to_datetime(df_emp_mes["Fecha"]).dt.date == hoy.date()]

                casos_dia = df_emp_hoy["Casos"].sum()
                casos_mes = df_emp_mes["Casos"].sum()

                # Cálculo de dinero
                dinero_horas = (df_emp_mes["Horas_extra"] * df_emp_mes["Valor_hora_extra"]).sum()
                dinero_casos = (df_emp_mes["Casos"] * df_emp_mes["Valor_por_caso"]).sum()
                adicionales_mes = df_emp_mes["Adicionales"].sum()
                dinero_total_mes = salario_base_mensual + dinero_horas + dinero_casos + adicionales_mes

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Casos hoy", int(casos_dia))
                col2.metric("Casos en el mes", int(casos_mes))
                col3.metric("¿Cumple meta diaria?", "Sí" if casos_dia >= meta_dia else "No")
                col4.metric("¿Cumple meta mensual?", "Sí" if casos_mes >= meta_mes else "No")

                st.markdown("#### Dinero acumulado en el mes")
                col5, col6, col7 = st.columns(3)
                col5.metric("Horas extra (mes)", f"${dinero_horas:,.0f}")
                col6.metric("Casos (mes)", f"${dinero_casos:,.0f}")
                col7.metric("Total estimado mes", f"${dinero_total_mes:,.0f}")

                st.markdown("#### Gráfica de productividad (casos por día)")
                df_graf = (
                    df_emp_mes.groupby(pd.to_datetime(df_emp_mes["Fecha"]).dt.date)["Casos"]
                    .sum()
                    .reset_index()
                    .rename(columns={"Fecha": "Día"})
                )
                st.bar_chart(df_graf.set_index("Fecha")["Casos"])

                st.markdown("#### Registros del mes")
                st.dataframe(df_emp_mes, use_container_width=True)

# ------------------------
# PERFIL ADMINISTRADOR / LÍDER (LECTURA GLOBAL)
# ------------------------
if perfil in ["Administrador", "Líder"]:
    st.subheader("Vista global de productividad")

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
            resumen = df_mes.copy()
            resumen["Dinero_horas"] = resumen["Horas_extra"] * resumen["Valor_hora_extra"]
            resumen["Dinero_casos"] = resumen["Casos"] * resumen["Valor_por_caso"]
            resumen["Total_mes_est"] = salario_base_mensual + resumen["Dinero_horas"] + resumen["Dinero_casos"] + resumen["Adicionales"]

            resumen_emp = resumen.groupby(["Empleado", "Lider"]).agg(
                Casos_mes=("Casos", "sum"),
                Horas_extra_mes=("Horas_extra", "sum"),
                Adicionales_mes=("Adicionales", "sum"),
                Dinero_horas_mes=("Dinero_horas", "sum"),
                Dinero_casos_mes=("Dinero_casos", "sum"),
                Total_mes=("Total_mes_est", "sum"),
            ).reset_index()

            resumen_emp["Cumple_meta_mes"] = resumen_emp["Casos_mes"] >= meta_mes

            st.markdown("#### Resumen por empleado (mes actual)")
            st.dataframe(resumen_emp, use_container_width=True)
