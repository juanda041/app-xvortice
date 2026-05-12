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
        df = conn.read(worksheet=nombre_hoja, ttl="0")
        return df
    except Exception:
        return pd.DataFrame()

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos") 

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
st.sidebar.markdown("---")
# Aquí cambias la meta cuando quieras
meta_ahorro = st.sidebar.number_input("🎯 Ajustar Meta ($)", value=5000, step=500)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Seleccione Módulo:", 
    ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Resumen de Capital")
    if not df_mov.empty:
        # Limpieza de datos para evitar el error de los 400 mil dólares
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        actual = ingresos - gastos
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Neto", f"${actual:,.2f}")
        c2.metric("Gastos Totales", f"${gastos:,.2f}", delta_color="inverse")
        c3.metric("Meta", f"${meta_ahorro:,.2f}")
        
        progreso = min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(progreso, text=f"Progreso: {progreso*100:.1f}%")

        # --- ANÁLISIS DE GASTOS ---
        st.markdown("---")
        st.subheader("💸 ¿En qué se va el dinero?")
        df_gastos = df_mov[df_mov['Tipo'] == 'Gasto']
        if not df_gastos.empty:
            # Si no tienes columna 'Categoria', usamos 'Comentario'
            col_agrupar = 'Categoria' if 'Categoria' in df_gastos.columns else 'Comentario'
            resumen_gastos = df_gastos.groupby(col_agrupar)['Monto'].sum()
            st.bar_chart(resumen_gastos)
        
        # --- IA ANALISTA ---
        st.info(f"🤖 **Analista IA:** Juan, {'¡vas volando!' if actual >= meta_ahorro else f'faltan ${meta_ahorro-actual:,.2f} para la meta.'}")

    else:
        st.warning("No hay datos en Movimientos. Registra algo nuevo.")

elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento")
    with st.form("f_reg"):
        f_user = st.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        # CATEGORÍAS NUEVAS PARA TU GRÁFICO
        f_cat = st.selectbox("Categoría", ["Inversión Hapi", "Comida", "Versa (Gas/Mec)", "Venta Xvortice", "Préstamo", "Personal", "Otro"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Comentario")
        if st.form_submit_button("Guardar en Excel"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Usuario": f_user, "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("✅ ¡Guardado con éxito!")

# --- Módulos de Créditos, Inversiones e Interés se mantienen igual para no borrar nada ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    st.dataframe(df_cred, use_container_width=True)

elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi")
    st.dataframe(df_port, use_container_width=True)

elif menu == "Interés Compuesto":
    st.header("📈 Simulador")
    cap = st.number_input("Capital", value=4000.0)
    st.write(f"Proyección simple: {cap * 1.10:,.2f} a un año (10%)")
