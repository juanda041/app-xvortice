import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Patrimonio de Alto Nivel")
st.subheader("Daniel | Gestión Patrimonial e Inversiones")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto'})
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. LÓGICA DE INGRESOS Y EGRESOS (SEPARADOS) ---
    ingresos = df[df['Categoría'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    egresos = df[df['Categoría'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    ahorro_real = ingresos - egresos
    meta = 10000.00

    # --- 2. PORTAFOLIO EN VIVO (MERCADO) ---
    st.divider()
    st.markdown("### 📈 Portafolio en Tiempo Real")
    # Aquí buscamos las filas que sean "Inversión" y tengan un Ticker (ej: NVDA, BTC-USD) en el Comentario o Detalle
    activos = ["NVDA", "BTC-USD", "ETH-USD", "VOO"] # tickers que manejamos
    precios_vivos = {}
    
    col_vivos = st.columns(len(activos))
    for i, ticker in enumerate(activos):
        try:
            data = yf.Ticker(ticker).history(period="1d")
            precio = data['Close'].iloc[-1]
            precios_vivos[ticker] = precio
            col_vivos[i].metric(ticker, f"${precio:,.2f}")
        except:
            continue

    # --- 3. DASHBOARD PRINCIPAL ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Totales", f"${ingresos:,.2f}")
    c2.metric("Gastos Totales", f"${egresos:,.2f}", delta=f"-{egresos:,.2f}", delta_color="inverse")
    c3.metric("Patrimonio Neto", f"${ahorro_real:,.2f}")
    progreso = (ahorro_real / meta) * 100
    c4.metric("Meta $10k", f"{progreso:.1f}%", f"${ahorro_real - meta:,.2f}")

    # --- 4. SECCIONES AVANZADAS ---
    t1, t2, t3, t4 = st.tabs(["📊 Flujo de Caja", "🏦 Inversiones", "💹 Interés Compuesto", "🤖 IA Xvortice"])

    with t1:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_pie = px.pie(df, values='Monto', names='Categoría', hole=0.5, title="Distribución Global")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            st.write("### Últimos Movimientos")
            st.dataframe(df.tail(10), use_container_width=True)

    with t2:
        st.write("### Análisis de Activos")
        # Gráfica de barras de lo que tienes invertido
        df_inv = df[df['Categoría'].str.contains('Inversión', case=False, na=False)]
        if not df_inv.empty:
            fig_inv = px.bar(df_inv, x='Detalle', y='Monto', color='Monto', title="Capital por Activo")
            st.plotly_chart(fig_inv, use_container_width=True)

    with t3:
        st.subheader("Simulador de Libertad Financiera")
        p_ini = st.number_input("Capital Actual", value=float(ahorro_real))
        t_int = st.slider("Interés Anual Esperado (%)", 1, 20, 10)
        tiempo = st.slider("Años de espera", 1, 40, 10)
        res = p_ini * (1 + (t_int/100))**tiempo
        st.success(f"Daniel, proyectando tu capital a {tiempo} años, tendrías: ${res:,.2f}")

    with t4:
        st.subheader("Consultas de Inteligencia Artificial")
        pregunta = st.text_input("¿En qué puedo ayudarte hoy, Daniel?")
        if pregunta:
            st.info("🤖 Analizando... Tu relación Ingreso/Gasto es positiva. Tienes un margen del " + str(round((ahorro_real/ingresos)*100, 2)) + "% para invertir.")

except Exception as e:
    st.error(f"Error al cargar el sistema completo: {e}")
