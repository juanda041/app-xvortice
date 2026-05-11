import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Xvortice App", page_icon="🚀")

st.title("🚀 Sistema Xvortice")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- REGISTRO DE MOVIMIENTOS ---
st.header("📝 Registro Diario")
with st.form("registro"):
    monto_val = st.number_input("Monto ($)", min_value=0.0)
    tipo_sel = st.selectbox("Tipo", ['Ingreso', 'Gasto'])
    cat_sel = st.selectbox("Categoría", ['🛒 Xvortice', '🏠 Hogar', '🚗 Versa', '💰 Bolsa'])
    detalle_val = st.text_input("Descripción", placeholder="Ej: Venta de perfume / Super")
    
    btn_g = st.form_submit_button("Guardar en Excel")

    if btn_g:
        # Creamos la fila con TUS columnas exactas del Excel
        nueva_fila = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Usuario": "Juan",
            "Tipo": tipo_sel,
            "Categoria": cat_sel,
            "Subcategoria": "-", 
            "Monto": monto_val,
            "Descripcion": detalle_val
        }])
        
        # Leer datos actuales y agregar la nueva fila
        data_actual = conn.read()
        updated_df = pd.concat([data_actual, nueva_fila], ignore_index=True)
        
        # Guardar de vuelta en Google Sheets
        conn.update(data=updated_df)
        st.success("✅ ¡Guardado en Gestion Patrimonial!")

# --- CALCULADORA E IA ---
st.divider()
st.header("📊 Asesor IA Patrimonial")
col1, col2 = st.columns(2)
with col1:
    efectivo = st.number_input("Efectivo ($)", min_value=0.0)
    bolsa = st.number_input("Bolsa/ETFs ($)", min_value=0.0)
with col2:
    negocio = st.number_input("Xvortice ($)", min_value=0.0)
    deudas = st.number_input("Deudas ($)", min_value=0.0)

if st.button("ANALIZAR CON IA"):
    activos = efectivo + bolsa + negocio
    total = activos - deudas
    st.metric("Patrimonio Neto", f"${total:,.2f}")
    
    if deudas > (activos * 0.4):
        st.warning("🤖 IA: Tus deudas están algo altas. Prioriza pagar el Versa o tarjetas antes de meter más a la bolsa.")
    elif bolsa == 0:
        st.info("🤖 IA: El negocio va bien, pero recuerda diversificar en ETFs para tu retiro.")
    else:
        st.success("🤖 IA: ¡Balance sólido! Estás gestionando muy bien el capital de Xvortice.")
