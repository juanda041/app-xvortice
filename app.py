import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Xvortice Executive", 
    page_icon="📈", 
    layout="wide"
)

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # Carga de Movimientos con blindaje
    try:
        df_m = conn.read(worksheet="Movimientos", ttl="0")
    except Exception:
        df_m = pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto"])

    # Carga de Portafolio con blindaje (EVITA EL ERROR ROJO)
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except Exception:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])

    # Carga de Créditos con blindaje
    try:
        df_c = conn.read(worksheet="Creditos", ttl="0")
    except Exception:
        df_c = pd.DataFrame(columns=["Cliente", "Producto", "Monto Total", "Saldo Pendiente", "Fecha Limite"])
        
    return df_m, df_p, df_c

# Ejecutar carga
df_mov, df_port, df_cred = cargar_datos()

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("🏛️ Xvortice Corporate")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo Estratégico:", 
    ["Estado Patrimonial", "Gestión de Créditos", "Cartera de Inversiones", "Proyección de Riqueza", "Registro de Operaciones"])

meta_ahorro = st.sidebar.number_input("Objetivo de Capital ($)", value=5000)

# --- 1. ESTADO PATRIMONIAL ---
if menu == "Estado Patrimonial":
    st.header("🏛️ Análisis de Activos y Patrimonio")
    
    if not df_mov.empty:
        # Convertir montos a números por si acaso
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        
        ventas = df_mov[df_mov['Categoria'] == 'Venta de Artículo']['Monto'].sum()
        reserva = df_mov[df_mov['Categoria'] == 'Reserva de Capital']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        patrimonio_liquido = ventas + reserva - gastos
        progreso = min(patrimonio_liquido / meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        
        st.write(f"**Progreso hacia Meta (${meta_ahorro:,.0f})**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimonio Líquido", f"${patrimonio_liquido:,.2f}")
        c2.metric("Reserva de Capital", f"${reserva:,.2f}")
        c3.metric("Rendimiento de Meta", f"{progreso*100:.1f}%")
        
        st.markdown("---")
        st.subheader("🤖 Analista IA Xvortice")
        faltante = max(0, meta_ahorro - patrimonio_liquido)
        if progreso < 1.0:
            st.info(f"Juan, el capital actual es de ${patrimonio_liquido:,.2f}. Faltan ${faltante:,.2f} para tu objetivo.")
        else:
            st.success("¡Felicidades! Has alcanzado la meta estratégica de $5,000.")
    else:
        st.warning("No hay movimientos registrados. Empieza en el módulo de 'Registro de Operaciones'.")

# --- 2. GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas y Cobros")
    if not df_cred.empty:
        st.table(df_cred)
    else:
        st.info("No hay créditos activos en este momento.")

# --- 3. CARTERA DE INVERSIONES ---
elif menu == "Cartera de Inversiones":
    st.header("📈 Cartera Live (Wall Street)")
    if not df_port.empty and "Ticker" in df_port.columns:
        try:
            lista_f = []
            for i, row in df_port.iterrows():
                ticker_sim = row['Ticker'].strip()
                stock = yf.Ticker(ticker_sim)
                precio = stock.history(period="1d")['Close'].iloc[-1]
                valor_actual = precio * row['Cantidad']
                lista_f.append({"Activo": ticker_sim, "Valor Actual": valor_actual})
            
            df_fig = pd.DataFrame(lista_f)
            fig = px.pie(df_fig, values='Valor Actual', names='Activo', hole=0.5, title="Distribución de Activos")
            st.plotly_chart(fig)
            st.dataframe(df_fig)
        except:
            st.error("Error conectando con Yahoo Finance. Verifica los Tickers en tu Excel.")
    else:
        st.info("Agrega activos a la hoja 'Portafolio' de tu Excel (Ticker, Cantidad) para ver este análisis.")

# --- 4. PROYECCIÓN DE RIQUEZA ---
elif menu == "Proyección de Riqueza":
    st.header("⏳ Simulador de Interés Compuesto")
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        cap_ini = st.number_input("Capital Inicial ($)", value=1000)
        aporte = st.number_input("Aporte Mensual ($)", value=200)
    with col_inv2:
        tasa = st.slider("Tasa Anual Esperada (%)", 1, 20, 10)
        tiempo = st.slider("Años a proyectar", 1, 30, 10)
    
    meses = tiempo * 12
    t_men = (tasa / 100) / 12
    proyeccion = []
    capital = cap_ini
    for m in range(meses):
        capital = (capital + aporte) * (1 + t_men)
        proyeccion.append(capital)
    
    df_proy = pd.DataFrame({"Mes": range(meses), "Capital": proyeccion})
    st.plotly_chart(px.line(df_proy, x="Mes", y="Capital", title="Crecimiento Estimado"))
    st.success(f"Patrimonio estimado en {tiempo} años: **${capital:,.2f}**")

# --- 5. REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Movimientos")
    with st.form("registro_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_fecha = st.date_input("Fecha")
            f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        with col_f2:
            f_cat = st.selectbox("Categoría", ["Venta de Artículo", "Reserva de Capital", "Gasto Operativo", "Gasto Personal"])
            f_monto = st.number_input("Monto ($)", min_value=0.0)
        
        if st.form_submit_button("
