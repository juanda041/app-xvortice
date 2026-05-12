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
meta_ahorro = st.sidebar.number_input("🎯 Meta de Patrimonio ($)", value=5000, step=500)
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real")
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    valor_inv = 0
    if not df_port.empty:
        t_list = df_port['Ticker'].unique().tolist()
        p_vivos = obtener_precios_vivos(t_list)
        df_port['Live Price'] = df_port['Ticker'].map(p_vivos)
        valor_inv = (pd.to_numeric(df_port['Cantidad']) * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo", f"${efectivo:,.2f}")
    c2.metric("Inversiones", f"${valor_inv:,.2f}")
    c3.metric("TOTAL", f"${cap_total:,.2f}")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total < meta_ahorro:
        st.warning(f"Juan, faltan ${meta_ahorro - cap_total:,.2f} para la meta. ¡Sigue adelante!")
    else:
        st.success("¡Meta alcanzada! Xvortice está creciendo.")

elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Movimientos")
    t1, t2 = st.tabs(["💰 Ingreso", "💸 Gasto"])
    
    with t1:
        with st.form("f_ing"):
            cat_i = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta Xvortice", "Capital"])
            mon_i = st.number_input("Monto ($)", min_value=0.0)
            not_i = st.text_input("Nota")
            if st.form_submit_button("Guardar Ingreso"):
                n_i = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Ingreso", "Categoria": cat_i, "Monto": mon_i, "Comentario": not_i}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, n_i], ignore_index=True))
                st.cache_data.clear()
                st.success("Registrado.")

    with t2:
        with st.form("f_gas"):
            cat_g = st.selectbox("Categoría", ["Versa", "Comida", "Hapi", "Gastos Operativos", "Otros Gastos"])
            mon_g = st.number_input("Monto ($)", min_value=0.0)
            not_g = st.text_input("Nota")
            if st.form_submit_button("Guardar Gasto"):
                n_g = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Gasto", "Categoria": cat_g, "Monto": mon_g, "Comentario": not_g}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, n_g], ignore_index=True))
                st.cache_data.clear()
                st.error("Registrado.")

elif menu == "Inversiones":
    st.header("📈 Portafolio")
    if not df_port.empty:
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("Aún no hay activos.")

elif menu == "Gestión de Créditos":
    st.header("💸 Créditos")
    st.dataframe(df_cred, use_container_width=True)

elif menu == "Interés Compuesto":
    st.header("📈 Proyección")
    p_ini = st.number_input("Capital Inicial", value=4000.0)
    tiempo = st.slider("Años", 1, 30, 10)
    st.write(f"Resultado a 10% anual: **${p_ini * (1.10**tiempo):,.2f}**")
