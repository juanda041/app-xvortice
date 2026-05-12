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
st.sidebar.subheader("⚙️ Configuración")
meta_ahorro = st.sidebar.number_input("Ajustar Meta de Patrimonio ($)", value=5000, step=500)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Módulo:", 
    ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO 1: PATRIMONIO ---
if menu == "Estado Patrimonial":
    st.header("📊 Análisis de Ingresos y Gastos")
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        df_ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']
        df_gastos = df_mov[df_mov['Tipo'] == 'Gasto']
        actual = df_ingresos['Monto'].sum() - df_gastos['Monto'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos", f"${df_ingresos['Monto'].sum():,.2f}")
        c2.metric("Gastos", f"${df_gastos['Monto'].sum():,.2f}", delta_color="inverse")
        c3.metric("Neto", f"${actual:,.2f}")
        
        st.progress(min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)

        st.markdown("---")
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.subheader("💰 Entradas")
            st.bar_chart(df_ingresos.groupby('Categoria')['Monto'].sum() if 'Categoria' in df_ingresos.columns else [])
        with col_der:
            st.subheader("💸 Salidas")
            st.bar_chart(df_gastos.groupby('Categoria')['Monto'].sum() if 'Categoria' in df_gastos.columns else [])

        st.info(f"🤖 **Analista IA:** Juan, {'vas por buen camino' if actual > 0 else 'toca revisar los gastos'}.")
    else:
        st.info("Sin datos para analizar.")

# --- MÓDULO 2: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Simulador de Crecimiento")
    col1, col2 = st.columns(2)
    cap_i = col1.number_input("Capital Inicial ($)", value=4000.0) 
    aporte = col1.number_input("Aporte Mensual ($)", value=100.0)
    años = col2.slider("Años", 1, 30, 10)
    tasa = col2.slider("Tasa Anual (%)", 1, 15, 10) / 100
    meses = años * 12
    tasa_m = tasa / 12
    final = cap_i * (1 + tasa_m)**meses + aporte * (((1 + tasa_m)**meses - 1) / tasa_m)
    st.success(f"### Proyección: ${final:,.2f}")

# --- MÓDULO 3: REGISTRO ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Registro")
    with st.form("f_reg"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Ahorros", "Inversiones", "Bonos", "Entrada de Capital", "Mantenimiento Versa", "Comida", "Otros"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Descripción")
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Usuario": "Juan", "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("✅ Guardado.")

# --- MÓDULO 4: CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Nuevo"):
        with st.form("f_cred"):
            f_cli = st.text_input("Cliente")
            f_prod = st.text_input("Producto")
            f_sal = st.number_input("Saldo ($)", min_value=0.0)
            if st.form_submit_button("Registrar"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_cred, use_container_width=True)

# --- MÓDULO 5: INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Portafolio Hapi")
    with st.expander("➕ Nueva Inversión"):
        with st.form("f_inv"):
            f_tick = st.text_input("Ticker")
            f_can = st.number_input("Cantidad", min_value=0.0)
            f_cos = st.number_input("Costo Promedio", min_value=0.0)
            if st.form_submit_button("Guardar"):
                nueva_inv = pd.DataFrame([{"Ticker": f_tick.upper(), "Cantidad": f_can, "Costo Promedio": f_cos}])
                df_up_i = pd.concat([df_port, nueva_inv], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_i)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_port, use_container_width=True)
