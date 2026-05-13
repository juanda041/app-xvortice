import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Gestión Patrimonial")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. CARGA DE DATOS
    movs = conn.read(worksheet="Movimientos", ttl=0).dropna(how='all')
    portafolio = conn.read(worksheet="Portafolio", ttl=0).dropna(how='all')
    creditos = conn.read(worksheet="Creditos", ttl=0).dropna(how='all')

    # Limpieza estándar de nombres de columnas (quitar espacios y poner minúsculas para el código)
    movs.columns = [str(c).strip() for c in movs.columns]
    portafolio.columns = [str(c).strip() for c in portafolio.columns]
    creditos.columns = [str(c).strip() for c in creditos.columns]

    # --- 2. LÓGICA DE INVERSIONES CONSOLIDADAS ---
    # Buscamos la columna de Ticker y Cantidad sin importar mayúsculas
    col_ticker = [c for c in portafolio.columns if 'ticker' in c.lower()][0]
    col_cant = [c for c in portafolio.columns if 'cant' in c.lower()][0]
    
    inv_resumen = portafolio.groupby(col_ticker)[col_cant].sum().reset_index()
    
    valor_portafolio_hoy = 0
    with st.sidebar:
        st.header("📊 Mercado en Vivo")
        for index, row in inv_resumen.iterrows():
            t = row[col_ticker]
            if t.upper() != "CASH" and t != "":
                try:
                    p_actual = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
                    valor_portafolio_hoy += (row[col_cant] * p_actual)
                    st.write(f"**{t}:** ${p_actual:,.2f}")
                except: continue
        st.divider()
        meta_dinamica = st.number_input("🎯 Meta", value=10000)

    # --- 3. CÁLCULO DE PATRIMONIO REAL ---
    # Buscamos columnas de saldo en créditos (Evita el error que te salió)
    col_saldo = [c for c in creditos.columns if 'saldo' in c.lower() or 'pendiente' in c.lower()]
    total_cobrar = creditos[col_saldo[0]].sum() if col_saldo else 0
    
    # Liquidez (Ingresos - Gastos Personales)
    col_tipo = [c for c in movs.columns if 'tipo' in c.lower()][0]
    col_monto = [c for c in movs.columns if 'monto' in c.lower()][0]
    ingresos = movs[movs[col_tipo].str.contains('Ingreso', case=False, na=False)][col_monto].sum()
    gastos = movs[movs[col_tipo].str.contains('Gasto|Egreso', case=False, na=False)][col_monto].sum()
    liquidez = ingresos - gastos

    patrimonio_total = liquidez + valor_portafolio_hoy + total_cobrar

    # --- 4. DASHBOARD ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PATRIMONIO TOTAL", f"${patrimonio_total:,.2f}")
    m2.metric("Portafolio Actual", f"${valor_portafolio_hoy:,.2f}")
    m3.metric("Efectivo/Liquidez", f"${liquidez:,.2f}")
    m4.metric("Por Cobrar", f"${total_cobrar:,.2f}")

    # --- 5. PANELES ---
    t1, t2, t3 = st.tabs(["📝 Ver y Editar Datos", "💹 Proyección", "🤖 IA"])

    with t1:
        st.subheader("Registros en Google Sheets")
        st.info("Para editar, haz los cambios en tu Excel y actualiza esta página.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Créditos activos:**")
            st.dataframe(creditos, use_container_width=True)
        with col_b:
            st.write("**Movimientos:**")
            st.dataframe(movs.tail(10), use_container_width=True)

    with t2:
        años = st.slider("Años", 1, 30, 5)
        futuro = patrimonio_total * (1 + (0.10))**años
        st.success(f"Proyección a {años} años (10% anual): ${futuro:,.2f}")

    with t3:
        if st.text_input("Consultar a Xvortice:"):
            st.write(f"Daniel, tu patrimonio de ${patrimonio_total:,.2f} está bien distribuido.")

except Exception as e:
    st.error(f"Error de lectura: {e}. Asegúrate de que las pestañas se llamen Movimientos, Portafolio y Creditos.")
