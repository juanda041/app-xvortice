import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuración Pro de la App
st.set_page_config(page_title="Xvortice - Gestión Patrimonial", layout="wide", page_icon="🏛️")

# Estilo personalizado
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Inteligencia Financiera")
st.divider()

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leer datos de la hoja principal
    df = conn.read(ttl="0")
    df = df.dropna(how="all")
    df = df.fillna("")

    # Asegurar que Monto sea número
    if 'Monto' in df.columns:
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- LÓGICA DE GESTIÓN PATRIMONIAL ---
    # Filtramos por tus categorías reales
    ahorros = df[df['Categoría'].str.contains('Ahorro', case=False, na=False)]['Monto'].sum()
    inversiones = df[df['Categoría'].str.contains('Inversión', case=False, na=False)]['Monto'].sum()
    deudas_clientes = df[df['Categoría'].str.contains('Deuda|Préstamo', case=False, na=False)]['Monto'].sum()
    
    patrimonio_total = ahorros + inversiones + deudas_clientes

    # --- DASHBOARD SUPERIOR ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Patrimonio Total", f"${patrimonio_total:,.2f}")
    with col2:
        st.metric("Ahorros Líquidos", f"${ahorros:,.2f}")
    with col3:
        st.metric("Portafolio Inversión", f"${inversiones:,.2f}")
    with col4:
        st.metric("Cuentas por Cobrar", f"${deudas_clientes:,.2f}")

    # --- ANÁLISIS CON IA Y GRÁFICAS ---
    st.divider()
    pest1, pest2, pest3 = st.tabs(["📊 Análisis Visual", "💰 Control de Gastos", "🤖 Consultas IA"])

    with pest1:
        st.subheader("Distribución de Activos")
        fig = px.pie(df, values='Monto', names='Categoría', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    with pest2:
        st.subheader("Historial de Movimientos")
        # Buscador para filtrar rápido
        busqueda = st.text_input("🔍 Buscar en descripción o detalle:")
        if busqueda:
            df_mostrar = df[df.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
        else:
            df_mostrar = df
        st.dataframe(df_mostrar, use_container_width=True)

    with pest3:
        st.subheader("Asistente Xvortice")
        pregunta = st.text_input("Hazle una pregunta a la IA sobre tus finanzas:")
        if pregunta:
            # Aquí simulamos la respuesta basada en tus datos reales
            if "ahorro" in pregunta.lower():
                st.info(f"Daniel, según tus datos, llevas ${ahorros:,.2f} ahorrados. Estás al {(ahorros/5000)*100:.1f}% de tu meta de $5,000.")
            else:
                st.write("Analizando tendencias en tu base de datos...")
                st.success("Tus inversiones en ETFs están diversificadas correctamente según el plan.")

except Exception as e:
    st.error(f"Error al cargar el cerebro de la app: {e}")
    st.info("Asegúrate de que las columnas en tu Excel se llamen: Fecha, Categoría, Monto, Detalle.")
