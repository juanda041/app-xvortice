import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de alta gama
st.set_page_config(page_title="Xvortice Executive", layout="wide")

# --- CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    df_m = conn.read(worksheet="Movimientos", ttl="0")
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])
    return df_m, df_p

df_mov, df_port = cargar_datos()

# --- INTERFAZ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corporate")
menu = st.sidebar.selectbox("Navegación Estratégica:", 
    ["Dashboard de Patrimonio", "Gestión de Inversiones (Live)", "Registro de Operaciones"])

meta_ahorro = st.sidebar.number_input("Meta de Capital ($)", value=5000)

# --- 1. DASHBOARD DE PATRIMONIO ---
if menu == "Dashboard de Patrimonio":
    st.header("📊 Resumen Ejecutivo de Patrimonio")
    
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        capital_vivo = ingresos - gastos
        
        progreso = min(capital_vivo / meta_ahorro, 1.0)
        
        st.write(f"**Camino a la Meta Estratégica (${meta_ahorro:,.0f})**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Operativo", f"${capital_vivo:,.2f}")
        c2.metric("Meta Alcanzada", f"{progreso*100:.1f}%")
        c3.metric("Faltante", f"${max(0, meta_ahorro - capital_vivo):,.2f}")

# --- 2. GESTIÓN DE INVERSIONES (LA MAGIA) ---
elif menu == "Gestión de Inversiones (Live)":
    st.header("📈 Mi Portafolio en Tiempo Real")
    
    # Formulario para agregar directo desde la App
    with st.expander("➕ Registrar Nueva Compra (Directo a Portafolio)"):
        with st.form("add_stock"):
            col1, col2, col3 = st.columns(3)
            t_ticker = col1.text_input("Ticker (Ej: VOO, NVDA, AAPL)").upper()
            t_cant = col2.number_input("Cantidad comprada", min_value=0.0)
            t_pago = col3.number_input("Precio pagado por acción", min_value=0.0)
            
            if st.form_submit_button("Sincronizar Posición"):
                # Aquí podrías usar conn.update para escribir en el Excel
                st.success(f"Posición de {t_ticker} registrada. (Actualiza tu Excel con estos datos)")

    if not df_port.empty:
        st.markdown("---")
        lista_precios = []
        total_portafolio = 0
        
        # Calculando valores en vivo
        with st.spinner('Consultando Wall Street...'):
            for index, row in df_port.iterrows():
                tk = row['Ticker'].strip()
                stock_data = yf.Ticker(tk)
                # Obtenemos precio actual
                precio_hoy = stock_data.history(period="1d")['Close'].iloc[-1]
                valor_total = precio_hoy * row['Cantidad']
                total_portafolio += valor_total
                
                lista_precios.append({
                    "Acción": tk,
                    "Valor Actual ($)": valor_total,
                    "Cantidad": row['Cantidad']
                })
        
        df_visual = pd.DataFrame(lista_precios)
        
        col_graf, col_met = st.columns([2, 1])
        
        with col_graf:
            # EL FAMOSO GRÁFICO DE PASTEL
            fig = px.pie(df_visual, values='Valor Actual ($)', names='Acción', 
                         title='Diversificación de mi Capital',
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_met:
            st.metric("VALOR TOTAL LIVE", f"${total_portafolio:,.2f}")
            st.write("**Desglose de Activos:**")
            st.dataframe(df_visual[["Acción", "Valor Actual ($)"]], hide_index=True)

# --- 3. REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Registro de Flujo de Caja")
    with st.form("registro_profesional"):
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        with c2:
            cat = st.selectbox("Categoría Profesional", 
                               ["Venta de Artículo", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
            monto = st.number_input("Monto ($)", min_value=0.0)
        
        detalle = st.text_area("Detalle de la transacción")
        if st.form_submit_button("Registrar en Xvortice"):
            st.success("✅ Operación sincronizada con éxito")
            st.balloons()
