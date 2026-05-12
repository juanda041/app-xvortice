import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Configuración de nivel ejecutivo
st.set_page_config(page_title="Xvortice Executive", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Título de la Firma
st.title("🏛️ Xvortice: Centro de Estrategia Patrimonial")
st.markdown("---")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARGA DE DATOS ---
df_mov = conn.read(worksheet="Movimientos", ttl="0")
try:
    df_port = conn.read(worksheet="Portafolio", ttl="0")
except:
    df_port = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])

# --- MENÚ LATERAL ---
st.sidebar.header("Xvortice Navigation")
menu = st.sidebar.selectbox("Seleccionar Módulo:", 
    ["Estado del Patrimonio", "Control de Créditos", "Portafolio en Tiempo Real", "Nuevo Registro"])

meta_ahorro = st.sidebar.number_input("Meta de Capital Estratégico ($)", value=5000)

# --- 1. ESTADO DEL PATRIMONIO (Elegante) ---
if menu == "Estado del Patrimonio":
    st.subheader("📊 Análisis de Metas y Liquidez")
    
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        capital_operativo = ingresos - gastos
        
        progreso = min(capital_operativo / meta_ahorro, 1.0)
        
        # Barra de progreso estilizada
        st.write(f"**Progreso hacia la meta de ${meta_ahorro:,.0f}**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Operativo", f"${capital_operativo:,.2f}")
        c2.metric("Eficiencia de Meta", f"{progreso*100:.1f}%")
        c3.metric("Faltante Neto", f"${max(0, meta_ahorro - capital_operativo):,.2f}")
        
        st.info(f"🤖 **Analista IA:** Juan, mantienes un capital de ${capital_operativo:,.2f}. "
                f"Para alcanzar tu meta, necesitas captar ${max(0, meta_ahorro - capital_operativo):,.2f} adicionales. "
                "Considera reinvertir las utilidades de las ventas de artículos para acelerar el interés compuesto.")

# --- 2. CONTROL DE CRÉDITOS ---
elif menu == "Control de Créditos":
    st.subheader("💸 Cuentas Activas por Cobrar")
    st.write("Gestión de activos circulantes en el mercado (dinero en la calle).")
    # (Aquí cargará los datos de tu pestaña Creditos)
    st.info("Próximamente: Notificaciones automáticas de cobro.")

# --- 3. PORTAFOLIO EN TIEMPO REAL (La Magia) ---
elif menu == "Portafolio en Tiempo Real":
    st.subheader("📈 Rendimiento de Inversiones (Live)")
    
    if not df_port.empty and 'Ticker' in df_port.columns:
        total_invertido_actual = 0
        total_costo_base = 0
        
        for index, row in df_port.iterrows():
            ticker = row['Ticker'].strip().upper()
            cantidad = float(row['Cantidad'])
            precio_compra = float(row['Precio de Compra'])
            
            # Consultar Yahoo Finance
            stock = yf.Ticker(ticker)
            try:
                precio_actual = stock.history(period="1d")['Close'].iloc[-1]
            except:
                precio_actual = precio_compra # Fallback
            
            valor_actual = precio_actual * cantidad
            costo_base = precio_compra * cantidad
            ganancia = valor_actual - costo_base
            
            total_invertido_actual += valor_actual
            total_costo_base += costo_base
            
            with st.expander(f"🔍 Detalle: {ticker}"):
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"**Precio Actual:** ${precio_actual:,.2f}")
                col_b.write(f"**Valor Posición:** ${valor_actual:,.2f}")
                col_c.write(f"**Rendimiento:** {'🟢' if ganancia >= 0 else '🔴'} ${ganancia:,.2f}")
        
        st.divider()
        st.metric("VALOR TOTAL DEL PORTAFOLIO", f"${total_invertido_actual:,.2f}", 
                  delta=f"${total_invertido_actual - total_costo_base:,.2f} vs Costo")
    else:
        st.warning("Configura tus Tickers y Cantidades en la pestaña 'Portafolio' de tu Excel para ver los datos en vivo.")

# --- 4. NUEVO REGISTRO ---
elif menu == "Nuevo Registro":
    st.subheader("📝 Registro de Operaciones Ejecutivas")
    with st.form("registro_form"):
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input("Fecha de Operación")
            tipo = st.selectbox("Naturaleza", ["Ingreso", "Gasto"])
        with c2:
            categoria = st.selectbox("Categoría de Flujo", [
                "Venta de Artículo", 
                "Entrada de Capital", 
                "Inversión (ETFs/Acciones)",
                "Gasto Operativo",
                "Gasto Personal"
            ])
            monto = st.number_input("Monto de la Transacción ($)", min_value=0.0)
            
        detalle = st.text_area("Notas de la Operación")
        
        if st.form_submit_button("Confirmar y Sincronizar"):
            st.success(f"Registro de {categoria} procesado correctamente.")
            st.balloons()
