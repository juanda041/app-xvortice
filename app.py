import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab-panel"] { background-color: #0e1117; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Maestro de Gestión")

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Movimientos", ttl=0)
    # Limpieza profunda de datos
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción', 'Detalle': 'Ticker'})
    df['Categoría'] = df['Categoría'].astype(str).fillna("")
    df['Ticker'] = df['Ticker'].astype(str).fillna("")
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- 1. LÓGICA DE INVERSIONES EN VIVO ---
    tickers_usuario = ["NVDA", "VOO", "BAC", "O", "BTC-USD", "ETH-USD"]
    precios_mercado = {}
    
    with st.expander("📈 Monitor de Portafolio en Vivo", expanded=True):
        cols_p = st.columns(len(tickers_usuario))
        for i, t in enumerate(tickers_usuario):
            try:
                # Obtenemos precio actual
                price = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
                precios_mercado[t] = price
                cols_p[i].metric(t, f"${price:,.2f}")
            except:
                precios_mercado[t] = 0

    # --- 2. CÁLCULO DE PATRIMONIO DINÁMICO ---
    # Ingresos totales
    ingresos = df[df['Categoría'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    
    # Gastos Personales (Restan patrimonio)
    gastos_pers = df[df['Categoría'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    
    # Gastos de Negocio / Operativos (Se restan de efectivo pero se consideran activo en inventario/cuentas)
    gastos_negocio = df[df['Categoría'].str.contains('Operativo|Negocio', case=False, na=False)]['Monto'].sum()
    
    # Cuentas por Cobrar (Suma al patrimonio)
    cuentas_cobrar = df[df['Categoría'].str.contains('Cobrar', case=False, na=False)]['Monto'].sum()
    
    # Inversiones (Valorizadas)
    valor_inv = 0
    for t in tickers_usuario:
        cant = df[df['Ticker'].str.contains(t, case=False, na=False)]['Monto'].sum()
        valor_inv += (cant * precios_mercado.get(t, 0))
    
    # Si no hay tickers, sumamos lo anotado como Inversión
    if valor_inv == 0:
        valor_inv = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()

    # PATRIMONIO TOTAL = (Ingresos + Valor Inversiones + Cuentas Cobrar) - Gastos Personales
    patrimonio_real = (ingresos + valor_inv + cuentas_cobrar) - gastos_pers

    # --- 3. DASHBOARD DE MÉTRICAS ---
    st.divider()
    meta_dinamica = st.sidebar.number_input("🎯 Ajustar Meta Personal", value=10000, step=1000)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio_real:,.2f}")
    c2.metric("Inversiones (Bolsa)", f"${valor_inv:,.2f}")
    c3.metric("Cuentas por Cobrar", f"${cuentas_cobrar:,.2f}")
    progreso = (patrimonio_real / meta_dinamica) * 100
    c4.metric(f"Meta ${meta_dinamica:,.0f}", f"{progreso:.1f}%", f"${patrimonio_real - meta_dinamica:,.2f}")

    # --- 4. SECCIONES (TABS) ---
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Gestión Financiera", "📊 Análisis Xvortice", "💹 Interés Compuesto", "🤖 Analista IA"])

    with tab1:
        col_reg, col_hist = st.columns([1, 2])
        with col_reg:
            st.subheader("Registrar Movimiento")
            with st.form("master_form"):
                f = st.date_input("Fecha", datetime.now())
                cat = st.selectbox("Categoría", ["Ingreso", "Gasto Personal", "Gasto Operativo", "Inversión", "Cuenta por Cobrar"])
                m = st.number_input("Monto ($)", min_value=0.0)
                t = st.text_input("Ticker / Detalle (Ej: NVDA o Cliente X)")
                if st.form_submit_button("Guardar"):
                    st.success("¡Listo! Anótalo en tu Excel.")
        with col_hist:
            st.subheader("Historial de Actividad")
            st.dataframe(df.tail(10), use_container_width=True)

    with tab2:
        st.subheader("Distribución de Activos")
        labels = ['Inversiones', 'Cuentas por Cobrar', 'Capital Líquido']
        values = [valor_inv, cuentas_cobrar, (ingresos - gastos_pers - gastos_negocio)]
        fig = px.pie(names=labels, values=values, hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    with t3 := tab3:
        st.subheader("💰 Simulación de Patrimonio Futuro")
        p = st.number_input("Capital Inicial (Patrimonio Actual)", value=float(patrimonio_real))
        r = st.slider("Tasa Anual Estimada (%)", 1, 30, 10)
        t = st.slider("Años de Proyección", 1, 50, 10)
        final = p * (1 + (r/100))**t
        st.success(f"En {t} años, tu patrimonio proyectado sería de: ${final:,.2f}")

    with tab4:
        st.subheader("🤖 Inteligencia Financiera")
        duda = st.text_input("Hazle una pregunta a Xvortice sobre tu dinero
