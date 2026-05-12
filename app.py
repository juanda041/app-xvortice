import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1)
def cargar(hoja):
    try: 
        return conn.read(worksheet=hoja, ttl="0")
    except: 
        return pd.DataFrame()

@st.cache_data(ttl=600)
def precios_vivos(ticks):
    p_dict = {}
    for t in ticks:
        if str(t).upper() == "CASH": continue
        try:
            val = yf.Ticker(str(t).strip().upper()).history(period="1d")['Close'].iloc[-1]
            p_dict[t] = val
        except: p_dict[t] = None
    return p_dict

# Carga de datos
df_m = cargar("Movimientos")
df_p = cargar("Portafolio")
df_c = cargar("Creditos")

# --- MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
meta = st.sidebar.number_input("🎯 Meta Patrimonio ($)", value=10000, step=500)
mod = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Registro", "Inversiones", "Créditos", "Proyección"])

# --- 1. ESTADO PATRIMONIAL ---
if mod == "Estado Patrimonial":
    st.header("📊 Patrimonio Real")
    df_m['Monto'] = pd.to_numeric(df_m['Monto'], errors='coerce').fillna(0)
    cash_mov = df_m[df_m['Tipo']=='Ingreso']['Monto'].sum() - df_m[df_m['Tipo']=='Gasto']['Monto'].sum()
    
    v_inv = 0
    if not df_p.empty:
        # Procesamiento de Portafolio
        df_p['Cantidad'] = pd.to_numeric(df_p['Cantidad'], errors='coerce').fillna(0)
        df_acciones = df_p[df_p['Ticker'] != 'CASH'].copy()
        df_efectivo = df_p[df_p['Ticker'] == 'CASH'].copy()
        
        # Precios en vivo
        tk_list = df_acciones['Ticker'].dropna().unique().tolist()
        v_dict = precios_vivos(tk_list)
        df_acciones['Precio_Live'] = df_acciones['Ticker'].map(v_dict)
        
        # Calcular valor actual por fila
        df_acciones['Valor_Total'] = df_acciones['Cantidad'] * df_acciones['Precio_Live'].fillna(0)
        
        # Valor de la liquidez en Hapi
        cash_hapi = df_efectivo['Cantidad'].sum()
        
        # Unimos todo para las gráficas
        df_resumen = df_acciones[['Ticker', 'Valor_Total']].copy()
        if cash_hapi > 0:
            df_resumen = pd.concat([df_resumen, pd.DataFrame([{"Ticker": "CASH", "Valor_Total": cash_hapi}])])
        
        v_inv = df_resumen['Valor_Total'].sum()
        
        # Calcular porcentajes
        if v_inv > 0:
            df_resumen['%'] = (df_resumen['Valor_Total'] / v_inv) * 100

    total = cash_mov + v_inv
    col1, col2, col3 = st.columns(3)
    col1.metric("Efectivo (Otros)", f"${cash_mov:,.2f}")
    col2.metric("Bolsa + Liquidez", f"${v_inv:,.2f}")
    col3.metric("TOTAL NETO", f"${total:,.2f}")
    st.progress(min(total/meta, 1.0) if meta > 0 else 0)
    
    # --- SECCIÓN DE GRÁFICAS ---
    st.markdown("---")
    c_graf1, c_graf2 = st.columns([1, 1])
    
    with c_graf1:
        st.subheader("🥧 Distribución del Portafolio")
        if v_inv > 0:
            fig = px.pie(df_resumen, values='Valor_Total', names='Ticker', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
    
    with c_graf2:
        st.subheader("📈 Porcentaje por Activo")
        if v_inv > 0:
            # Formateamos para que se vea limpio
            df_mostrar = df_resumen.copy()
            df_mostrar['Valor_Total'] = df_mostrar['Valor_Total'].map("${:,.2f}".format)
            df_mostrar['%'] = df_mostrar['%'].map("{:,.2f}%".format)
            st.table(df_mostrar.sort_values(by='%', ascending=False))

    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if total < meta:
        st.warning(f"Daniel, faltan ${meta-total:,.2f} para tu meta. Tu acción con más peso es {df_resumen.sort_values(by='%', ascending=False).iloc[0]['Ticker']}.")

# --- 2. REGISTRO ---
elif mod == "Registro":
    st.header("📝 Gestión de Movimientos")
    i_tab, g_tab = st.tabs(["💰 Ingresos", "💸 Gastos"])
