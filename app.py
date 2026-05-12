import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_todo():
    try:
        # Cargamos las hojas principales de tus fotos
        m = conn.read(worksheet="Movimientos", ttl="0")
        p = conn.read(worksheet="Portafolio", ttl="0")
        c = conn.read(worksheet="Creditos", ttl="0") # Asegúrate que en Excel sea 'Creditos'
        
        # Limpieza para que la IA y las gráficas funcionen
        if not m.empty and 'Monto' in m.columns:
            m['Monto'] = pd.to_numeric(m['Monto'], errors='coerce').fillna(0)
        if not c.empty and 'Saldo pendiente' in c.columns:
            c['Saldo pendiente'] = pd.to_numeric(c['Saldo pendiente'], errors='coerce').fillna(0)
            
        return m, p, c
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_mov, df_port, df_cred = cargar_todo()

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corporate")
menu = st.sidebar.selectbox("Seleccione Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

meta_ahorro = 5000

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO 1: PATRIMONIO ---
if menu == "Estado Patrimonial":
    st.header("📊 Análisis de Activos")
    if not df_mov.empty:
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        actual = ingresos - gastos
        
        c1, c2 = st.columns(2)
        c1.metric("Capital Neto Xvortice", f"${actual:,.2f}")
        c2.metric("Meta 2026", f"${meta_ahorro:,.2f}")
        st.progress(min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        st.markdown("---")
        st.subheader("🤖 Analista IA Xvortice")
        if actual < meta_ahorro:
            st.info(f"Juan, el capital actual es ${actual:,.2f}. Faltan ${meta_ahorro - actual:,.2f} para los $5,000.")
        else:
            st.success("¡Meta de $5,000 alcanzada!")
            
        st.write("### Historial de Movimientos")
        st.dataframe(df_mov, use_container_width=True)
    else:
        st.warning("No hay datos en 'Movimientos'.")

# --- MÓDULO 2: REGISTRO ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Registro de Movimiento")
    with st.form("form_reg"):
        col1, col2 = st.columns(2)
        f_fecha = col1.date_input("Fecha")
        f_user = col1.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = col2.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_cat = col2.selectbox("Categoría", ["Venta de Artículo", "Reserva de Capital", "Gasto Personal"])
        
        f_sub = st.text_input("Subcategoría")
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Comentario / Descripción")
        
        if st.form_submit_button("Guardar en la Nube"):
            nuevo = pd.DataFrame([{
                "Fecha": str(f_fecha), "Usuario": f_user, "Tipo": f_tipo, 
                "Categoria": f_cat, "Subcategoria": f_sub, "Monto": f_monto, "Comentario": f_coment
            }])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.success("✅ Guardado con éxito")
            st.rerun()

# --- MÓDULO 3: CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    
    with st.expander("➕ Registrar Nuevo Crédito"):
        with st.form("form_cred"):
            c1, c2 = st.columns(2)
            f_cli = c1.text_input("Cliente")
            f_prod = c2.text_input("Producto")
            f_sal = st.number_input("Saldo Pendiente ($)", min_value=0.0)
            f_est = st.selectbox("Estado", ["Pendiente", "Abonado", "Pagado"])
            if st.form_submit_button("Guardar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal, "Estado": f_est}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.success("✅ Crédito registrado")
                st.rerun()
    
    st.markdown("---")
    if not df_cred.empty:
        st.dataframe(df_cred, use_container_width=True)
        total_c = df_cred['Saldo pendiente'].sum()
        st.metric("Total por recuperar", f"${total_c:,.2f}")

# --- MÓDULO 4: INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Cartera Live")
    if not df_port.empty:
        st.dataframe(df_port, use_container_width=True)
    else:
        st.info("No hay acciones o ETFs registrados en 'Portafolio'.")
