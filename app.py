import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN Y CARGA DE DATOS ---
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

# Carga global de hojas
df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos")

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
st.sidebar.markdown("---")
meta_ahorro = st.sidebar.number_input("🎯 Meta de Patrimonio ($)", value=5000, step=500)
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO 1: ESTADO PATRIMONIAL (CON ANALISTA IA) ---
if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Bolsa)")
    
    # Cálculo Efectivo
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    # Cálculo Inversiones Live
    valor_inv = 0
    if not df_port.empty:
        t_list = df_port['Ticker'].unique().tolist()
        p_vivos = obtener_precios_vivos(t_list)
        df_port['Live Price'] = df_port['Ticker'].map(p_vivos)
        valor_inv = (pd.to_numeric(df_port['Cantidad']) * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ahorros (Cash)", f"${efectivo:,.2f}")
    c2.metric("Portafolio Live", f"${valor_inv:,.2f}")
    c3.metric("PATRIMONIO TOTAL", f"${cap_total:,.2f}", delta=f"{cap_total - meta_ahorro:,.2f} vs Meta")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total < meta_ahorro:
        st.warning(f"Juan, estás al **{cap_total/meta_ahorro*100:.1f}%** de tu meta de ${meta_ahorro:,.0f}. El mercado dice que tu portafolio vale ${valor_inv:,.2f}. ¡Sigue así!")
    else:
        st.success(f"¡Meta superada! Patrimonio consolidado: **${cap_total:,.2f}**. Estrategia sugerida: Rebalanceo y aumento de meta a $10,000.")

# --- MÓDULO 2: REGISTRO SEPARADO (INGRESOS vs GASTOS) ---
elif menu == "Registro de Operaciones":
    st.header("📝 Gestión de Movimientos")
    tab1, tab2 = st.tabs(["💰 Registrar Ingreso", "💸 Registrar Gasto"])
    
    with tab1:
        with st.form("form_ingresos"):
            f_cat_i = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta Xvortice", "Entrada de Capital"])
            f_monto_i = st.number_input("Monto ($)", min_value=0.0)
            f_nota_i = st.text_input("Nota")
            if st.form_submit_button("Guardar Ingreso"):
                n_i = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Ingreso", "Categoria": f_cat_i, "Monto": f_monto_i, "Comentario": f_nota_i}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, n_i], ignore_index=True))
                st.cache_data.clear()
                st.success("Ingreso registrado.")

    with tab2:
        with st.form("form_gastos"):
            f_cat_g = st.selectbox("Categoría", ["Versa", "Comida", "Hapi (Inversión)", "Gastos Operativos", "Otros Gastos"])
            f_monto_g = st.number_input("Monto ($)", min_value=0
