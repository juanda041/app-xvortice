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
        if not t or pd.isna(t): continue
        try:
            stock = yf.Ticker(str(t).strip().upper())
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
# Meta fijada en 10,000 como pediste
meta_ahorro = st.sidebar.number_input("🎯 Meta de Patrimonio ($)", value=10000, step=500)
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- ESTADO PATRIMONIAL + IA ---
if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Bolsa)")
    
    # Cálculo Efectivo
    efectivo = 0
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    # Cálculo Inversiones Live
    valor_inv = 0
    if not df_port.empty:
        t_list = df_port['Ticker'].dropna().unique().tolist()
        p_vivos = obtener_precios_vivos(t_list)
        df_port['Live Price'] = df_port['Ticker'].map(p_vivos)
        df_port['Cantidad'] = pd.to_numeric(df_port['Cantidad'], errors='coerce').fillna(0)
        valor_inv = (df_port['Cantidad'] * df_port['Live Price'].fillna(0)).sum()

    cap_total = efectivo + valor_inv
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo", f"${efectivo:,.2f}")
    c2.metric("Portafolio Bolsa", f"${valor_inv:,.2f}")
    c3.metric("TOTAL NETO", f"${cap_total:,.2f}")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total < meta_ahorro:
        st.warning(f"Juan, vas por el **{cap_total/meta_ahorro*100:.1f}%** del camino. Faltan **${meta_ahorro - cap_total:,.2f}** para el primer gran hito de Xvortice.")
    else:
        st.success(f"¡Meta de ${meta_ahorro:,.0f} superada! El interés compuesto empezará a trabajar más fuerte ahora.")

# --- REGISTRO SEPARADO (INGRESOS / GASTOS) ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Movimientos")
    t1, t2 = st.tabs(["💰 Registrar Ingreso", "💸 Registrar Gasto"])
    
    with t1:
        with st.form("form_i", clear_on_submit=True):
            cat_i = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta Xvortice", "Capital"])
            mon_i = st.number_input("Monto ($)", min_value=0.0)
            not_i = st.text_input("Nota / Detalle")
            if st.form_submit_button("Confirmar Ingreso"):
                n_i = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Ingreso", "Categoria": cat_i, "Monto": mon_i, "Comentario": not_i}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, n_i], ignore_index=True))
                st.cache_data.clear()
                st.success(f"Ingreso de ${mon_i} guardado.")
                st.rerun()

    with t2:
        with st.form("form_g", clear_on_submit=True):
            cat_g = st.selectbox("Categoría", ["Versa", "Comida", "Hapi", "Gastos Operativos", "Otros Gastos"])
            mon_g = st.number_input("Monto ($)", min_value=0.0)
            not_g = st.text_input("Nota / Detalle")
            if st.form_submit_button("Confirmar Gasto"):
                n_g = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Gasto", "Categoria": cat_g, "Monto": mon_g, "Comentario": not_g}])
                conn.update(works
