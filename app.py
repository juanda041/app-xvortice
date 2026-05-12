import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# Configuración de nivel ejecutivo
st.set_page_config(page_title="Xvortice Executive", layout="wide")

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    df_m = conn.read(worksheet="Movimientos", ttl="0")
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])
    try:
        df_c = conn.read(worksheet="Creditos", ttl="0")
    except:
        df_c = pd.DataFrame(columns=["Cliente", "Producto", "Monto Total", "Saldo Pendiente", "Fecha Limite"])
    return df_m, df_p, df_c

df_mov, df_port, df_cred = cargar_datos()

# --- NAVEGACIÓN ---
st.sidebar.title("🏛️ Xvortice Corporate")
menu = st.sidebar.selectbox("Módulo Estratégico:", 
    ["Estado Patrimonial", "Gestión de Créditos", "Cartera de Inversiones", "Proyección de Riqueza", "Registro de Operaciones"])
meta_ahorro = st.sidebar.number_input("Objetivo de Capital ($)", value=5000)

# --- 1. ESTADO PATRIMONIAL ---
if menu == "Estado Patrimonial":
    st.header("🏛️ Análisis de Activos y Patrimonio")
    if not df_mov.empty:
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
            st.info(f"Juan, vas por buen camino. Tu Reserva de Capital y ventas suman ${patrimonio_liquido:,.2f}. Faltan ${faltante:,.2f} para tu meta.")
        else:
            st.success(f"¡Meta alcanzada! Tienes ${patrimonio_liquido:,.2f}. Es momento de ejecutar el plan de inversión a largo plazo.")

# --- 2. GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas (Capital en Circulación)")
    with st.expander("➕ Apertura de Nuevo Crédito"):
        with st.form("form_cred"):
            c_cliente = st.text_input("Nombre del Deudor")
            c_prod = st.text_input("Activo Entregado")
            c_monto = st.number_input("Monto de la Deuda", min_value=0.0)
            c_fecha = st.date_input("Vencimiento")
            if st.form_submit_button("Sincronizar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": c_cliente, "Producto": c_prod, "Monto Total": c_monto, "Saldo Pendiente": c_monto, "Fecha Limite": str(c_fecha)}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.success("Crédito registrado.")
    if not df_cred.empty: st.table(df_cred)

# --- 3. CARTERA DE INVERSIONES (LIVE) ---
elif menu == "Cartera de Inversiones":
    st.header("📈 Rendimiento de Capital en Bolsa")
    with st.expander("➕ Agregar Acción"):
        with st.form("form_inv"):
            t_ticker = st.text_input("Ticker (Ej: VOO)").upper()
            t_cant = st.number_input("Cantidad", min_value=0.0)
            t_pago = st.number_input("Precio Compra", min_value=0.0)
            if st.form_submit_button("Guardar Acción"):
                n_acc = pd.DataFrame([{"Ticker": t_ticker, "Cantidad": t_cant, "Precio de Compra": t_pago}])
                df_up_p = pd.concat([df_port, n_acc], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_p)
                st.success("Acción sincronizada.")
    
    if not df_port.empty:
        lista_f = []
        total_inv = 0
        for i, row in df_port.iterrows():
            stock = yf.Ticker(row['Ticker'].strip())
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor = precio * row['Cantidad']
            total_inv += valor
            lista_f.append({"Activo": row['Ticker'], "Valor": valor})
        df_fig = pd.DataFrame(lista_f)
        fig = px.pie(df_fig, values='Valor', names='Activo', hole=0.5, title="Distribución de Portafolio")
        st.plotly_chart(fig)
        st.metric("TOTAL EN INVERSIONES", f"${total_inv:,.2f}")

# --- 4. PROYECCIÓN DE RIQUEZA (CALCULADORA) ---
elif menu == "Proyección de Riqueza":
    st.header("⏳ Simulador de Interés Compuesto")
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        cap_ini = st.number_input("Capital Actual ($)", value=1000)
        aporte = st.number_input("Aporte Mensual ($)", value=200)
    with col_inv2:
        tasa = st.slider("Interés Anual Esperado (%)", 1, 20, 10)
        tiempo = st.slider("Años a futuro", 1, 30, 10)
    
    meses = tiempo * 12
    t_mensual = (tasa / 100) / 12
    valores = []
    actual = cap_ini
    for m in range(meses):
        actual = (actual + aporte) * (1 + t_mensual)
        valores.append(actual)
    
    df_proy = pd.DataFrame({"Fecha": pd.date_range(start=pd.Timestamp.now(), periods=meses, freq='M'), "Capital": valores})
    st.plotly_chart(px.area(df_proy, x="Fecha", y="Capital", title="Crecimiento de Xvortice"))
    st.success(f"En {tiempo} años tendrías aprox. **${valores[-1]:,.2f}**")

# --- 5. REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Consignación de Movimientos")
    with st.form("main_form"):
        f_fecha = st.date_input("Fecha")
        f_tipo = st.selectbox("Naturaleza", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Venta de Artículo", "Reserva de Capital", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_desc = st.text_area("Detalle")
        if st.form_submit_button("Sincronizar"):
            n_mov = pd.DataFrame([{"Fecha": str(f_fecha), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Detalle": f_desc}])
            df_up_m = pd.concat([df_mov, n_mov], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.success("Movimiento guardado con éxito.")
