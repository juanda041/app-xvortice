import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN Y CARGA DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def cargar_datos(nombre_hoja):
    try:
        # Leemos la hoja específica
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def obtener_precios_vivos(tickers):
    precios = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Trae el último precio de cierre
            precio = stock.history(period="1d")['Close'].iloc[-1]
            precios[t] = precio
        except:
            precios[t] = None
    return precios

# Carga inicial
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

# --- MÓDULO 1: ESTADO PATRIMONIAL (CON IA) ---
if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Bolsa)")
    
    # Cálculo de Efectivo (Ingresos - Gastos)
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
    gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    efectivo = ingresos - gastos
    
    # Cálculo de Inversiones (Precio en vivo)
    valor_inv = 0
    if not df_port.empty:
        tickers = df_port['Ticker'].unique().tolist()
        precios_vivos = obtener_precios_vivos(tickers)
        df_port['Live Price'] = df_port['Ticker'].map(precios_vivos)
        valor_inv = (df_port['Cantidad'] * df_port['Live Price']).sum()

    cap_total = efectivo + valor_inv
    
    # Métricas principales
    c1, c2, c3 = st.columns(3)
    c1.metric("Ahorros (Efectivo)", f"${efectivo:,.2f}")
    c2.metric("Portafolio (Hapi)", f"${valor_inv:,.2f}")
    c3.metric("PATRIMONIO TOTAL", f"${cap_total:,.2f}")
    
    st.progress(min(cap_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

    # --- 🤖 ANALISTA IA ---
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if cap_total < meta_ahorro:
        st.warning(f"Juan, estás al **{cap_total/meta_ahorro*100:.1f}%** de tu meta. Faltan **${meta_ahorro - cap_total:,.2f}**. ¡A seguir invirtiendo en esos ETFs!")
    else:
        st.success(f"¡Meta superada! Tu capital neto es de **${cap_total:,.2f}**. Es momento de actualizar objetivos.")

# --- MÓDULO 2: INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi (Live)")
    
    with st.expander("➕ Añadir compra al Portafolio", expanded=False):
        with st.form("form_inv"):
            col1, col2 = st.columns(2)
            f_tick = col1.text_input("Ticker (Ej: VOO, NVDA)")
            f_cant = col2.number_input("Cantidad de acciones", min_value=0.0, step=0.0001)
            f_p_compra = col1.number_input("Precio de Compra Individual ($)")
            f_p_prom = col2.number_input("Costo Promedio Actual ($)")
            
            if st.form_submit_button("Guardar"):
                nueva_f = pd.DataFrame([{
                    "Ticker": f_tick.upper(),
                    "Cantidad": f_cant,
                    "Precio de Compra": f_p_compra,
                    "Costo Promedio": f_p_prom
                }])
                df_up_i = pd.concat([df_port, nueva_f], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_i)
                st.cache_data.clear()
                st.rerun()

    if not df_port.empty:
        # Precios en vivo
        t_list = df_port['Ticker'].unique().tolist()
        p_vivos = obtener_precios_vivos(t_list)
        df_port['Precio Actual'] = df_port['Ticker'].map(p_vivos)
        df_port['Valor Actual'] = df_port['Cantidad'] * df_port['Precio Actual']
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("Portafolio vacío.")

# --- MÓDULO 3: CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Nuevo Crédito"):
        with st.form("form_cred"):
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

# --- MÓDULO 4: REGISTRO ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Ingresos/Gastos")
    with st.form("form_mov"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Versa", "Comida", "Hapi"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        if st.form_submit_button("Guardar"):
            n_m = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto}])
            df_up_m = pd.concat([df_mov, n_m], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.cache_data.clear()
            st.success("Guardado en la nube.")

# --- MÓDULO 5: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Proyección de Crecimiento")
    p = st.number_input("Capital Inicial ($)", value=4000.0)
    años = st.slider("Años de espera", 1, 30, 10)
    st.success(f"### Proyección (10% anual): ${p * (1.10**años):,.2f}")
