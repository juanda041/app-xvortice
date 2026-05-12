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
meta_ahorro = st.sidebar.number_input("🎯 Meta 2026 ($)", value=5000, step=500)
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Inversiones", "Gestión de Créditos", "Registro de Operaciones", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO INVERSIONES (CON NUEVO CAMPO) ---
if menu == "Inversiones":
    st.header("📈 Portafolio Hapi (En Vivo)")
    
    # Formulario para escribir (SIEMPRE VISIBLE)
    with st.expander("➕ Añadir nueva compra al Portafolio", expanded=True):
        with st.form("form_inv_new"):
            c1, c2, c3 = st.columns(3)
            f_tick = c1.text_input("Ticker (Ej: VOO, NVDA)")
            f_nom = c2.text_input("Nombre (Ej: S&P 500)")
            f_cant = c3.number_input("Cantidad", min_value=0.0, step=0.0001)
            
            c4, c5 = st.columns(2)
            f_p_compra = c4.number_input("Precio de Compra Individual ($)", min_value=0.0)
            f_p_promedio = c5.number_input("Costo Promedio ($)", min_value=0.0)
            
            if st.form_submit_button("Guardar en Portafolio"):
                nueva_fila = pd.DataFrame([{
                    "Ticker": f_tick.upper(),
                    "Nombre": f_nom,
                    "Cantidad": f_cant,
                    "Precio de Compra": f_p_compra,
                    "Costo Promedio": f_p_promedio
                }])
                df_up_i = pd.concat([df_port, nueva_fila], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_i)
                st.cache_data.clear()
                st.rerun()

    if not df_port.empty:
        # Traer precios de la bolsa
        tickers = df_port['Ticker'].unique().tolist()
        precios = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios)
        
        # Mostrar tabla
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("El portafolio está vacío.")

# --- MÓDULO CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Registrar nuevo crédito", expanded=True):
        with st.form("form_cred_new"):
            f_cli = st.text_input("Cliente")
            f_prod = st.text_input("Producto")
            f_sal = st.number_input("Saldo ($)", min_value=0.0)
            if st.form_submit_button("Registrar"):
                n_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, n_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_cred, use_container_width=True)

# --- MÓDULO ESTADO PATRIMONIAL ---
elif menu == "Estado Patrimonial":
    st.header("📊 Resumen de Capital")
    
    # Cálculo Efectivo
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    # Cálculo Inversiones
    valor_inv = 0
    if not df_port.empty:
        tickers = df_port['Ticker'].unique().tolist()
        precios = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios)
        valor_inv = (df_port['Cantidad'] * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    
    c1, c2 = st.columns(2)
    c1.metric("Capital Neto Real", f"${cap_total:,.2f}")
    c2.metric("Meta 2026", f"${meta_ahorro:,.2f}")
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

# --- MÓDULO REGISTRO ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento")
    with st.form("form_mov_new"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Comentario")
        if st.form_submit_button("Guardar en Excel"):
            n_m = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": f_tipo, "Monto": f_monto, "Comentario": f_coment}])
            df_up_m = pd.concat([df_mov, n_m], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.cache_data.clear()
            st.success("¡Guardado!")

# --- MÓDULO INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Proyección de Interés Compuesto")
    c1, c2 = st.columns(2)
    p = c1.number_input("Capital Inicial", value=4000.0)
    t = c2.slider("Años", 1, 30, 10)
    r = 0.10 # 10% anual
    final = p * (1 + r)**t
    st.success(f"### Estimación a {t} años: ${final:,.2f}")
