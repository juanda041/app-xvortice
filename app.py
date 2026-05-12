import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN Y CARGA ---
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
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Inversiones", "Gestión de Créditos", "Registro de Operaciones", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- ESTADO PATRIMONIAL (CON IA) ---
if menu == "Estado Patrimonial":
    st.header("📊 Resumen de Capital")
    
    # Cálculo Efectivo
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
    gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    efectivo = ingresos - gastos
    
    # Cálculo Inversiones
    valor_inv = 0
    if not df_port.empty:
        t_list = df_port['Ticker'].unique().tolist()
        p_vivos = obtener_precios_vivos(t_list)
        df_port['Live Price'] = df_port['Ticker'].map(p_vivos)
        valor_inv = (pd.to_numeric(df_port['Cantidad']) * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    
    c1, c2 = st.columns(2)
    c1.metric("Capital Neto Real", f"${cap_total:,.2f}")
    c2.metric("Meta 2026", f"${meta_ahorro:,.2f}")
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    # --- 🤖 ANALISTA IA ---
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total >= meta_ahorro:
        st.success(f"¡Meta de ${meta_ahorro:,.0f} alcanzada! Vamos por el siguiente nivel.")
    else:
        st.warning(f"Faltan ${meta_ahorro - cap_total:,.2f} para la meta. ¡Sigue así!")

# --- INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi")
    with st.expander("➕ Añadir compra", expanded=False):
        with st.form("f_inv"):
            f_tick = st.text_input("Ticker (Ej: VOO)")
            f_cant = st.number_input("Cantidad", step=0.0001)
            f_p_compra = st.number_input("Precio de Compra")
            if st.form_submit_button("Guardar"):
                nueva = pd.DataFrame([{"Ticker": f_tick.upper(), "Cantidad": f_cant, "Precio de Compra": f_p_compra}])
                df_up = pd.concat([df_port, nueva], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_port, use_container_width=True)

# --- GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Créditos por Cobrar")
    st.dataframe(df_cred, use_container_width=True)

# --- REGISTRO DE OPERACIONES (CAMBIO AQUÍ) ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Ingresos/Gastos")
    with st.form("form_mov_v45"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        # Aquí añadimos las categorías que faltaban
        f_cat = st.selectbox("Categoría", [
            "Ahorros", 
            "Bonos", 
            "Versa", 
            "Comida", 
            "Hapi", 
            "Gastos Operativos", 
            "Otros Gastos"
        ])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_comentario = st.text_input("Comentario (Opcional)")
        
        if st.form_submit_button("Guardar en Excel"):
            n_m = pd.DataFrame([{
                "Fecha": str(pd.Timestamp.now().date()), 
                "Tipo": f_tipo, 
                "Categoria": f_cat, 
                "Monto": f_monto,
                "Comentario": f_comentario
            }])
            df_up_m = pd.concat([df_mov, n_m], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.cache_data.clear()
            st.success(f"✅ Registrado como {f_cat}")

# --- INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Proyección")
    p = st.number_input("Capital Inicial", value=4000.0)
    t = st.slider("Años", 1, 30, 10)
    st.write(f"Resultado estimado: **${p * (1.10**t):,.2f}**")
