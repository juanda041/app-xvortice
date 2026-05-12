import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import yfinance as yf

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIONES Y CACHÉ ---
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
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Inversiones", "Gestión de Créditos"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio en Tiempo Real")
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        valor_mercado_total = 0
        if not df_port.empty:
            tickers = df_port['Ticker'].unique().tolist()
            precios_vivos = obtener_precios_vivos(tickers)
            df_port['Precio_Actual'] = df_port['Ticker'].map(precios_vivos)
            valor_mercado_total = (df_port['Cantidad'] * df_port['Precio_Actual']).sum()

        capital_total = efectivo + valor_mercado_total
        c1, c2, c3 = st.columns(3)
        c1.metric("Efectivo", f"${efectivo:,.2f}")
        c2.metric("Inversiones (Market)", f"${valor_mercado_total:,.2f}")
        c3.metric("PATRIMONIO TOTAL", f"${capital_total:,.2f}")
        st.progress(min(capital_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        st.markdown("---")
        st.info(f"🤖 **Analista IA:** Juan, tu fuerza financiera es de ${capital_total:,.2f}. Mantener el ahorro biweekly es clave.")

elif menu == "Interés Compuesto":
    st.header("📈 Simulador de Interés Compuesto")
    col1, col2 = st.columns(2)
    p = col1.number_input("Capital Inicial ($)", value=4000.0)
    pmt = col1.number_input("Aporte Mensual ($)", value=200.0)
    t = col2.slider("Años", 1, 30, 10)
    r = col2.slider("Tasa Anual (%)", 1, 15, 10) / 100
    
    n = 12 # Compuesto mensualmente
    rate_m = r / n
    meses = t * n
    
    # Fórmula: FV = P(1 + r/n)^(nt) + PMT * [((1 + r/n)^(nt) - 1) / (r/n)]
    futuro_p = p * (1 + rate_m)**meses
    futuro_pmt = pmt * (((1 + rate_m)**meses - 1) / rate_m)
    total_f = futuro_p + futuro_pmt
    
    st.success(f"### Estimación en {t} años: ${total_f:,.2f}")
    st.write(f"Inversión total: ${p + (pmt * meses):,.2f} | Ganancia por interés: ${total_f - (p + (pmt * meses)):,.2f}")

elif menu == "Registro de Operaciones":
    st.header("📝 Registro")
    with st.form("f_reg"):
        tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta", "Versa", "Comida", "Hapi"])
        monto = st.number_input("Monto", min_value=0.0)
        desc = st.text_area("Comentario")
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": tipo, "Categoria": cat, "Monto": monto, "Comentario": desc}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("✅ Datos sincronizados.")

elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi")
    if not df_port.empty:
        tickers = df_port['Ticker'].unique().tolist()
        precios = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios)
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("No hay activos.")

elif menu == "Gestión de Créditos":
    st.header("💸 Créditos")
    st.dataframe(df_cred, use_container_width=True)
