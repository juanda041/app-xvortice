import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="Xvortice - Gestión Patrimonial", layout="wide")

st.title("🏛️ Xvortice")
st.subheader("Control de Capital e Inversiones")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer los datos (ajusta 'Hoja 1' al nombre real de tu pestaña principal si es necesario)
df = conn.read()

# Limpieza rápida: quitar filas vacías y convertir "None" en espacios en blanco
df = df.dropna(how="all")
df = df.fillna("")

# --- VISTA DE PATRIMONIO ---
total_ahorro = df[df['Categoría'] == 'Ahorro']['Monto'].sum()
total_inversion = df[df['Categoría'] == 'Inversión']['Monto'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Ahorro Total", f"${total_ahorro:,.2f}")
col2.metric("Inversiones", f"${total_inversion:,.2f}")
col3.metric("Meta 2026", "$5,000.00", f"{total_ahorro - 5000:,.2f}")

# --- TABLA FORMATEADA ---
st.write("### Registros Recientes")
# Mostramos solo las columnas importantes para que no se vea desordenado
columnas_visibles = ["Fecha", "Categoría", "Subcategoría", "Monto", "Detalle"]
st.dataframe(df[columnas_visibles], use_container_width=True)
