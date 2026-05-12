import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de nivel ejecutivo
st.set_page_config(page_title="Xvortice Executive", layout="wide")

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # Cargamos movimientos
    df_m = conn.read(worksheet="Movimientos", ttl="0")
    # Cargamos portafolio
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])
    return df_m, df_p

df_mov, df_port = cargar_datos()

# --- NAVEGACIÓN ---
st.sidebar.title("🏛️ Xvortice Menu")
menu = st.sidebar.selectbox("Módulo:", ["Dashboard & Meta", "Inversiones (Live)", "Nuevo Registro"])
meta_ahorro = st.sidebar.number_input("Meta Actual ($)", value=5000)

# --- 1. DASHBOARD COMPLETO ---
if menu == "Dashboard & Meta":
    st.header("📊 Resumen General de Patrimonio")
    
    if not df_mov.empty:
        # Limpieza de datos
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        capital_total = ingresos - gastos
        
        # Barra de progreso
        progreso = min(capital_total / meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        st.write(f"**Progreso hacia tu meta de ${meta_ahorro:,.0f}**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital en Caja", f"${capital_total:,.2f}")
        c2.metric("Meta Alcanzada", f"{progreso*100:.1f}%")
        c3.metric("Faltante", f"${max(0, meta_ahorro - capital_total):,.2f}")
        
        st.info(f"🤖 **Analista Xvortice:** Juan, tienes el {progreso*100:.1f}% de tu objetivo. ¡Dale duro a las ventas!")

# --- 2. INVERSIONES CON GRÁFICO Y REGISTRO ---
elif menu == "Inversiones (Live)":
    st.header("📈 Mi Portafolio en Tiempo Real")
    
    # Formulario para agregar acciones desde la App
    with st.expander("➕ Agregar Acción al Portafolio (Sin Excel)"):
        with st.form("form_inv"):
            col1, col2, col3 = st.columns(3)
            t_ticker = col1.text_input("Ticker (Ej: VOO, NVDA)").upper()
            t_cant = col2.number_input("Cantidad", min_value=0.0)
            t_pago = col3.number_input("Precio Compra", min_value=0.0)
            
            if st.form_submit_button("Sincronizar"):
                nueva_accion = pd.DataFrame([{"Ticker": t_ticker, "Cantidad": t_cant, "Precio de Compra": t_pago}])
                df_up = pd.concat([df_port, nueva_accion], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up)
                st.success("¡Acción guardada! Refresca para ver el gráfico.")
                st.balloons()

    if not df_port.empty:
        # Cálculo de valores Live
        lista_final = []
        total_live = 0
        for i, row in df_port.iterrows():
            ticker = row['Ticker'].strip()
            # Consultar precio actual
            stock = yf.Ticker(ticker)
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor_posicion = precio * row['Cantidad']
            total_live += valor_posicion
            lista_final.append({"Acción": ticker, "Valor": valor_posicion})
        
        # Gráfico de Pastel
        df_fig = pd.DataFrame(lista_final)
        fig = px.pie(df_fig, values='Valor', names='Acción', hole=0.4, title="Distribución de mi Capital")
        
        c_inv1, c_inv2 = st.columns([2,1])
        c_inv1.plotly_chart(fig, use_container_width=True)
        c_inv2.metric("VALOR TOTAL EN BOLSA", f"${total_live:,.2f}")
        c_inv2.dataframe(df_fig, hide_index=True)

# --- 3. REGISTRO PROFESIONAL ---
elif menu == "Nuevo Registro":
    st.header("📝 Registro de Operaciones")
    with st.form("main_form"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            f_fecha = st.date_input("Fecha")
            f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        with col_r2:
            f_cat = st.selectbox("Categoría Profesional", 
                               ["Venta de Artículo", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
            f_monto = st.number_input("Monto ($)", min_value=0.0)
        
        f_desc = st.text_area("Detalle")
        
        if st.form_submit_button("Guardar Registro"):
            # Lógica para guardar movimientos (Ventas/Gastos)
            nuevo_mov = pd.DataFrame([{"Fecha": str(f_fecha), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Detalle": f_desc}])
            df_final_mov = pd.concat([df_mov, nuevo_mov], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_final_mov)
            st.success("✅ ¡Registro guardado en Movimientos!")
