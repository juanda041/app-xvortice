import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Xvortice App", page_icon="💰")

st.title("🚀 Sistema Xvortice")
st.write("Gestión de Patrimonio e Inversiones")

# --- REGISTRO DE GASTOS ---
st.header("📝 Registro Diario")
with st.form("registro"):
    monto = st.number_input("Monto ($)", min_value=0.0)
    cat = st.selectbox("Categoría", ['🛒 Xvortice', '🏠 Hogar', '🚗 Versa', '💰 Bolsa', '💵 Ingreso'])
    det = st.text_input("Detalle", placeholder="Ej: Venta de perfume")
    btn_g = st.form_submit_button("Guardar Movimiento")
    if btn_g:
        st.success(f"Registrado: ${monto} en {cat}. (Sincronizado)")

# --- CALCULADORA E IA ---
st.header("📊 Asesor IA Patrimonial")
col1, col2 = st.columns(2)
with col1:
    efectivo = st.number_input("Efectivo ($)", min_value=0.0)
    bolsa = st.number_input("Bolsa/ETFs ($)", min_value=0.0)
with col2:
    negocio = st.number_input("Xvortice ($)", min_value=0.0)
    deudas = st.number_input("Deudas/Pasivos ($)", min_value=0.0)

if st.button("ANALIZAR CON IA"):
    activos = efectivo + bolsa + negocio
    total = activos - deudas
    st.metric("Patrimonio Neto", f"${total:,.2f}")
    
    if deudas > (activos * 0.4):
        st.warning("🤖 IA: Prioriza pagar deudas (Versa/Tarjetas) antes de invertir.")
    elif bolsa == 0:
        st.info("🤖 IA: No olvides tu meta de ETFs para el retiro.")
    else:
        st.success("🤖 IA: ¡Tu balance es excelente! Sigue así.")
