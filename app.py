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
        # Forzamos la lectura sin caché para que veas tus datos del Excel siempre
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except Exception as e:
        st.error(f"Error al conectar con la hoja {nombre_hoja}: {e}")
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

# Carga de datos
df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos")

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
# Así debe quedar para que siempre inicie en 10,000:
meta_ahorro = st.sidebar.number_input("🎯 Meta de Patrimonio ($)", value=10000, step=500)
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Bolsa)")
    
    # Cálculo Efectivo
    efectivo = 0
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        efectivo = ingresos - gastos
    
    # Cálculo Inversiones
    valor_inv = 0
    if not df_port.empty:
        tickers = df_port['Ticker'].dropna().unique().tolist()
        precios_vivos = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios_vivos)
        df_port['Cantidad'] = pd.to_numeric(df_port['Cantidad'], errors='coerce').fillna(0)
        valor_inv = (df_port['Cantidad'] * df_port['Live Price'].fillna(0)).sum()

    cap_total = efectivo + valor_inv
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo", f"${efectivo:,.2f}")
    c2.metric("Inversiones (Live)", f"${valor_inv:,.2f}")
    c3.metric("PATRIMONIO TOTAL", f"${cap_total:,.2f}")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total < meta_ahorro:
        st.warning(f"Juan, estás al **{cap_total/meta_ahorro*100:.1f}%** de tu meta. Faltan **${meta_ahorro - cap_total:,.2f}**.")
    else:
        st.success(f"¡Meta de ${meta_ahorro:,.0f} superada! Excelente gestión.")

elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Movimientos")
    t1, t2 = st.tabs(["💰 Registrar Ingreso", "💸 Registrar Gasto"])
    
    with t1:
        with st.form("f_ing", clear_on_submit=True):
            cat_i = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta Xvortice", "Capital"])
            mon_i = st.number_input("Monto ($)", min_value=0.0)
            not_i = st.text_input("Nota")
            if st.form_submit_button("Guardar Ingreso"):
                nueva = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Ingreso", "Categoria": cat_i, "Monto": mon_i, "Comentario": not_i}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, nueva], ignore_index=True))
                st.cache_data.clear()
                st.success("Ingreso Guardado")
                st.rerun()

    with t2:
        with st.form("f_gas", clear_on_submit=True):
            cat_g = st.selectbox("Categoría", ["Versa", "Comida", "Hapi", "Gastos Operativos", "Otros Gastos"])
            mon_g = st.number_input("Monto ($)", min_value=0.0)
            not_g = st.text_input("Nota")
            if st.form_submit_button("Guardar Gasto"):
                nueva = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": "Gasto", "Categoria": cat_g, "Monto": mon_g, "Comentario": not_g}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_mov, nueva], ignore_index=True))
                st.cache_data.clear()
                st.error("Gasto Guardado")
                st.rerun()

elif menu == "Inversiones":
    st.header("📈 Mi Portafolio")
    # Formulario para añadir
    with st.expander("➕ Añadir compra al Portafolio"):
        with st.form("f_inv_new"):
            col1, col2 = st.columns(2)
            f_t = col1.text_input("Ticker (Ej: VOO)")
            f_c = col2.number_input("Cantidad", step=0.0001)
            f_pc = col1.number_input("Precio de Compra ($)")
            if st.form_submit_button("Añadir a Bolsa"):
                nueva = pd.DataFrame([{"Ticker": f_t.upper(), "Cantidad": f_c, "Precio de Compra": f_pc}])
                conn.update(worksheet="Portafolio", data=pd.concat([df_port, nueva], ignore_index=True))
                st.cache_data.clear()
                st.rerun()

    if not df_port.empty:
        # Precios en vivo
        t_list = df_port['Ticker'].dropna().unique().tolist()
        precios = obtener_precios_vivos(t_list)
        df_port['Precio Actual'] = df_port['Ticker'].map(precios)
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("No hay datos en la hoja de Portafolio.")

elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Registrar nuevo crédito"):
        with st.form("f_cred_new"):
            f_cli = st.text_input("Nombre del Cliente")
            f_sal = st.number_input("Saldo Pendiente ($)", min_value=0.0)
            if st.form_submit_button("Registrar Crédito"):
                nueva = pd.DataFrame([{"Cliente": f_cli, "Saldo pendiente": f_sal}])
                conn.update(worksheet="Creditos", data=pd.concat([df_cred, nueva], ignore_index=True))
                st.cache_data.clear()
                st.rerun()
    
    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)
    else:
        st.info("No hay créditos pendientes registrados.")

elif menu == "Interés Compuesto":
    st.header("📈 Proyección a Futuro")
    p = st.number_input("Capital Actual ($)", value=4000.0)
    a = st.slider("Años de inversión", 1, 30, 10)
    resultado = p * (1.10**a)
    st.success(f"### Estimación a {a} años (10% anual): ${resultado:,.2f}")
