import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Xvortice Pro", layout="wide")

# Título Principal
st.title("⚡ Xvortice: Business & Wealth Control")
st.markdown("---")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARGA DE DATOS ---
# Cargamos movimientos
df_mov = conn.read(worksheet="Movimientos", ttl="0")

# Cargamos créditos (la nueva hoja que creaste)
try:
    df_cred = conn.read(worksheet="Creditos", ttl="0")
except:
    df_cred = pd.DataFrame(columns=["Cliente", "Producto", "Monto Total", "Saldo Pendiente", "Fecha Limite"])

# --- BARRA LATERAL (Sidebar) ---
st.sidebar.header("Menú de Control")
menu = st.sidebar.selectbox("Selecciona una opción:", [
    "Dashboard & Meta", 
    "Ventas a Crédito", 
    "Inversiones ETFs", 
    "Nuevo Registro"
])

# Configuración de Meta (puedes cambiar los 5000 cuando quieras)
meta_ahorro = st.sidebar.number_input("Tu Meta Actual ($)", value=5000)

# --- SECCIÓN 1: DASHBOARD & META ---
if menu == "Dashboard & Meta":
    st.header(f"🎯 Objetivo de Ahorro: ${meta_ahorro:,.0f}")
    
    if not df_mov.empty:
        # Convertir montos a números por si acaso
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        total_ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        total_gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        balance_actual = total_ingresos - total_gastos
        
        # Barra de progreso
        progreso = min(balance_actual / meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(progreso)
        st.write(f"Felicidades Juan, llevas el **{progreso*100:.1f}%** de tu meta completado.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Capital en Caja", f"${balance_actual:,.2f}")
        col2.metric("Faltante para Meta", f"${max(0, meta_ahorro - balance_actual):,.2f}")
        col3.metric("Ingresos Totales", f"${total_ingresos:,.2f}")

        st.info(f"🤖 **Analista Xvortice:** Estás a ${max(0, meta_ahorro - balance_actual):,.2f} de alcanzar tu objetivo. ¡Sigue así!")

# --- SECCIÓN 2: VENTAS A CRÉDITO ---
elif menu == "Ventas a Crédito":
    st.header("💸 Dinero en la Calle (Cuentas por Cobrar)")
    
    with st.expander("➕ Registrar nuevo crédito"):
        with st.form("form_credito"):
            c_cliente = st.text_input("Nombre del Cliente")
            c_prod = st.text_input("Artículo entregado")
            c_monto = st.number_input("Monto total de la deuda", min_value=0.0)
            c_fecha = st.date_input("Fecha máxima de pago")
            if st.form_submit_button("Guardar Deuda"):
                st.success(f"Registrado: {c_cliente} te debe ${c_monto}")

    st.subheader("Listado de Deudores")
    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)
    else:
        st.write("No hay deudas registradas en la pestaña 'Creditos'.")

# --- SECCIÓN 3: INVERSIONES ---
elif menu == "Inversiones ETFs":
    st.header("📈 Mi Portafolio Personal")
    st.write("Aquí verás el crecimiento de tus ETFs (VOO, etc.)")
    st.metric("Valor en Cartera (Hapi)", "$0.00")
    st.info("Estrategia: Core (Largo Plazo) & Satellite (Trading)")

# --- SECCIÓN 4: NUEVO REGISTRO ---
elif menu == "Nuevo Registro":
    st.header("📝 Registro Profesional de Operaciones")
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        with col1:
            f_fecha = st.date_input("Fecha de hoy")
            f_tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
        with col2:
            f_cat = st.selectbox("Categoría Profesional", [
                "Venta de Artículo", 
                "Entrada de Capital", 
                "Inversión (ETFs/Acciones)",
                "Gasto Operativo",
                "Gasto Personal"
            ])
            f_monto = st.number_input("Monto ($)", min_value=0.0)
            
        f_desc = st.text_area("Detalle de la operación")
        
        if st.form_submit_button("Subir a Xvortice"):
            st.success(f"¡{f_cat} guardado exitosamente!")
            st.balloons()
