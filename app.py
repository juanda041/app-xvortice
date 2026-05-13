import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN DE INTERFAZ LIMPIA ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f2937; border-radius: 5px; color: white; padding: 8px 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Gestión Patrimonial")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. CARGA DE PESTAÑAS (Basado en tus fotos)
    movs = conn.read(worksheet="Movimientos", ttl=0).dropna(how='all')
    portafolio = conn.read(worksheet="Portafolio", ttl=0).dropna(how='all')
    creditos = conn.read(worksheet="Creditos", ttl=0).dropna(how='all')

    # Limpieza de nombres de columnas
    movs.columns = [str(c).strip() for c in movs.columns]
    portafolio.columns = [str(c).strip() for c in portafolio.columns]
    creditos.columns = [str(c).strip() for c in creditos.columns]

    # --- 2. LÓGICA DE INVERSIONES CONSOLIDADAS ---
    # Sumamos cantidades de la misma acción para que no se repitan
    inv_resumen = portafolio.groupby('Ticker')['Cantidad'].sum().reset_index()
    
    valor_portafolio_hoy = 0
    with st.sidebar:
        st.header("📊 Precios en Vivo")
        for index, row in inv_resumen.iterrows():
            ticker = row['Ticker']
            if ticker != "CASH":
                try:
                    p_actual = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                    valor_ticker = row['Cantidad'] * p_actual
                    valor_portafolio_hoy += valor_ticker
                    st.write(f"**{ticker}:** ${p_actual:,.2f} (Total: ${valor_ticker:,.2f})")
                except:
                    continue
        
        st.divider()
        meta_dinamica = st.number_input("🎯 Meta de Patrimonio", value=10000, step=500)

    # --- 3. CÁLCULO DE PATRIMONIO REAL ---
    # Efectivo (Suma de lo que tienes en 'Movimientos' como Ahorros/Ingresos menos Gastos Personales)
    ingresos = movs[movs['Tipo'] == 'Ingreso']['Monto'].sum()
    gastos_p = movs[movs['Tipo'] == 'Gasto']['Monto'].sum() # Solo gastos que no son de negocio
    efectivo_liquido = ingresos - gastos_p
    
    # Cuentas por Cobrar (De la pestaña Creditos)
    total_cobrar = creditos['saldo pendiente'].sum() if 'saldo pendiente' in creditos.columns else 0
    
    # Patrimonio Total = Liquidez + Acciones a valor de mercado + Deudas de clientes
    patrimonio_total = efectivo_liquido + valor_portafolio_hoy + total_cobrar

    # --- 4. DASHBOARD DE MÉTRICAS (SOLO LAS TUYAS) ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    m2.metric("Mis Acciones", f"${valor_portafolio_hoy:,.2f}")
    m3.metric("Liquidez", f"${efectivo_liquido:,.2f}")
    m4.metric("Por Cobrar", f"${total_cobrar:,.2f}")

    # --- 5. PANELES DE CONTROL ---
    tab1, tab2, tab3 = st.tabs(["📝 Gestión de Datos", "💹 Proyección", "🤖 IA Xvortice"])

    with tab1:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.subheader("Tus Acciones (Consolidadas)")
            st.table(inv_resumen)
        with col_b:
            st.subheader("Próximos Cobros")
            if 'Cliente' in creditos.columns:
                st.dataframe(creditos[['Cliente', 'saldo pendiente']].tail(10), use_container_width=True)

    with tab2:
        st.subheader("💰 Simulador de Interés Compuesto")
        # Simula tu patrimonio real creciendo en el tiempo
        años = st.slider("Años de espera", 1, 30, 5)
        tasa = st.slider("Rendimiento Anual Esperado (%)", 1, 20, 10)
        futuro = patrimonio_total * (1 + (tasa/100))**años
        st.success(f"Daniel, manteniendo tu patrimonio actual, en {años} años tendrías: ${futuro:,.2f}")

    with tab3:
        st.subheader("🤖 Analista Financiero Personal")
        if st.text_input("¿Qué quieres saber de tu dinero?"):
            cobrar_pct = (total_cobrar / patrimonio_total) * 100
            st.info(f"Daniel, tienes un {cobrar_pct:.1f}% de tu patrimonio 'en la calle' (por cobrar). Es un activo fuerte, pero recuerda la liquidez.")

except Exception as e:
    st.error(f"Error al leer el Excel: {e}. Revisa que los nombres de las columnas coincidan con tus fotos.")
