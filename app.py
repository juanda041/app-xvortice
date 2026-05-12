import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Xvortice Executive", 
    page_icon="📈", 
    layout="wide"
)

# --- 2. CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # Carga de Movimientos con blindaje
    try:
        df_m = conn.read(worksheet="Movimientos", ttl="0")
    except Exception:
        df_m = pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto"])

    # Carga de Portafolio con blindaje (EVITA EL ERROR ROJO DE SHEET NOT FOUND)
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

# Ejecutar carga de datos inicial
df_mov, df_port, df_cred = cargar_datos()

# --- 3. NAVEGACIÓN LATERAL ---
st.sidebar.title("🏛️ Xvortice Corporate")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo Estratégico:", 
    ["Estado Patrimonial", "Gestión de Créditos", "Cartera de Inversiones", "Proyección de Riqueza", "Registro de Operaciones"])

meta_ahorro = st.sidebar.number_input("Objetivo de Capital ($)", value=5000)

# --- 4. LÓGICA DE LOS MÓDULOS ---

# MÓDULO 1: ESTADO PATRIMONIAL
if menu == "Estado Patrimonial":
    st.header("🏛️ Análisis de Activos y Patrimonio")
    
    if not df_mov.empty:
        # Limpieza de datos duplicados y conversión a números
        df_mov = df_mov.loc[:, ~df_mov.columns.duplicated()]
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
            st.info(f"Juan, vas por buen camino. Faltan ${faltante:,.2f} para tu meta.")
        else:
            st.success("¡Meta estratégica alcanzada! Objetivo de $5,000 completado.")
    else:
        st.warning("No hay datos en 'Movimientos'. Registra tu primera operación.")

# MÓDULO 2: GESTIÓN DE CRÉDITOS
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas")
    if not df_cred.empty:
        st.table(df_cred)
    else:
        st.info("No hay créditos registrados en la hoja 'Creditos'.")

# MÓDULO 3: CARTERA DE INVERSIONES
elif menu == "Cartera de Inversiones":
    st.header("📈 Cartera Live")
    if not df_port.empty and "Ticker" in df_port.columns:
        try:
            lista_f = []
            for i, row in df_port.iterrows():
                t_sim = str(row['Ticker']).strip()
                stock = yf.Ticker(t_sim)
                precio = stock.history(period="1d")['Close'].iloc[-1]
                valor_v = precio * row['Cantidad']
                lista_f.append({"Activo": t_sim, "Valor Actual": valor_v})
            
            df_fig = pd.DataFrame(lista_f)
            fig = px.pie(df_fig, values='Valor Actual', names='Activo', hole=0.5)
            st.plotly_chart(fig)
        except Exception:
            st.error("Error al conectar con Wall Street. Revisa los Tickers en tu Excel.")
    else:
        st.info("Hoja 'Portafolio' no detectada o vacía.")

# MÓDULO 4: PROYECCIÓN DE RIQUEZA
elif menu == "Proyección de Riqueza":
    st.header("⏳ Simulador de Interés Compuesto")
    col1, col2 = st.columns(2)
    with col1:
        cap_ini = st.number_input("Capital Inicial ($)", value=1000)
        aporte = st.number_input("Aporte Mensual ($)", value=200)
    with col2:
        tasa = st.slider("Tasa Anual (%)", 1, 20, 10)
        tiempo = st.slider("Años", 1, 30, 10)
    
    meses = tiempo * 12
    r_men = (tasa / 100) / 12
    datos_p = []
    total = cap_ini
    for m in range(meses):
        total = (total + aporte) * (1 + r_men)
        datos_p.append(total)
    
    st.plotly_chart(px.area(y=datos_p, title="Crecimiento Proyectado"))
    st.success(f"Capital estimado: ${total:,.2f}")

# MÓDULO 5: REGIST
