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
    except Exception as e:
        return pd.DataFrame()

df_mov = cargar_datos("Movimientos")
df_port = cargar_datos("Portafolio")
df_cred = cargar_datos("Creditos") 

# --- 3. MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
menu = st.sidebar.selectbox("Seleccione Módulo:", 
    ["Estado Patrimonial", "Interés Compuesto", "Registro de Operaciones", "Gestión de Créditos", "Inversiones"])

meta_ahorro = 5000

# --- 4. LÓGICA DE MÓDULOS ---

if menu == "Estado Patrimonial":
    st.header("📊 Resumen de Capital")
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        actual = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum() - df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Capital Neto Real", f"${actual:,.2f}")
        c2.metric("Meta 2026", f"${meta_ahorro:,.2f}")
        
        progreso = min(actual/meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.progress(progreso)

        st.markdown("---")
        st.subheader("🤖 Analista IA Xvortice")
        
        col_ia, col_tip = st.columns([2, 1])
        
        with col_ia:
            if actual < 2000:
                st.warning(f"Juan, estamos en fase de acumulación. Faltan ${meta_ahorro - actual:,.2f} para la primera meta grande.")
            elif 2000 <= actual < 5000:
                st.info(f"¡Excelente ritmo! Llevas un {progreso*100:.1f}% de la meta.")
            else:
                st.success("¡Meta de $5,000 alcanzada! Vamos por el siguiente nivel.")

        with col_tip:
            # AQUÍ ESTÁ EL CAMBIO: Usamos st.info con un icono de bombilla
            consejos = [
                "Revisa el costo promedio de NVDA antes de comprar más.",
                "El ahorro constante biweekly es tu mejor arma.",
                "No olvides registrar las ventas de perfumes hoy.",
                "¿Ya revisaste el nivel de aceite del Versa?"
            ]
            st.info(f"💡 **Tip del día:** {np.random.choice(consejos)}")
        
        st.markdown("---")
        st.write("### Historial de Movimientos")
        st.dataframe(df_mov, use_container_width=True)
    else:
        st.info("Cargando datos...")

elif menu == "Interés Compuesto":
    st.header("📈 Proyección de Crecimiento")
    col1, col2 = st.columns(2)
    cap_i = col1.number_input("Capital Inicial ($)", value=4000.0) 
    aporte = col1.number_input("Aporte Mensual ($)", value=100.0)
    años = col2.slider("Años", 1, 30, 10)
    tasa = col2.slider("Tasa Anual (%)", 1, 15, 10) / 100
    meses = años * 12
    tasa_m = tasa / 12
    final = cap_i * (1 + tasa_m)**meses + aporte * (((1 + tasa_m)**meses - 1) / tasa_m)
    st.success(f"### Estimación en {años} años: ${final:,.2f}")

elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento")
    with st.form("form_registro"):
        f_user = st.selectbox("Usuario", ["Juan Daniel", "Jenny"])
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_coment = st.text_area("Comentario")
        if st.form_submit_button("Guardar en Excel"):
            nuevo = pd.DataFrame([{"Fecha": str(pd.Timestamp.now().date()), "Usuario": f_user, "Tipo": f_tipo, "Monto": f_monto, "Comentario": f_coment}])
            df_up = pd.concat([df_mov, nuevo], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up)
            st.cache_data.clear()
            st.success("✅ Guardado.")

elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas por Cobrar")
    with st.expander("➕ Agregar nuevo crédito"):
        with st.form("f_cred"):
            f_cli = st.text_input("Cliente")
            f_prod = st.text_input("Producto")
            f_sal = st.number_input("Saldo pendiente ($)", min_value=0.0)
            if st.form_submit_button("Registrar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": f_cli, "Producto": f_prod, "Saldo pendiente": f_sal}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_cred, use_container_width=True)

elif menu == "Inversiones":
    st.header("📈 Cartera de Inversión")
    with st.expander("➕ Registrar Nueva Inversión"):
        with st.form("f_inv"):
            col_a, col_b = st.columns(2)
            f_ticker = col_a.text_input("Ticker")
            f_nombre = col_b.text_input("Nombre")
            f_cant = col_a.number_input("Cantidad", min_value=0.0, step=0.01)
            f_costo = col_b.number_input("Costo Promedio ($)", min_value=0.0, step=0.01)
            if st.form_submit_button("Guardar"):
                nueva_inv = pd.DataFrame([{"Ticker": f_ticker.upper(), "Nombre": f_nombre, "Cantidad": f_cant, "Costo Promedio": f_costo}])
                df_up_i = pd.concat([df_port, nueva_inv], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_i)
                st.cache_data.clear()
                st.rerun()
    st.dataframe(df_port, use_container_width=True)
