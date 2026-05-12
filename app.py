import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Xvortice Pro", layout="wide")

# Estilo y Título
st.title("⚡ Xvortice: Business & Wealth Control")
st.markdown("---")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARGA DE DATOS ---
df_mov = conn.read(worksheet="Movimientos", ttl="0")
try:
    df_cred = conn.read(worksheet="Creditos", ttl="0")
except:
    df_cred = pd.DataFrame(columns=["Cliente", "Producto", "Monto Total", "Saldo Pendiente", "Fecha Limite"])

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
menu = st.sidebar.selectbox("Ir a:", ["Dashboard & Meta", "Ventas a Crédito", "Inversiones ETFs", "Nuevo Registro"])

# Meta Dinámica de 5k
meta_ahorro = st.sidebar.number_input("Tu Meta Actual ($)", value=5000)

# --- SECCIÓN 1: DASHBOARD & META ---
if menu == "Dashboard & Meta":
    st.header(f"🎯 Objetivo: ${meta_ahorro:,.0f}")
    
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        total_ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        total_gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        balance_actual = total_ingresos - total_gastos
        
        progreso = min(balance_actual / meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(progreso)
        st.write(f"Has alcanzado el **{progreso*100:.1f}%** de tu meta.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Capital Actual", f"${balance_actual:,.2f}")
        col2.metric("Faltante", f"${max(0, meta_ahorro - balance_actual):,.2f}")
        col3.metric("Ventas Totales", f"${total_ingresos:,.2f}")

        st.info(f"🤖 **Analista IA:** Juan, estás a un {(1-progreso)*100:.0f}% de los ${meta_ahorro}. " 
                "El nuevo formato de 'Venta de Artículo' te ayudará a organizar mejor el flujo.")

# --- SECCIÓN 2: VENTAS A CRÉDITO ---
elif menu == "Ventas a Crédito":
    st.header("💸 Dinero en la Calle")
    with st.expander("➕ Registrar nuevo crédito"):
        with st.form("form_credito"):
            c_cliente = st.text_input("Nombre del Cliente")
            c_prod = st.text_input("Artículo (Ej: Nike Air, Perfume)")
            c_monto = st.number_input("Monto Total", min_value=0.0)
            c_fecha = st.date_input("Fecha límite de pago")
            if st.form_submit_button("Guardar Crédito"):
                st.success(f"Anotado: {c_cliente} debe ${c_monto}")

    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)

# --- SECCIÓN 3: INVERSIONES ---
elif menu == "Inversiones ETFs":
    st.header("📈 Mi Portafolio")
    st.metric("Valor estimado en ETFs", "$0.00")
    st.write("Estrategia Core & Satellite activa.")

# --- SECCIÓN 4: NUEVO REGISTRO (CATEGORÍAS PROFESIONALES) ---
elif menu == "Nuevo Registro":
    st.header("📝 Registro de Operaciones")
    with st.form("main_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            f_fecha = st.date_input("Fecha")
            f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        with col_b:
            # Aquí están tus nuevas categorías
            f_cat = st.selectbox("Categoría", [
                "Venta de Artículo", 
                "Entrada de Capital", 
                "Inversión (ETFs/Acciones)",
                "Gasto Operativo",
                "Gasto Personal"
            ])
            f_monto = st.number_input("Monto ($)", min_value=0.0)
            
        f_desc = st.text_area("Detalle (Ej: Venta de Zapatillas / Inyección de capital personal)")
        
        if st.form_submit_button("Registrar en Xvortice"):
            # Aquí se conectará con tu lógica de guardado
            st.success(f"✅ {f_cat} registrado por ${f_monto}")
            st.balloons()
