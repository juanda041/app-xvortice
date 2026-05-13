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
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción', 'Detalle': 'Ticker'})
    
    # Asegurar que los datos sean legibles
    df['Categoría'] = df['Categoría'].astype(str).fillna("")
    df['Ticker'] = df['Ticker'].astype(str).fillna("")
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. MERCADO EN VIVO ---
    tickers_vivos = ["NVDA", "VOO", "BAC", "O", "BTC-USD"]
    precios_mkt = {}
    with st.expander("📈 Monitor de Mercado", expanded=True):
        cols_m = st.columns(len(tickers_vivos))
        for i, t in enumerate(tickers_vivos):
            try:
                p = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
                precios_mkt[t] = p
                cols_m[i].metric(t, f"${p:,.2f}")
            except:
                precios_mkt[t] = 0

    # --- 2. LÓGICA DE PATRIMONIO DANIEL ---
    ingresos = df[df['Categoría'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    gastos_personales = df[df['Categoría'].str.contains('Gasto Personal|Egreso', case=False, na=False)]['Monto'].sum()
    cuentas_cobrar = df[df['Categoría'].str.contains('Cobrar', case=False, na=False)]['Monto'].sum()
    
    # Inversiones valorizadas (Monto del Excel = Cantidad de acciones)
    valor_acciones = 0
    for t, precio in precios_mkt.items():
        cantidad = df[df['Ticker'].str.contains(t, case=False, na=False)]['Monto'].sum()
        valor_acciones += (cantidad * precio)
    
    # Si no hay tickers detectados, sumamos el monto directo de "Inversión"
    if valor_acciones == 0:
        valor_acciones = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()

    # PATRIMONIO = Ingresos + Valor Acciones + Cuentas Cobrar - Gastos Personales
    patrimonio_total = (ingresos + valor_acciones + cuentas_cobrar) - gastos_personales
    
    # --- 3. DASHBOARD ---
    st.divider()
    meta_dinamica = st.sidebar.number_input("🎯 Ajustar Meta", value=10000)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    c2.metric("Portafolio en Vivo", f"${valor_acciones:,.2f}")
    c3.metric("Cuentas por Cobrar", f"${cuentas_cobrar:,.2f}")
    c4.metric(f"Meta ${meta_dinamica:,.0f}", f"{(patrimonio_total/meta_dinamica)*100:.1f}%")

    # --- 4. TABS ---
    t1, t2, t3, t4 = st.tabs(["💰 Gestión", "📊 Análisis", "💹 Interés", "🤖 IA"])

    with t1:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            with st.form("f1"):
                st.write("Registrar Movimiento")
                cat = st.selectbox("Categoría", ["Ingreso", "Gasto Personal", "Gasto Operativo", "Inversión", "Cuenta por Cobrar"])
                mon = st.number_input("Monto", min_value=0.0)
                tic = st.text_input("Ticker o Detalle")
                if st.form_submit_button("Guardar"):
                    st.success("Cópialo a tu Excel.")
        with col_b:
            st.dataframe(df.tail(10), use_container_width=True)

    with t2:
        fig = px.pie(names=['Inversiones', 'Cuentas Cobrar', 'Capital Neto'], 
                     values=[valor_acciones, cuentas_cobrar, (ingresos - gastos_personales)], hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

    with t3:
        st.subheader("Simulador de Años")
        cap = st.number_input("Capital", value=float(patrimonio_total))
        tas = st.slider("Interés %", 1, 30, 10)
        añs = st.slider("Años", 1, 50, 10)
        st.write(f"Resultado: ${cap * (1 + (tas/100))**añs:,.2f}")

    with t4:
        st.write("🤖 Consultoría IA Xvortice")
        duda = st.text_input("Pregunta:")
        if duda:
            st.info(f"Daniel, tu patrimonio real es ${patrimonio_total:,.2f}. Tu enfoque en activos por cobrar es clave.")

except Exception as e:
    st.error(f"Error: {e}")
