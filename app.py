import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO "DARK PRO" ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    div[data-testid="stExpander"] { border: 1px solid #3b82f6; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #3b82f6; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro")
st.markdown(f"**Daniel** | Portafolio Global | Gestión de Capital")

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. MONITOR DE MERCADO ---
    with st.expander("📈 Monitor de Mercado en Vivo", expanded=True):
        activos = ["NVDA", "BTC-USD", "VOO", "BAC", "O"]
        cols_m = st.columns(len(activos))
        for i, ticker in enumerate(activos):
            try:
                data = yf.Ticker(ticker).history(period="1d")
                precio = data['Close'].iloc[-1]
                cols_m[i].metric(ticker, f"${precio:,.2f}")
            except:
                continue

    # --- 2. LÓGICA DE PATRIMONIO ---
    ingresos = df[df['Categoría'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    egresos = df[df['Categoría'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    patrimonio_neto = ingresos - egresos
    meta_objetivo = 10000.00
    progreso_meta = (patrimonio_neto / meta_objetivo) * 100

    # --- 3. DASHBOARD PRINCIPAL ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Totales", f"${ingresos:,.2f}")
    c2.metric("Egresos Totales", f"${egresos:,.2f}", delta=f"-{egresos:,.2f}", delta_color="inverse")
    c3.metric("Patrimonio Neto", f"${patrimonio_neto:,.2f}")
    c4.metric("Meta $10k", f"{progreso_meta:.1f}%", f"${patrimonio_neto - meta_objetivo:,.2f}")

    # --- 4. PANEL DE CONTROL ---
    t1, t2, t3, t4 = st.tabs(["💰 Flujo de Caja", "📊 Análisis", "💹 Interés Compuesto", "🤖 Asistente IA"])

    with t1:
        col_form, col_view = st.columns([1, 2])
        with col_form:
            st.subheader("📝 Nuevo Registro")
            with st.form("registro_xvortice"):
                f = st.date_input("Fecha", datetime.now())
                c = st.selectbox("Categoría", ["Ingreso", "Gasto", "Inversión", "Ahorro"])
                m = st.number_input("Monto ($)", min_value=0.0)
                d = st.text_input("Detalle")
                if st.form_submit_button("Guardar"):
                    st.success("Dato listo para anotar en el Excel.")
        with col_view:
            st.subheader("Historial")
            st.dataframe(df.tail(10), use_container_width=True)

    with t2:
        fig_pie = px.pie(df, values='Monto', names='Categoría', hole=0.5, title="Distribución de Capital")
        st.plotly_chart(fig_pie, use_container_width=True)

    with t3:
        st.subheader("💰 Simulador de Interés Compuesto")
        p_ini = st.number_input("Capital Actual", value=float(patrimonio_neto))
        t_int = st.slider("Interés Anual (%)", 1, 20, 10)
        tiempo = st.slider("Años", 1, 40, 10)
        res = p_ini * (1 + (t_int/100))**tiempo
        st.success(f"Proyección a {tiempo} años: ${res:,.2f}")

    with t4:
        st.subheader("🤖 Consultoría IA Xvortice")
        pregunta = st.text_input("Analiza tu situación financiera:")
        if pregunta:
            st.info(f"Daniel, basándome en tus ingresos de ${ingresos:,.2f}, vas por excelente camino.")

except Exception as e:
    st.error(f"Error en el sistema maestro: {e}")
