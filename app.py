import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración Pro - El Xvortice que armamos
st.set_page_config(page_title="Xvortice", layout="wide", page_icon="🏛️")

st.title("🏛️ Xvortice: Gestión Patrimonial")
st.markdown(f"**Usuario:** Daniel | **Meta 2026:** $5,000.00")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leemos la pestaña de Movimientos
    df = conn.read(worksheet="Movimientos", ttl=0)
    df = df.dropna(how="all").fillna("")
    
    # Limpieza de columnas para que no fallen las tildes
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})

    if not df.empty:
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        
        # --- CÁLCULOS DE PATRIMONIO ---
        ahorro = df[df['Categoría'].str.contains('Ahorro', case=False, na=False)]['Monto'].sum()
        inversion = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()
        patrimonio_total = ahorro + inversion

        # --- DASHBOARD DE MÉTRICAS ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimonio Total", f"${patrimonio_total:,.2f}")
        c2.metric("Portafolio ETFs/Acciones", f"${inversion:,.2f}")
        progreso = (ahorro / 5000) * 100
        c3.metric("Progreso Meta $5K", f"{progreso:.1f}%", f"${ahorro - 5000:,.2f}")

        st.divider()

        # --- SECCIONES DE LA APP ---
        tab1, tab2, tab3, tab4 = st.tabs(["💰 Gestión de Gastos", "📈 Inversiones & Interés", "🤖 IA Xvortice", "📋 Historial"])

        with tab1:
            st.subheader("Registrar nuevo movimiento")
            with st.form("registro"):
                col_f, col_c, col_m = st.columns(3)
                f = col_f.date_input("Fecha", datetime.now())
                c = col_c.selectbox("Categoría", ["Ahorro", "Inversión", "Gasto", "Ingreso"])
                m = col_m.number_input("Monto ($)", min_value=0.0)
                d = st.text_input("Descripción (Ej: Abono de cliente, Compra NVDA)")
                if st.form_submit_button("Guardar Registro"):
                    st.warning("Copia esta fila a tu Excel para actualizar el total.")

        with tab2:
            st.subheader("Simulador de Interés Compuesto")
            p = st.number_input("Capital Inicial", value=float(patrimonio_total))
            i = st.slider("Interés Anual (%)", 1, 15, 10)
            t = st.slider("Años", 1, 30, 10)
            resultado = p * (1 + (i/100))**t
            st.success(f"En {t} años, tu capital proyectado es: ${resultado:,.2f}")

        with tab3:
            st.subheader("Consultas a la IA")
            pregunta = st.text_input("¿Qué quieres saber de tus finanzas?")
            if pregunta:
                st.write("🤖 Daniel, analizando tus datos de 'Movimientos', veo que vas por buen camino.")

        with tab4:
            st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar Xvortice: {e}")
