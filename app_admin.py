import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Portal de Productividad", layout="wide")

st.title("Panel de Productividad de la Empresa")

# Inicializar tabla de registros en memoria
if "registros" not in st.session_state:
    st.session_state["registros"] = pd.DataFrame(
        columns=[
            "Empleado",
            "Fecha",
            "Casos",
            "Horas extra",
            "Adicionales",
        ]
    )

df = st.session_state["registros"]

# Barra lateral: selección de perfil y parámetros generales
st.sidebar.header("Configuración")

perfil = st.sidebar.selectbox("Perfil", ["Empleado", "Administrador"])

# Parámetros de cálculo
salario_base_mensual = st.sidebar.number_input(
    "Salario base mensual ($)", min_value=0.0, value=1_500_000.0, step=100_000.0
)
valor_hora_extra = st.sidebar.number_input(
    "Valor por hora extra ($)", min_value=0.0, value=10_000.0, step=1_000.0
)
valor_por_caso = st.sidebar.number_input(
    "Valor aproximado por caso ($)", min_value=0.0, value=5_000.0, step=500.0
)
meta_casos_mes = st.sidebar.number_input(
    "Meta de casos por mes (para evaluación en modo administrador)",
    min_value=0,
    value=100,
    step=5,
)

st.markdown("---")

# PERFIL EMPLEADO
if perfil == "Empleado":
    st.subheader("Registro de productividad (Empleado)")

    with st.form("form_empleado"):
        col1, col2 = st.columns(2)
        with col1:
            empleado = st.text_input("Nombre del empleado")
            fecha = st.date_input("Fecha", value=datetime.today())
            casos = st.number_input("Número de casos del día", min_value=0, step=1)
        with col2:
            horas_extra = st.number_input("Horas extra del día", min_value=0.0, step=0.5)
            adicionales = st.number_input("Adicionales ($)", min_value=0.0, step=1000.0)

        enviado = st.form_submit_button("Guardar registro")

    if enviado:
        if empleado.strip() == "":
            st.warning("Por favor ingrese el nombre del empleado.")
        else:
            nuevo = pd.DataFrame(
                [[empleado, fecha, casos, horas_extra, adicionales]],
                columns=df.columns,
            )
            st.session_state["registros"] = pd.concat(
                [st.session_state["registros"], nuevo], ignore_index=True
            )
            df = st.session_state["registros"]
            st.success("Registro guardado correctamente.")

    if df.empty:
        st.info("Aún no hay registros para mostrar.")
    else:
        st.subheader("Resumen del empleado")

        empleados_disponibles = ["Seleccione..."] + sorted(df["Empleado"].unique().tolist())
        empleado_sel = st.selectbox("Seleccione su nombre para ver su resumen", empleados_disponibles)

        if empleado_sel != "Seleccione...":
            hoy = datetime.today()
            df_empleado = df[
                (df["Empleado"] == empleado_sel)
                & (pd.to_datetime(df["Fecha"]).dt.month == hoy.month)
                & (pd.to_datetime(df["Fecha"]).dt.year == hoy.year)
            ]

            if df_empleado.empty:
                st.info("No hay registros para este mes.")
            else:
                total_casos = df_empleado["Casos"].sum()
                total_horas_extra = df_empleado["Horas extra"].sum()
                total_adicionales = df_empleado["Adicionales"].sum()

                pago_por_horas = total_horas_extra * valor_hora_extra
                pago_por_casos = total_casos * valor_por_caso
                pago_estimado = salario_base_mensual + pago_por_horas + pago_por_casos + total_adicionales

                colA, colB, colC, colD = st.columns(4)
                colA.metric("Casos en el mes", int(total_casos))
                colB.metric("Horas extra en el mes", f"{total_horas_extra:.1f}")
                colC.metric("Adicionales acumulados", f"${total_adicionales:,.0f}")
                colD.metric("Pago estimado del mes", f"${pago_estimado:,.0f}")

                st.markdown("#### Registros del mes")
                st.dataframe(df_empleado, use_container_width=True)

# PERFIL ADMINISTRADOR
else:
    st.subheader("Vista de administrador")

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
            resumen = df_mes.groupby("Empleado").agg(
                Casos_mes=("Casos", "sum"),
                Horas_extra_mes=("Horas extra", "sum"),
                Adicionales_mes=("Adicionales", "sum"),
            ).reset_index()

            resumen["Pago_estimado"] = (
                salario_base_mensual
                + resumen["Horas_extra_mes"] * valor_hora_extra
                + resumen["Casos_mes"] * valor_por_caso
                + resumen["Adicionales_mes"]
            )

            resumen["Cumple_meta"] = resumen["Casos_mes"] >= meta_casos_mes

            st.markdown("#### Resumen por empleado (mes actual)")
            st.dataframe(resumen, use_container_width=True)

            st.markdown("Notas:")
            st.write(
                "- 'Casos_mes' corresponde al número total de casos registrados en el mes actual por cada empleado."
            )
            st.write(
                "- 'Cumple_meta' compara los casos del mes con la meta configurada en la barra lateral."
            )
