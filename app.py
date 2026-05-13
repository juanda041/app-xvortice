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
st.markdown("**Daniel** | Gestión Patrimonial e Inversiones")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Detalle': 'Ticker'})
    
    # --- LIMPIEZA CRÍTICA (Esto evita el error que te salió) ---
    df['Categoría'] = df['Categoría'].astype(str).fillna("")
    df['Ticker'] = df['Ticker'].astype(str).fillna("")
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. MONITOR DE MERCADO EN VIVO ---
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

    # --- 2. LÓGICA DE PATRIMONIO TOTAL (CON ACCIONES) ---
    # Sumamos Ahorros y Efectivo
    filtro_ahorro = df['Categoría'].str.contains('Ahorro|Efectivo', case=False, na=False)
    solo_ahorro = df[filtro_ahorro]['Monto'].sum()
    
    # Calculamos valor real de Inversiones
    valor_inversiones_actual = 0
    for t in tickers_interes:
        # Buscamos cuántas acciones tienes de ese Ticker en el Excel
        cant_acciones = df[df['Ticker'].str.contains(t, case=False, na=False)]['Monto'].sum()
        if cant_acciones > 0:
            valor_inversiones_actual += (cant_acciones * precios_hoy.get(t, 0))

    # Si no tienes cantidades de acciones, sumamos el monto fijo que pusiste como "Inversión"
    if valor_inversiones_actual == 0:
        filtro_inv = df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)
        valor_inversiones_actual = df[filtro_inv]['Monto'].sum()

    patrimonio_total = solo_ahorro + valor_inversiones_actual
    meta_10k = 10000.00

    # --- 3. DASHBOARD MAESTRO ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    c2.metric("Valor Portafolio (Hoy)", f"${valor_inversiones_actual:,.2f}")
    c3.metric("Efectivo / Ahorros", f"${solo_ahorro:,.2f}")
    c4.metric("Meta $10k", f"{(patrimonio_total/meta_10k)*100:.1f}%")

    # --- 4. SECCIONES ---
    t1, t2, t3, t4 = st.tabs(["💰 Historial", "📊 Gráficas", "💹 Interés", "🤖 IA"])
    
    with t1:
        st.dataframe(df, use_container_width=True)
    with t2:
        fig = px.pie(values=[solo_ahorro, valor_inversiones_actual], 
                     names=['Ahorro/Efectivo', 'Inversiones'], 
                     hole=0.5, title="Composición del Patrimonio Real")
        st.plotly_chart(fig, use_container_width=True)
    with t3:
        st.subheader("Simulador de Interés Compuesto")
        cap = st.number_input("Capital Inicial", value=float(patrimonio_total))
        años = st.slider("Años", 1, 30, 10)
        res = cap * (1 + (0.10))**años # Calculado al 10% anual
        st.success(f"En {años} años tendrías: ${res:,.2f}")
    with t4:
        st.info(f"Daniel, tu portafolio de acciones hoy vale ${valor_inversiones_actual:,.2f}. ¡Sigue así!")

except Exception as e:
    st.error(f"Error: {e}")
