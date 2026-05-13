import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN DARK PRO ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1f2937; border-radius: 10px 10px 0px 0px; color: white; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro")
st.markdown(f"**Daniel** | Gestión de Capital e Inversiones")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. MONITOR DE MERCADO (DIVERSIFICACIÓN) ---
    with st.expander("📈 Monitor de Mercado en Vivo", expanded=True):
        activos = ["NVDA", "BTC-USD", "VOO", "BAC", "O"]
        cols_m = st.columns(len(activos))
        for i, ticker in enumerate(activos):
            try:
                data = yf.Ticker(ticker).history(period="1d")
                precio = data['Close'].iloc[-1]
                cols_m[i].metric(ticker, f"${precio:,.2f}")
            except: continue

    # --- 2. LÓGICA DE PATRIMONIO MAESTRA ---
    # Sumamos todo lo que es Capital (Ahorros + Inversiones + Efectivo)
    patrimonio_total = df[df['Categoría'].str.contains('Ahorro|Inversión|Inversion|Efectivo', case=False, na=False)]['Monto'].sum()
    
    # Diferenciamos Ingresos vs Gastos del mes para el flujo
    ingresos_mes = df[df['Categoría'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    gastos_mes = df[df['Categoría'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    
    meta_objetivo = 10000.00
    progreso_meta = (patrimonio_total / meta_objetivo) * 100

    # --- 3. DASHBOARD PRINCIPAL ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    c2.metric("Flujo Mensual (Neto)", f"${ingresos_mes - gastos_mes:,.2f}")
    c3.metric("Meta $10,000", f"{progreso_meta:.1f}%")
    c4.metric("Faltante Meta", f"${meta_objetivo - patrimonio_total:,.2f}")

    # --- 4. PANEL DE CONTROL ---
    t1, t2, t3, t4 = st.tabs(["💰 Gestión y Registro", "📊 Análisis de Activos", "💹 Interés Compuesto", "🤖 IA Xvortice"])

    with t1:
        col_f, col_v = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Registrar Movimiento")
            with st.form("reg_master"):
                f = st.date_input("Fecha", datetime.now())
                c = st.selectbox("Categoría", ["Ahorro", "Inversión", "Ingreso", "Gasto", "Efectivo"])
                m = st.number_input("Monto ($)", min_value=0.0)
                d = st.text_input("Detalle")
                if st.form_submit_button("Guardar"):
                    st.success("¡Listo! Agrégalo a tu Excel.")
        with col_v:
            st.subheader("Historial Reciente")
            st.dataframe(df.tail(15), use_container_width=True)

    with t2:
        st.subheader("Distribución de tu Patrimonio")
        fig = px.pie(df[df['Categoría'].str.contains('Ahorro|Inversión|Inversion|Efectivo', case=False, na=False)], 
                     values='Monto', names='Categoría', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_
