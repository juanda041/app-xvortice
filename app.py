import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# Función de carga ultra-segura
def cargar_datos(hoja):
    try:
        return conn.read(worksheet=hoja, ttl="1s")
    except:
        return pd.DataFrame()

# Cargar hojas
df_p = cargar_datos("Portafolio")
df_m = cargar_datos("Movimientos")
df_c = cargar_datos("Creditos")

# --- SIDEBAR ---
st.sidebar.title("🏛️ Xvortice Corp")
mod = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Inversiones", "Créditos", "Registro"])

# --- LÓGICA DE PRECIOS ---
def get_live_prices(tickers):
    d = {}
    for t in tickers:
        if t == "CASH" or pd.isna(t): continue
        try:
            d[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
        except:
            d[t] = 0
    return d

# --- MODULO 1: ESTADO PATRIMONIAL ---
if mod == "Estado Patrimonial":
    st.header("📊 Resumen de Patrimonio")
    
    if not df_p.empty:
        # Limpieza de datos
        df_p['Cantidad'] = pd.to_numeric(df_p['Cantidad'], errors='coerce').fillna(0)
        
        # Separar acciones de liquidez
        acciones = df_p[df_p['Ticker'] != 'CASH'].copy()
        cash_hapi = df_p[df_p['Ticker'] == 'CASH']['Cantidad'].sum()
        
        # Obtener precios y calcular
        precios = get_live_prices(acciones['Ticker'].unique())
        acciones['Precio'] = acciones['Ticker'].map(precios)
        acciones['Subtotal'] = acciones['Cantidad'] * acciones['Precio']
        
        # Crear tabla para gráfica
        resumen = acciones[['Ticker', 'Subtotal']].copy()
        if cash_hapi > 0:
            resumen = pd.concat([resumen, pd.DataFrame([{"Ticker": "CASH", "Subtotal": cash_hapi}])])
        
        total_bolsa = resumen['Subtotal'].sum()
        
        # Métricas
        st.metric("Total en Bolsa (Live)", f"${total_bolsa:,.2f}")
        
        # Gráfica
        fig = px.pie(resumen, values='Subtotal', names='Ticker', hole=0.5, title="Mi Portafolio")
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de %
        resumen['%'] = (resumen['Subtotal'] / total_bolsa * 100).map("{:.2f}%".format)
        st.table(resumen)
    else:
        st.warning("No hay datos en la hoja 'Portafolio'")

# --- MODULO 2: INVERSIONES ---
elif mod == "Inversiones":
    st.header("📈 Gestión de Activos")
    st.write("Datos actuales en Excel:")
    st.dataframe(df_p)
    
    with st.expander("Añadir/Sumar"):
        with st.form("add_inv"):
            t = st.text_input("Ticker").upper()
            c = st.number_input("Cantidad a sumar", format="%.5f")
            if st.form_submit_button("Guardar"):
                # Aquí podrías poner la lógica de suma si quieres, 
                # pero primero asegúrate que esto cargue.
                st.write("Función de guardado lista.")

# --- MODULO 3: CRÉDITOS ---
elif mod == "Créditos":
    st.header("💸 Cuentas por Cobrar")
    st.dataframe(df_c)

# --- MODULO 4: REGISTRO ---
elif mod == "Registro":
    st.header("📝 Movimientos")
    st.dataframe(df_m)
