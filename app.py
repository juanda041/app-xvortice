import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Xvortice App", page_icon="🚀")

st.title("📝 Registro Diario")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos existentes de la pestaña "Movimientos"
try:
    existing_data = conn.read(worksheet="Movimientos", ttl=0)
except:
    existing_data = pd.DataFrame(columns=["Fecha", "Usuario", "Monto", "Tipo", "Categoria", "Descripcion"])

# Formulario de entrada
with st.form(key="registro_form"):
    monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
    tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
    categoria = st.selectbox("Categoría", ["Xvortice", "Inversión", "Supermercado", "Personal"])
    descripcion = st.text_input("Descripción", placeholder="Ej: Venta de perfume / Super")
    
    submit_button = st.form_submit_button(label="Guardar en Excel")

if submit_button:
    # Crear nueva fila
    nueva_fila = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Usuario": "Juan",
        "Monto": monto,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descripcion": descripcion
    }])
    
    # Combinar y actualizar la pestaña "Movimientos"
    updated_df = pd.concat([existing_data, nueva_fila], ignore_index=True)
    conn.update(worksheet="Movimientos", data=updated_df)
    
    st.success("✅ ¡Guardado con éxito en la pestaña Movimientos!")
    st.balloons()
    
