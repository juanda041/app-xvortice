import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
from datetime import datetime

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
            st.info(f"Juan, vas por buen camino. Faltan ${faltante:,.2f} para tu meta de ${meta_ahorro}.")
        else:
            st.success("¡Meta alcanzada!")

# --- 2. GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas")
    if not df_cred.empty: st.table(df_cred)

# --- 3. CARTERA DE INVERSIONES ---
elif menu == "Cartera de Inversiones":
    st.header("📈 Cartera Live")
    if not df_port.empty:
        lista_f = []
        for i, row in df_port.iterrows():
            stock = yf.Ticker(row['Ticker'].strip())
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor = precio * row['Cantidad']
            lista_f.append({"Activo": row['Ticker'], "Valor": valor})
        df_fig = pd.DataFrame(lista_f)
        fig = px.pie(df_fig, values='Valor', names='Activo', hole=0.5)
        st.plotly_chart(fig)

# --- 4. PROYECCIÓN DE RIQUEZA (CORREGIDO) ---
elif menu == "Proyección de Riqueza":
    st.header("⏳ Simulador de Interés Compuesto")
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        cap_ini = st.number_input("Capital Actual ($)", value=1000)
        aporte = st.number_input("Aporte Mensual ($)", value=200)
    with col_inv2:
        tasa = st.slider("Interés Anual Esperado (%)", 1, 20, 10)
        tiempo = st.slider("Años a futuro", 1, 30, 10)
    
    meses_total = tiempo * 12
    t_mensual = (tasa / 100) / 12
    
    fechas = []
    valores = []
    actual = cap_ini
    fecha_actual = datetime.now()
    
    for m in range(meses_total):
        actual = (actual + aporte) * (1 + t_mensual)
        valores.append(actual)
        # Generar lista de meses manualmente para evitar el error de Pandas
        fechas.append(m) 
    
    df_proy = pd.DataFrame({"Mes": fechas, "Capital Estimado": valores})
    
    # Usamos el número de mes en el eje X para que sea infalible
    fig_proy = px.area(df_proy, x="Mes", y="Capital Estimado", 
                       title=f"Evolución del Capital en {tiempo} años",
                       labels={"Mes": "Meses desde hoy"})
    
    st.plotly_chart(fig_proy, use_container_width=True)
    st.success(f"En {tiempo} años, el patrimonio estimado de Xvortice sería: **${valores[-1]:,.2f}**")

# --- 5. REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Nuevo Movimiento")
    with st.form("main_form"):
        f_fecha = st.date_input("Fecha")
        f_tipo = st.selectbox("Naturaleza", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Venta de Artículo", "Reserva de Capital", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        if st.form_submit_button("Sincronizar"):
            n_mov = pd.DataFrame([{"Fecha": str(f_fecha), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto}])
            df_up_m = pd.concat([df_mov, n_mov], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.success("Guardado.")
