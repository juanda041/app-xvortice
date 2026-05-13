import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro")
st.markdown("**Daniel** | Gestión Patrimonial e Inversiones")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leer la pestaña correcta
    df = conn.read(worksheet="Movimientos", ttl=0)
    
    # Limpieza para evitar el error de "float" anterior
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})
    df['Categoría'] = df['Categoría'].astype(str).fillna("")
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. LÓGICA DE PATRIMONIO (Suma lo que tienes en el Excel) ---
    # Sumamos todas tus cuentas de activos
    total_ahorro = df[df['Categoría'].str.contains('Ahorro|Efectivo', case=False, na=False)]['Monto'].sum()
    total_inversion = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()
    
    patrimonio_total = total_ahorro + total_inversion
    meta_10k = 10000.00

    # --- 2. DASHBOARD PRINCIPAL ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    c2.metric("Inversiones Acumuladas", f"${total_inversion:,.2f}")
    c3.metric("Efectivo / Ahorros", f"${total_ahorro:,.2f}")
    c4.metric("Meta $10,000", f"{(patrimonio_total/meta_10k)*100:.1f}%")

    # --- 3. SECCIONES DE CONTROL ---
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Registrar & Historial", "📈 Mercado en Vivo", "📊 Análisis", "🤖 IA Xvortice"])

    with tab1:
        col_form, col_data = st.columns([1, 2])
        with col_form:
            st.subheader("Anotar Movimiento")
            with st.form("registro_v3"):
                f = st.date_input("Fecha", datetime.now())
                c = st.selectbox("Categoría", ["Ahorro", "Inversión", "Ingreso", "Gasto", "Efectivo"])
                m = st.number_input("Monto ($)", min_value=0.0)
                d = st.text_input("Detalle (Ej: Compra VOO, Abono cliente)")
                if st.form_submit_button("Guardar"):
                    st.success("¡Datos listos! Cópialos a tu Excel.")
        with col_data:
            st.subheader("Tus Apuntes")
            st.dataframe(df.tail(15), use_container_width=True)

    with tab2:
        st.subheader("Precios del Mercado")
        activos = ["NVDA", "VOO", "BAC", "O", "BTC-USD"]
        cols_m = st.columns(len(activos))
        for i, t in enumerate(activos):
            try:
                precio = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
                cols_m[i].metric(t, f"${precio:,.2f}")
            except: continue

    with tab3:
        st.subheader("Distribución Real")
        fig = px.pie(df[df['Categoría'].str.contains('Ahorro|Inversión|Inversion|Efectivo', case=False, na=False)], 
                     values='Monto', names='Categoría', hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Consultoría IA")
        pregunta = st.text_input("¿Qué quieres analizar hoy?")
        if pregunta:
            st.info(f"Daniel, tu patrimonio de ${patrimonio_total:,.2f} está creciendo. Tu meta de $10k está a ${meta_10k - patrimonio_total:,.2f} de distancia.")

except Exception as e:
    st.error(f"Error: {e}")
