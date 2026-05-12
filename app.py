import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xvortice Corporate", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN INTELIGENTE CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) # Cache de 5 min para no saturar la conexión
def cargar_todo():
    try:
        # Cargamos las 4 hojas que vi en tus fotos
        m = conn.read(worksheet="Movimientos", ttl="0")
        p = conn.read(worksheet="Portafolio", ttl="0")
        c = conn.read(worksheet="creditos", ttl="0")
        conf = conn.read(worksheet="Configuracion", ttl="0")
        
        # Limpieza de Montos para que la IA pueda sumar
        for df in [m, c]:
            col_monto = 'Monto' if 'Monto' in df.columns else 'Monto Total'
            if col_monto in df.columns:
                df[col_monto] = pd.to_numeric(df[col_monto], errors='coerce').fillna(0)
        return m, p, c, conf
    except Exception as e:
        st.error(f"Error cargando hojas: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mov, df_port, df_cred, df_conf = cargar_todo()

# --- 3. INTERFAZ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corporate")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo Estratégico:", 
    ["Estado Patrimonial", "Gestión de Créditos", "Cartera de Inversiones", "Registro de Operaciones"])

meta_ahorro = st.sidebar.number_input("Objetivo de Capital ($)", value=5000)

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Análisis de Activos y Patrimonio")
    if not df_mov.empty:
        # Cálculo basado en tu columna 'Tipo' y 'Monto' (Foto 6)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        total_actual = ingresos - gastos
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Xvortice", f"${total_actual:,.2f}")
        c2.metric("Meta 2026", f"${meta_ahorro:,.2f}")
        c3.metric("Faltante", f"${max(0, meta_ahorro - total_actual):,.2f}")
        
        st.progress(min(total_actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        # Analista IA
        st.info(f"💡 **Analista Xvortice:** Tienes un flujo neto de ${total_actual:,.2f}. Tu reserva de capital es el pilar de tu expansión.")
        
        st.subheader("📝 Historial de Movimientos (Vista Excel)")
        st.dataframe(df_mov) # Muestra todas tus columnas: Usuario, Comentario, etc.
    else:
        st.warning("No hay datos en 'Movimientos'.")

elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas")
    if not df_cred.empty:
        st.dataframe(df_cred) # Basado en columnas de Foto 8: Cliente, Producto, Saldo
        total_por_cobrar = df_cred['Saldo pendiente'].sum() if 'Saldo pendiente' in df_cred.columns else 0
        st.success(f"Total por recuperar: ${total_por_cobrar:,.2f}")
    else:
        st.info("No hay créditos pendientes registrados.")

elif menu == "Cartera de Inversiones":
    st.header("📈 Cartera Live")
    if not df_port.empty and 'Ticker' in df_port.columns:
        # Sistema anti-bloqueo para yfinance
        try:
            tickers = " ".join(df_port['Ticker'].tolist())
            data = yf.download(tickers, period="1d")['Close'].iloc[-1]
            
            df_resumen = df_port.copy()
            df_resumen['Precio Actual'] = df_resumen['Ticker'].map(data)
            df_resumen['Valor Total'] = df_resumen['Cantidad'] * df_resumen['Precio Actual']
            st.dataframe(df_resumen)
            st.plotly_chart(px.pie(df_resumen, values='Valor Total', names='Ticker', title="Distribución de Activos"))
        except:
            st.warning("⚠️ El mercado está cerrado o hay mucha demanda. Mostrando datos locales.")
            st.dataframe(df_port)
    else:
        st.info("Registra tus ETFs o Acciones en la hoja 'Portafolio'.")

elif menu == "Registro de Operaciones":
    st.header("➕ Registrar Nueva Operación")
    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        fecha = col1.date_input("Fecha")
        usuario = col1.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        tipo = col2.selectbox("Tipo", ["Ingreso", "Gasto"])
        cat = col2.selectbox("Categoría", ["Venta de Artículo", "Reserva de Capital", "Otros"])
        monto = st.number_input("Monto ($)", min_value=0.0)
        coment = st.text_input("Comentario")
        
        if st.form_submit_button("Confirmar Registro"):
            # Creamos el registro con TODAS tus columnas (Foto 6)
            nuevo_dato = pd.DataFrame([{
                "Fecha": str(fecha), "Usuario": usuario, "Tipo": tipo, 
                "Categoria": cat, "Monto": monto, "Comentario": coment
            }])
            df_actualizado = pd.concat([df_mov, nuevo_dato], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_actualizado)
            st.success("✅ Datos guardados en la nube.")
            st.cache_data.clear()
            st.rerun()
