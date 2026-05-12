import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) 
def cargar_datos(nombre_hoja):
    try:
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except Exception:
        return pd.DataFrame()

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos") 

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
st.sidebar.markdown("---")

# Meta ajustable por el usuario
st.sidebar.subheader("⚙️ Configuración")
meta_ahorro = st.sidebar.number_input("Ajustar Meta de Patrimonio ($)", value=5000, step=500)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO 1: PATRIMONIO (SEPARADO Y CON IA) ---
if menu == "Estado Patrimonial":
    st.header("📊 Análisis de Ingresos y Gastos")
    
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        
        # Filtrado para cálculos
        df_ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']
        df_gastos = df_mov[df_mov['Tipo'] == 'Gasto']
        
        total_ingresos = df_ingresos['Monto'].sum()
        total_gastos = df_gastos['Monto'].sum()
        actual = total_ingresos - total_gastos
        
        # Métricas de resumen
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos (Suma)", f"${total_ingresos:,.2f}")
        c2.metric("Gastos (Resta)", f"${total_gastos:,.2f}", delta=f"-${total_gastos:,.2f}", delta_color="inverse")
        c3.metric("Capital Neto Real", f"${actual:,.2f}")
        
        progreso = min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(progreso, text=f"Progreso hacia la meta de ${meta_ahorro:,.0f}: {progreso*100:.1f}%")

        # --- VISTA EN DOS COLUMNAS ---
        st.markdown("---")
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.subheader("💰 Entradas de Capital")
            if not df_ingresos.empty:
                cat_ing = 'Categoria' if 'Categoria' in df_ingresos.columns else 'Comentario'
                res_ing = df_ingresos.groupby(cat_ing)['Monto'].sum()
                st.bar_chart(res_ing, color="#28a745")
                st.dataframe(df_ingresos, use_container_width=True)
            else: st.info("No hay ingresos.")

        with col_der:
            st.subheader("💸 Salidas y Gastos")
            if not df_gastos.empty:
                cat_gas = 'Categoria' if 'Categoria' in df_gastos.columns else 'Comentario'
                res_gas = df_gastos.groupby(cat_gas)['Monto'].sum()
                st.bar_chart(res_gas, color="#dc3545")
                st.dataframe(df_gastos, use_container_width=True)
            else: st.info("No hay gastos.")

        # --- ANALISTA IA ---
        st.markdown("---")
        st.subheader("🤖 Analista IA Xvortice")
        col_ia, col_tip = st.columns([2, 1])
        with col_ia:
            if actual < meta_ahorro:
                st.warning(f"Juan, faltan ${meta_ahorro - actual:,.2f} para la meta. Tus ingresos son sólidos, pero vigila las salidas.")
            else:
                st.success(f"¡Felicidades! Meta de ${meta_ahorro:,.2f} superada. ¿Subimos el nivel?")
        with col_tip:
            consejos = ["Ahorra el 10% de cada bono.", "Revisa el costo promedio en Hapi.", "Controla los gastos del Versa."]
            st.info(f"💡 **Tip:** {np.random.choice(consejos)}")
    else:
        st.info("Registra tu primer movimiento para ver el análisis.")

# --- MÓDULO 2: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Simul
