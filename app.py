import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import yfinance as yf # El motor de la bolsa

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

# Función mágica para traer precios reales
@st.cache_data(ttl=600) # El precio se actualiza cada 10 min para no saturar
def obtener_precios_vivos(tickers):
    precios = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Traemos el último precio de cierre
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
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio en Tiempo Real")
    
    if not df_mov.empty:
        # Ahorros en efectivo
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        # Valor de Inversiones (Bolsa en vivo)
        valor_mercado_total = 0
        if not df_port.empty:
            tickers = df_port['Ticker'].unique().tolist()
            precios_vivos = obtener_precios_vivos(tickers)
            
            # Calculamos el valor actual
            df_port['Precio_Actual'] = df_port['Ticker'].map(precios_vivos)
            df_port['Valor_Actual'] = df_port['Cantidad'] * df_port['Precio_Actual']
            valor_mercado_total = df_port['Valor_Actual'].sum()

        capital_total = efectivo + valor_mercado_total
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Efectivo", f"${efectivo:,.2f}")
        c2.metric("Inversiones (Hoy)", f"${valor_mercado_total:,.2f}")
        c3.metric("PATRIMONIO TOTAL", f"${capital_total:,.2f}")
        
        st.progress(min(capital_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        # --- ANALISTA IA ---
        st.markdown("---")
        st.info(f"🤖 **Analista IA:** Juan, con el mercado actual, tu patrimonio es de ${capital_total:,.2f}. El {valor_mercado_total/capital_total*100 if capital_total > 0 else 0:.1f}% de tu fuerza financiera está en la bolsa.")

# --- MÓDULO INVERSIONES (CON PRECIOS EN VIVO) ---
elif menu == "Inversiones":
    st.header("📈 Mi Portafolio (Market Live)")
    if not df_port.empty:
        tickers = df_port['Ticker'].unique().tolist()
        precios = obtener_precios_vivos(tickers)
        df_port['Precio Mercado'] = df_port['Ticker'].map(precios)
        df_port['Ganancia/Perdida %'] = ((df_port['Precio Mercado'] - df_port['Costo Promedio']) / df_port['Costo Promedio']) * 100
        
        st.dataframe(df_port[['Ticker', 'Cantidad', 'Costo Promedio', 'Precio Mercado', 'Ganancia/Perdida %']], use_container_width=True)
    else:
        st.info("Añade acciones en tu Excel para verlas aquí.")

# --- Módulos de Registro y Créditos (Iguales para seguridad) ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro")
    with st.form("f_reg"):
        tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta", "Versa", "Comida"])
        monto = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": tipo, "Categoria": cat, "Monto": monto}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("Registrado.")

elif menu == "Gestión de Créditos":
    st.header("💸 Créditos")
    st.dataframe(df_cred)
