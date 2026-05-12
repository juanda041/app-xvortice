import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) 
def cargar_datos(nombre_hoja):
    try:
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except Exception:
        return pd.DataFrame()

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos") 

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
meta_ahorro = st.sidebar.number_input("Ajustar Meta ($)", value=5000, step=500)
menu = st.sidebar.selectbox("Módulo:", ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Total Xvortice")
    
    # Cálculos de Movimientos (Efectivo)
    df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
    efectivo = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
    
    # CÁLCULO NUEVO: Valor del Portafolio
    valor_inversiones = 0
    if not df_port.empty:
        df_port['Cantidad'] = pd.to_numeric(df_port['Cantidad'], errors='coerce').fillna(0)
        df_port['Costo Promedio'] = pd.to_numeric(df_port['Costo Promedio'], errors='coerce').fillna(0)
        valor_inversiones = (df_port['Cantidad'] * df_port['Costo Promedio']).sum()

    capital_total = efectivo + valor_inversiones

    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo / Ahorros", f"${efectivo:,.2f}")
    c2.metric("Valor en Inversiones", f"${valor_inversiones:,.2f}")
    c3.metric("Capital Neto Total", f"${capital_total:,.2f}", delta=f"${valor_inversiones:,.2f} en activos")

    st.progress(min(capital_total/meta_ahorro, 1.0) if meta_ahorro > 0 else 0, text=f"Progreso meta: {capital_total/meta_ahorro*100:.1f}%")

    st.markdown("---")
    st.info(f"🤖 **Analista IA:** Juan, sumando tus activos en Hapi y tu efectivo, tienes un patrimonio real de ${capital_total:,.2f}. ¡Cada fracción de acción cuenta!")

# --- Módulo de Registro (Sigue igual para no romper nada) ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro")
    with st.form("f_reg"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Entrada de Capital", "Gasto Personal", "Mantenimiento Versa"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("Guardado.")

# --- Módulos restantes abreviados para el ejemplo ---
elif menu == "Inversiones":
    st.header("📈 Portafolio")
    st.dataframe(df_port)

elif menu == "Gestión de Créditos":
    st.header("💸 Créditos")
    st.dataframe(df_cred)
