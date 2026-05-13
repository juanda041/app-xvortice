import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

# Estilo Dark Pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro")
st.markdown("**Daniel** | Gestión Patrimonial Inteligente")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Detalle': 'Ticker'})
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. CÁLCULO DE INVERSIONES EN TIEMPO REAL ---
    # Diccionario de tus activos principales
    tickers_interes = ["NVDA", "VOO", "BAC", "O", "BTC-USD"]
    precios_hoy = {}
    
    with st.expander("📈 Monitor de Mercado (Precios Actuales)", expanded=True):
        cols = st.columns(len(tickers_interes))
        for i, t in enumerate(tickers_interes):
            try:
                stock = yf.Ticker(t).history(period="1d")
                precio = stock['Close'].iloc[-1]
                precios_hoy[t] = precio
                cols[i].metric(t, f"${precio:,.2f}")
            except:
                precios_hoy[t] = 0

    # --- 2. LÓGICA DE PATRIMONIO TOTAL ---
    # Ahorros y Efectivo del Excel
    solo_ahorro = df[df['Categoría'].str.contains('Ahorro|Efectivo', case=False, na=False)]['Monto'].sum()
    
    # Inversiones: Si el Ticker está en nuestra lista, usamos el precio de mercado
    valor_inversiones_actual = 0
    for t in tickers_interes:
        # Aquí suponemos que en 'Monto' guardas la cantidad de acciones/títulos
        cant_acciones = df[df['Ticker'].str.contains(t, case=False, na=False)]['Monto'].sum()
        valor_inversiones_actual += (cant_acciones * precios_hoy.get(t, 0))

    # Si no guardas cantidades sino dinero invertido, sumamos el monto directo
    if valor_inversiones_actual == 0:
        valor_inversiones_actual = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()

    patrimonio_total = solo_ahorro + valor_inversiones_actual
    meta = 10000.00

    # --- 3. DASHBOARD ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    c2.metric("Inversiones (Valor Actual)", f"${valor_inversiones_actual:,.2f}")
    c3.metric("Ahorro / Efectivo", f"${solo_ahorro:,.2f}")
    c4.metric("Meta $10k", f"{(patrimonio_total/meta)*100:.1f}%")

    # --- 4. TABS ---
    t1, t2, t3 = st.tabs(["💰 Registros", "📊 Gráficas", "🤖 IA"])
    
    with t1:
        st.dataframe(df, use_container_width=True)
    with t2:
        fig = px.pie(values=[solo_ahorro, valor_inversiones_actual], 
                     names=['Ahorro/Efectivo', 'Inversiones'], 
                     title="Composición del Patrimonio", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)
    with t3:
        st.info(f"Daniel, tus inversiones representan el {(valor_inversiones_actual/patrimonio_total)*100:.1f}% de tu capital total.")

except Exception as e:
    st.error(f"Error: {e}")
