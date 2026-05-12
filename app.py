import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

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
        if str(t).upper() == "CASH":
            continue
        try:
            val = yf.Ticker(str(t).strip().upper()).history(period="1d")['Close'].iloc[-1]
            p_dict[t] = val
        except: 
            p_dict[t] = None
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
    # Efectivo externo (el que anotas en el Registro)
    cash_mov = df_m[df_m['Tipo']=='Ingreso']['Monto'].sum() - df_m[df_m['Tipo']=='Gasto']['Monto'].sum()
    
    v_inv = 0
    cash_hapi = 0
    
    if not df_p.empty:
        # SEPARACIÓN: Acciones vs Efectivo en Portafolio
        df_acciones = df_p[df_p['Ticker'] != 'CASH'].copy()
        df_efectivo = df_p[df_p['Ticker'] == 'CASH'].copy()
        
        # 1. Valor de Acciones en Vivo
        tk_list = df_acciones['Ticker'].dropna().unique().tolist()
        v_dict = precios_vivos(tk_list)
        df_acciones['Live'] = df_acciones['Ticker'].map(v_dict)
        v_acciones = (pd.to_numeric(df_acciones['Cantidad']) * df_acciones['Live'].fillna(0)).sum()
        
        # 2. Valor de la Liquidez en Hapi
        cash_hapi = pd.to_numeric(df_efectivo['Cantidad']).sum()
        
        # Bolsa Live total (Acciones + Cash de Hapi)
        v_inv = v_acciones + cash_hapi

    total = cash_mov + v_inv
    col1, col2, col3 = st.columns(3)
    col1.metric("Efectivo (Otros)", f"${cash_mov:,.2f}")
    col2.metric("Bolsa + Liquidez", f"${v_inv:,.2f}")
    col3.metric("TOTAL NETO", f"${total:,.2f}")
    st.progress(min(total/meta, 1.0) if meta > 0 else 0)
    
    st.markdown("---")
    st.subheader("🔍 Desglose de Inversiones")
    if not df_p.empty:
        st.dataframe(df_p[['Ticker', 'Nombre', 'Cantidad']], use_container_width=True)
    
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if total < meta:
        st.warning(f"Daniel, faltan ${meta-total:,.2f} para tu meta de $10k. Xvortice sigue en marcha.")
    else:
        st.success("¡Meta superada! Es momento de escalar el capital.")

# --- 2. REGISTRO ---
elif mod == "Registro":
    st.header("📝 Gestión de Movimientos")
    i_tab, g_tab = st.tabs(["💰 Ingresos", "💸 Gastos"])
    with i_tab:
        with st.form("fi", clear_on_submit=True):
            c = st.selectbox("Categoría", ["Ahorros", "Bonos", "Venta Xvortice", "Capital"])
            m = st.number_input("Monto ($)", min_value=0.0)
            n = st.text_input("Nota")
            if st.form_submit_button("Guardar"):
                new = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()),"Tipo":"Ingreso","Categoria":c,"Monto":m,"Comentario":n}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_m, new], ignore_index=True))
                st.cache_data.clear()
                st.rerun()
    with g_tab:
        with st.form("fg", clear_on_submit=True):
            c = st.selectbox("Categoría", ["Versa", "Comida", "Hapi", "Gastos Operativos", "Otros Gastos"])
            m = st.number_input("Monto ($)", min_value=0.0)
            n = st.text_input("Nota")
            if st.form_submit_button("Guardar"):
                new = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()),"Tipo":"Gasto","Categoria":c,"Monto":m,"Comentario":n}])
                conn.update(worksheet="Movimientos", data=pd.concat([df_m, new], ignore_index=True))
                st.cache_data.clear()
                st.rerun()

# --- 3. INVERSIONES ---
elif mod == "Inversiones":
    st.header("📈 Portafolio Hapi")
    with st.expander("➕ Añadir Activo / Cash"):
        with st.form("fp"):
            c1, c2 = st.columns(2)
            tk = c1.text_input("Ticker (Usa 'CASH' para liquidez)")
            nm = c2.text_input("Nombre")
            ct = c1.number_input("Cantidad", step=0.00001, format="%.5f")
            pc = c2.number_input("Precio Compra")
            cp = c1.number_input("Costo Promedio")
            if st.form_submit_button("Actualizar Bolsa"):
                new = pd.DataFrame([{"Ticker":tk.upper(),"Nombre":nm,"Cantidad":ct,"Precio de Compra":pc,"Costo Promedio":cp}])
                conn.update(worksheet="Portafolio", data=pd.concat([df_p, new], ignore_index=True))
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_p, use_container_width=True)

# --- 4. CRÉDITOS ---
elif mod == "Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Nuevo Crédito"):
        with st.form("fc"):
            cl = st.text_input("Cliente")
            sd = st.number_input("Saldo")
            if st.form_submit_button("Registrar"):
                new = pd.DataFrame([{"Cliente":cl, "Saldo pendiente":sd}])
                conn.update(worksheet="Creditos", data=pd.concat([df_c, new], ignore_index=True))
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_c, use_container_width=True)

# --- 5. PROYECCIÓN ---
elif mod == "Proyección":
    st.header("📈 Interés Compuesto")
    cap = st.number_input("Capital Inicial", value=total if 'total' in locals() else 4000.0)
    años = st.slider("Años", 1, 30, 10)
    res = cap * (1.10**años)
    st.success(f"### Estimación (10% anual): ${res:,.2f}")
