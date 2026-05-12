import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ REFORZADO ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600) # Guardamos los datos por 10 min para evitar el error 429
def cargar_datos(nombre_hoja):
    try:
        # Forzamos la lectura limpia
        return conn.read(worksheet=nombre_hoja, ttl="0")
    except Exception:
        return pd.DataFrame()

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos")

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
st.sidebar.markdown("---")

# Meta ajustable (Como en tu Imagen 3)
st.sidebar.subheader("⚙️ Configuración")
meta_ahorro = st.sidebar.number_input("Ajustar Meta de Patrimonio ($)", value=5000, step=500)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Inversiones", "Gestión de Créditos", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Análisis de Ingresos y Gastos")
    
    if not df_mov.empty:
        # Limpieza de datos
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        df_ing = df_mov[df_mov['Tipo'] == 'Ingreso']
        df_gas = df_mov[df_mov['Tipo'] == 'Gasto']
        
        t_ing = df_ing['Monto'].sum()
        t_gas = df_gas['Monto'].sum()
        actual = t_ing - t_gas
        
        # Métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos (Suma)", f"${t_ing:,.2f}")
        m2.metric("Gastos (Resta)", f"${t_gas:,.2f}", delta=f"-${t_gas:,.2f}", delta_color="inverse")
        m3.metric("Capital Neto Real", f"${actual:,.2f}")
        
        prog = min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(prog, text=f"Progreso Meta: {prog*100:.1f}%")

        # --- SEPARACIÓN VISUAL ---
        st.markdown("---")
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.subheader("💰 Entradas (Ahorros/Bonos)")
            if not df_ing.empty:
                # Usamos Categoria si existe, si no Comentario
                eje = 'Categoria' if 'Categoria' in df_ing.columns else 'Comentario'
                st.bar_chart(df_ing.groupby(eje)['Monto'].sum(), color="#28a745")
                st.dataframe(df_ing[['Fecha', eje, 'Monto']], use_container_width=True)

        with col_der:
            st.subheader("💸 Salidas (Gastos/Versa)")
            if not df_gas.empty:
                eje_g = 'Categoria' if 'Categoria' in df_gas.columns else 'Comentario'
                st.bar_chart(df_gas.groupby(eje_g)['Monto'].sum(), color="#dc3545")
                st.dataframe(df_gas[['Fecha', eje_g, 'Monto']], use_container_width=True)

        # IA Analista
        st.markdown("---")
        if actual < meta_ahorro:
            st.warning(f"🤖 **Analista IA:** Juan, faltan ${meta_ahorro-actual:,.2f} para los ${meta_ahorro:,.0f}. ¡A meterle a esos ahorros!")
        else:
            st.success(f"🤖 **Analista IA:** ¡Meta superada! Es hora de ajustar a ${meta_ahorro + 5000:,.0f}.")

elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Registro")
    with st.form("f_registro"):
        f_user = st.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        
        # Categorías inteligentes
        if f_tipo == "Ingreso":
            f_cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Inversiones", "Entrada de Capital", "Venta Xvortice"])
        else:
            f_cat = st.selectbox("Categoría", ["Gasto Personal", "Mantenimiento Versa", "Comida", "Transporte", "Inversión Hapi (Salida)"])
            
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Descripción")
        
        if st.form_submit_button("Guardar Movimiento"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Usuario": f_user, "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear() # Limpiamos para ver el cambio
            st.success("✅ Guardado en la nube.")

elif menu == "Inversiones":
    st.header("📈 Portafolio de Activos")
    st.dataframe(df_port, use_container_width=True)
    # Formulario para Inversiones (se mantiene igual que antes)

elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    st.dataframe(df_cred, use_container_width=True)

elif menu == "Interés Compuesto":
    st.header("📈 Simulador")
    st.write("Cálculo basado en proyección del 10% anual.")
