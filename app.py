import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")

# --- 2. CONEXIÓN CON CACHÉ (Evita errores de conexión) ---
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
meta_ahorro = st.sidebar.number_input("Ajustar Meta ($)", value=5000, step=500)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Seleccione Módulo:", 
    ["Estado Patrimonial", "Registro de Operaciones", "Gestión de Créditos", "Inversiones", "Interés Compuesto"])

# --- 4. LÓGICA DE MÓDULOS ---

# --- MÓDULO 1: PATRIMONIO ---
if menu == "Estado Patrimonial":
    st.header("📊 Patrimonio Real (Efectivo + Inversiones)")
    if not df_mov.empty:
        # Cálculo de Efectivo
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        efectivo = ingresos - gastos
        
        # Cálculo de Inversiones
        valor_inv = 0
        if not df_port.empty:
            df_port['Cantidad'] = pd.to_numeric(df_port['Cantidad'], errors='coerce').fillna(0)
            df_port['Costo Promedio'] = pd.to_numeric(df_port['Costo Promedio'], errors='coerce').fillna(0)
            valor_inv = (df_port['Cantidad'] * df_port['Costo Promedio']).sum()
        
        total_neto = efectivo + valor_inv
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ahorro / Efectivo", f"${efectivo:,.2f}")
        c2.metric("Valor Inversiones", f"${valor_inv:,.2f}")
        c3.metric("Patrimonio Total", f"${total_neto:,.2f}")
        
        st.progress(min(total_neto/meta_ahorro, 1.0) if meta_ahorro > 0 else 0)
        
        st.markdown("---")
        st.subheader("🤖 Analista IA")
        st.info(f"Juan, tu capital total es de ${total_neto:,.2f}. El {valor_inv/total_neto*100 if total_neto > 0 else 0:.1f}% está en activos de Hapi.")
    else:
        st.info("Registra datos para ver el análisis.")

# --- MÓDULO 2: REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento (Suma o Resta)")
    with st.form("form_mov"):
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        if f_tipo == "Ingreso":
            f_cat = st.selectbox("Categoría", ["Ahorros", "Bonos", "Entrada de Capital", "Venta Xvortice"])
        else:
            f_cat = st.selectbox("Categoría", ["Gasto Personal", "Mantenimiento Versa", "Comida", "Inversión Hapi (Salida)"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_desc = st.text_area("Descripción")
        if st.form_submit_button("Guardar Movimiento"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Usuario": "Juan", "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Comentario": f_desc}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("✅ ¡Movimiento guardado!")

# --- MÓDULO 3: GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Registrar nuevo crédito"):
        with st.form("form_cred"):
            f_cli = st.text_input("Nombre del Cliente")
            f_prod = st.text_input("Producto/Servicio")
            f_sal = st.number_input("Saldo pendiente ($)", min_value=0.0)
            if st.form_submit_button("Registrar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_cred, use_container_width=True)

# --- MÓDULO 4: INVERSIONES ---
elif menu == "Inversiones":
    st.header("📈 Portafolio de Inversión (Hapi)")
    with st.expander("➕ Agregar Activo (Acción/ETF)"):
        with st.form("form_inv"):
            col1, col2 = st.columns(2)
            f_tick = col1.text_input("Ticker (Ej: VOO, NVDA)")
            f_nom = col2.text_input("Nombre del Activo")
            f_cant = col1.number_input("Cantidad de acciones", min_value=0.0, step=0.0001)
            f_cost = col2.number_input("Costo Promedio ($)", min_value=0.0)
            if st.form_submit_button("Actualizar Portafolio"):
                nueva_inv = pd.DataFrame([{"Ticker": f_tick.upper(), "Nombre": f_nom, "Cantidad": f_cant, "Costo Promedio": f_cost}])
                df_up_i = pd.concat([df_port, nueva_inv], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_i)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_port, use_container_width=True)

# --- MÓDULO 5: INTERÉS COMPUESTO ---
elif menu == "Interés Compuesto":
    st.header("📈 Simulador de Crecimiento")
    col1, col2 = st.columns(2)
    cap = col1.number_input("Capital Inicial", value=4000.0)
    años = col2.slider("Años", 1, 30, 10)
    st.success(f"### Estimación (10% anual): ${cap * (1.10**años):,.2f}")
