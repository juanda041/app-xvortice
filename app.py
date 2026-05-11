import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Xvortice - Centro de Control", layout="wide")

st.title("🚀 Xvortice: Gestión Patrimonial e Inventario")
st.markdown("---")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos
try:
    df = conn.read(worksheet="Movimientos", ttl="0")
except Exception as e:
    st.error("Error al leer el Excel. Revisa los permisos.")
    df = pd.DataFrame()

# Menú lateral para navegación
menu = st.sidebar.selectbox("Selecciona una sección", ["Resumen General", "Registrar Movimiento", "Inventario Xvortice", "Analista IA"])

# --- SECCIÓN 1: RESUMEN GENERAL (Aquí ves tus totales) ---
if menu == "Resumen General":
    st.header("📊 Resumen de tu Patrimonio")
    
    if not df.empty:
        # Limpieza rápida de datos para cálculos
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        
        col1, col2, col3 = st.columns(3)
        total_ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
        total_gastos = df[df['Tipo'] == 'Gasto']['Monto'].sum()
        balance = total_ingresos - total_gastos
        
        col1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
        col2.metric("Total Gastos", f"${total_gastos:,.2f}", delta_color="inverse")
        col3.metric("Balance Neto", f"${balance:,.2f}")
        
        st.markdown("---")
        st.subheader("Histórico de Movimientos")
        fig = px.line(df, x='Fecha', y='Monto', color='Tipo', title="Flujo de Caja Xvortice")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos para mostrar el resumen.")

# --- SECCIÓN 2: REGISTRAR MOVIMIENTO (El formulario) ---
elif menu == "Registrar Movimiento":
    st.header("📝 Nuevo Registro")
    with st.form("registro_form"):
        fecha = st.date_input("Fecha")
        usuario = st.text_input("Nombre de Usuario (Quien registra)")
        tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
        categoria = st.selectbox("Categoría", ["Venta Perfume", "Venta Celular", "Venta Calzado", "Inversión", "Gasto Personal", "Otros"])
        monto = st.number_input("Monto ($)", min_value=0.0, step=0.01)
        comentario = st.text_area("Descripción o detalle")
        
        submit = st.form_submit_button("Guardar en la Nube")
        
        if submit:
            new_data = pd.DataFrame([{
                "Fecha": str(fecha),
                "Usuario": usuario,
                "Tipo": tipo,
                "Categoria": categoria,
                "Monto": monto,
                "Comentario": comentario
            }])
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(worksheet="Movimientos", data=updated_df)
            st.success("✅ ¡Guardado con éxito en Xvortice!")
            st.balloons()

# --- SECCIÓN 3: INVENTARIO (Control de productos) ---
elif menu == "Inventario Xvortice":
    st.header("📦 Control de Inventario")
    st.write("Esta sección analiza tus ventas para decirte qué productos están saliendo más.")
    if not df.empty:
        ventas = df[df['Tipo'] == 'Ingreso']['Categoria'].value_counts()
        st.bar_chart(ventas)
    else:
        st.write("Registra ventas para ver el análisis de inventario.")

# --- SECCIÓN 4: ANALISTA IA (Lógica pura) ---
elif menu == "Analista IA":
    st.header("🤖 Analista Financiero Xvortice")
    if not df.empty:
        total_ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
        total_gastos = df[df['Tipo'] == 'Gasto']['Monto'].sum()
        
        st.write("### Análisis Actual:")
        if total_ingresos > total_gastos:
            st.success(f"Vas por buen camino, Juan. Tu negocio tiene un margen positivo de ${(total_ingresos-total_gastos):,.2f}.")
        else:
            st.warning("Ojo: Tus gastos están superando los ingresos este mes.")
        
        st.info("Próximamente: Sugerencias automáticas de inversión basadas en tus ventas de perfumes y calzado.")
    else:
        st.write("La IA necesita datos para empezar a razonar contigo.")
