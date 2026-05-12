import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ (Para evitar el Error 429) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600) # Guarda los datos por 10 min para no molestar a Google
def cargar_todo():
    try:
        m = conn.read(worksheet="Movimientos", ttl="0")
        p = conn.read(worksheet="Portafolio", ttl="0")
        c = conn.read(worksheet="Creditos", ttl="0")
        
        if not m.empty and 'Monto' in m.columns:
            m['Monto'] = pd.to_numeric(m['Monto'], errors='coerce').fillna(0)
        return m, p, c
    except Exception as e:
        st.error(f"Esperando conexión estable... (Detalle: {e})")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mov, df_port, df_cred = cargar_todo()

# --- 3. MENÚ ---
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Interés Compuesto", "Registro", "Créditos"])

# --- MÓDULO: ESTADO PATRIMONIAL ---
if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Actual")
    if not df_mov.empty:
        actual = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        st.metric("Capital Neto", f"${actual:,.2f}")
        st.progress(min(actual/5000, 1.0))
        st.dataframe(df_mov)

# --- MÓDULO NUEVO: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Calculadora de Proyección Xvortice")
    col1, col2 = st.columns(2)
    
    # Datos iniciales automáticos desde tu capital actual
    capital_inic = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum() if not df_mov.empty else 0
    
    cap_i = col1.number_input("Capital Inicial ($)", value=float(capital_inic))
    aporte = col1.number_input("Aporte Mensual ($)", value=100.0)
    años = col2.number_input("Años de inversión", value=5, min_value=1)
    tasa = col2.slider("Tasa de interés anual (%)", 1, 15, 8) / 100
    
    # Fórmula: A = P(1 + r/n)^(nt) + PMT * [((1 + r/n)^(nt) - 1) / (r/n)]
    meses = años * 12
    tasa_m = tasa / 12
    final = cap_i * (1 + tasa_m)**meses + aporte * (((1 + tasa_m)**meses - 1) / tasa_m)
    
    st.success(f"### En {años} años, tu capital será de: ${final:,.2f}")
    st.info(f"Ganancia total por intereses: ${(final - cap_i - (aporte*meses)):,.2f}")

# --- MÓDULO: REGISTRO ---
elif menu == "Registro":
    st.header("📝 Nuevo Registro")
    with st.form("reg"):
        f_user = st.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": "2026-05-11", "Usuario": f_user, "Tipo": f_tipo, "Monto": f_monto}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear() # Limpia el caché para ver el cambio
            st.rerun()

# --- MÓDULO: CRÉDITOS ---
elif menu == "Créditos":
    st.header("💸 Créditos")
    st.dataframe(df_cred)
