import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def cargar_datos(nombre_hoja):
    try:
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def obtener_precios_vivos(tickers):
    precios = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            precio = stock.history(period="1d")['Close'].iloc[-1]
            precios[t] = precio
        except:
            precios[t] = None
    return precios

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos")

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
st.sidebar.markdown("---")
meta_ahorro = st.sidebar.number_input("🎯 Meta de Patrimonio ($)", value=5000, step=500)
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Inversiones", "Gestión de Créditos", "Registro de Operaciones", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Bolsa)")
    
    # Cálculos
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    valor_inv = 0
    if not df_port.empty:
        tickers = df_port['Ticker'].unique().tolist()
        precios_vivos = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios_vivos)
        valor_inv = (df_port['Cantidad'] * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    
    # Métricas Visuales
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo / Ahorros", f"${efectivo:,.2f}")
    c2.metric("Valor en Bolsa", f"${valor_inv:,.2f}")
    c3.metric("PATRIMONIO TOTAL", f"${cap_total:,.2f}")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    # --- 🤖 SECCIÓN DEL ANALISTA IA (EL CEREBRO) ---
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    
    # Lógica de consejos de la IA
    if cap_total < meta_ahorro:
        faltante = meta_ahorro - cap_total
        st.warning(f"Juan, actualmente estás al **{cap_total/meta_ahorro*100:.1f}%** de tu meta. Te faltan **${faltante:,.2f}** para alcanzar los ${meta_ahorro:,.0f}. ¡Es momento de optimizar los gastos del Versa o buscar un bono extra!")
    else:
        st.success(f"¡Felicidades, Juan! Has superado la meta de ${meta_ahorro:,.0f}. Tu patrimonio actual es de **${cap_total:,.2f}**. Es hora de subir la meta a $10,000 y dejar que el interés compuesto haga el resto.")
    
    st.info("💡 **Tip del Analista:** El mercado siempre se mueve. No te asustes si el valor en bolsa baja un poco hoy, recuerda que tu estrategia es a largo plazo.")

elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi")
    with st.expander("➕ Añadir nueva compra", expanded=False):
        with st.form("f_inv"):
            f_tick = st.text_input("Ticker (Ej: VOO)")
            f_cant = st.number_input("Cantidad", min_value=0.0, step=0.0001)
            f_p_compra = st.number_input("Precio de Compra")
            if st.form_submit_button("Guardar"):
                nueva = pd.DataFrame([{"Ticker": f_tick.upper(), "Cantidad": f_cant, "Precio de Compra": f_p_compra}])
                df_up = pd.concat([df_port, nueva], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_port, use_container_width=True)

elif menu == "Gestión de Créditos":
    st.header("💸 Créd
