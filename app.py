import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ (Evita el error 429 de tus fotos) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) # Guarda datos 5 min para que Google no te bloquee
def cargar_datos(hoja):
    try:
        return conn.read(worksheet=hoja, ttl="0")
    except Exception as e:
        return pd.DataFrame()

# Carga inicial silenciosa
df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("creditos") # En tu foto 6 sale en minúscula

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Interés Compuesto", "Registro", "Créditos", "Inversiones"])

# --- LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Actual")
    if not df_mov.empty:
        # Convertimos Monto a número por si acaso
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        actual = ingresos - gastos
        
        st.metric("Capital Neto Real", f"${actual:,.2f}")
        st.write("### Últimos Movimientos")
        st.dataframe(df_mov, use_container_width=True)
    else:
        st.warning("Esperando a que Google desbloquee la conexión... espera 2 minutos.")

elif menu == "Interés Compuesto":
    st.header("📈 Simulador de Riqueza")
    col1, col2 = st.columns(2)
    cap_i = col1.number_input("Capital Inicial ($)", value=4000.0) # Basado en tu ahorro de la foto 6
    aporte = col1.number_input("Aporte Mensual ($)", value=200.0)
    años = col2.slider("Años", 1, 30, 10)
    tasa = col2.slider("Tasa Anual (%)", 1, 15, 10) / 100
    
    # Cálculo
    meses = años * 12
    tasa_m = tasa / 12
    final = cap_i * (1 + tasa_m)**meses + aporte * (((1 + tasa_m)**meses - 1) / tasa_m)
    
    st.success(f"### Proyección a {años} años: ${final:,.2f}")

elif menu == "Registro":
    st.header("📝 Registrar Venta o Gasto")
    with st.form("reg"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_input("Comentario")
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": "2026-05-12", "Usuario": "Juan Daniel", "Tipo": f_tipo, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("Guardado. Refresca en 10 segundos.")

elif menu == "Créditos":
    st.header("💸 Gestión de Cobros")
    # Formulario para que no se te pierda el escrito
    with st.expander("➕ Registrar Nuevo Cliente/Crédito"):
        with st.form("f_cred"):
            c1, c2 = st.columns(2)
            f_cli = c1.text_input("Cliente")
            f_prod = c2.text_input("Producto")
            f_sal = st.number_input("Saldo pendiente", min_value=0.0)
            if st.form_submit_button("Añadir a la lista"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="creditos", data=df_up_c)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_cred, use_container_width=True)

elif menu == "Inversiones":
    st.header("📈 Mi Portafolio")
    if not df_port.empty:
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("Hoja de Portafolio vacía o cargando...")
