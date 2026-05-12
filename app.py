import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ (Para evitar errores de cuota) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) # Guarda los datos 5 min para no saturar a Google
def cargar_datos(nombre_hoja):
    try:
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except Exception as e:
        return pd.DataFrame()

# Carga de las hojas (He cambiado 'creditos' por 'Creditos' como pediste)
df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos") 

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
menu = st.sidebar.selectbox("Seleccione Módulo:", 
    ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

meta_ahorro = 5000

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO: PATRIMONIO ---
if menu == "Estado Patrimonial":
    st.header("📊 Resumen de Capital")
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        actual = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Capital Neto Real", f"${actual:,.2f}")
        c2.metric("Meta de Ahorro", f"${meta_ahorro:,.2f}")
        st.progress(min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        st.write("### Historial Completo")
        st.dataframe(df_mov, use_container_width=True)
    else:
        st.info("Cargando datos desde Google Sheets... Si tarda mucho, refresca en 1 minuto.")

# --- MÓDULO: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Proyección de Crecimiento")
    col1, col2 = st.columns(2)
    # Usamos $4,000 como base inicial común en tus ahorros
    cap_i = col1.number_input("Capital Inicial ($)", value=4000.0) 
    aporte = col1.number_input("Aporte Mensual sugerido ($)", value=200.0)
    años = col2.slider("Años a futuro", 1, 30, 10)
    tasa = col2.slider("Tasa Anual Esperada (%)", 1, 15, 10) / 100
    
    meses = años * 12
    tasa_m = tasa / 12
    final = cap_i * (1 + tasa_m)**meses + aporte * (((1 + tasa_m)**meses - 1) / tasa_m)
    
    st.success(f"### Estimación en {años} años: ${final:,.2f}")
    st.info("Este cálculo asume que reinviertes tus ganancias mes a mes.")

# --- MÓDULO: REGISTRO ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento")
    with st.form("form_registro"):
        f_user = st.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Descripción / Comentario")
        if st.form_submit_button("Guardar en Excel"):
            nuevo = pd.DataFrame([{"Fecha": "2026-05-12", "Usuario": f_user, "Tipo": f_tipo, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear() # Limpia la memoria para mostrar el nuevo dato
            st.success("✅ Datos enviados. La App se actualizará en unos segundos.")

# --- MÓDULO: CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar (Xvortice)")
    with st.expander("➕ Agregar nuevo cliente/crédito"):
        with st.form("f_cred"):
            f_cli = st.text_input("Nombre del Cliente")
            f_prod = st.text_input("Producto vendido")
            f_sal = st.number_input("Saldo pendiente ($)", min_value=0.0)
            if st.form_submit_button("Registrar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c) # Aquí ya usa la 'C' mayúscula
                st.cache_data.clear()
                st.rerun()
    
    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)
        # Suma automática de lo que te deben
        if 'Saldo pendiente' in df_cred.columns:
            total_deuda = pd.to_numeric(df_cred['Saldo pendiente'], errors='coerce').sum()
            st.metric("Total por cobrar", f"${total_deuda:,.2f}")

# --- MÓDULO: INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Cartera de Inversión")
    if not df_port.empty:
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("No se encontraron activos en la hoja 'Portafolio'.")
