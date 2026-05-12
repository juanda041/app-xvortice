import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Xvortice Executive", layout="wide")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    df_m = conn.read(worksheet="Movimientos", ttl="0")
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])
    return df_m, df_p

df_mov, df_port = cargar_datos()

# --- MENÚ ---
st.sidebar.title("🏛️ Xvortice Menu")
menu = st.sidebar.selectbox("Módulo:", ["Dashboard", "Inversiones (Live)", "Nuevo Registro"])

# --- MODULO DE INVERSIONES CON GUARDADO DIRECTO ---
if menu == "Inversiones (Live)":
    st.header("📈 Mi Portafolio en Tiempo Real")
    
    with st.expander("➕ Agregar Acción Directo desde la App"):
        with st.form("form_acciones"):
            col1, col2, col3 = st.columns(3)
            t_ticker = col1.text_input("Ticker (Ej: VOO)").upper()
            t_cant = col2.number_input("Cantidad", min_value=0.0)
            t_pago = col3.number_input("Precio de Compra", min_value=0.0)
            
            if st.form_submit_button("Guardar en Portafolio"):
                # CREAMOS EL NUEVO DATO
                nueva_fila = pd.DataFrame([{"Ticker": t_ticker, "Cantidad": t_cant, "Precio de Compra": t_pago}])
                # LO JUNTAMOS CON LO QUE YA EXISTE
                df_actualizado = pd.concat([df_port, nueva_fila], ignore_index=True)
                # ¡LA MAGIA! LO MANDA AL EXCEL
                conn.update(worksheet="Portafolio", data=df_actualizado)
                st.success(f"✅ {t_ticker} guardado. ¡Refresca la página para ver el cambio!")
                st.balloons()

    # --- GRÁFICO DE PASTEL ---
    if not df_port.empty:
        total_port = 0
        datos_grafico = []
        for index, row in df_port.iterrows():
            tk = row['Ticker'].strip()
            stock = yf.Ticker(tk)
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor = precio * row['Cantidad']
            total_port += valor
            datos_grafico.append({"Acción": tk, "Valor": valor})
        
        df_fig = pd.DataFrame(datos_grafico)
        fig = px.pie(df_fig, values='Valor', names='Acción', title="Distribución de mi Capital", hole=.4)
        st.plotly_chart(fig)
        st.metric("VALOR TOTAL", f"${total_port:,.2f}")

# --- RESTO DE SECCIONES (Dashboard y Registro) ---
elif menu == "Dashboard":
    st.header("Resumen General")
    st.write("Aquí verás tus metas.")

elif menu == "Nuevo Registro":
    st.header("Registro de Ventas")
    # Formulario de ventas...
