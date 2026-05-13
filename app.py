import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Xvortice Test")
st.title("🏛️ Xvortice: Prueba de Conexión")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Movimientos", ttl="1s")
    
    if not df.empty:
        st.success("¡Conexión Exitosa con Google Sheets!")
        st.write("Últimos movimientos registrados:")
        st.dataframe(df.tail(5))
    else:
        st.warning("La hoja está vacía o no se encuentra.")
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Revisa si las 'Secrets' de Streamlit siguen configuradas.")
