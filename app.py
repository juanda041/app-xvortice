import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuración Pro
st.set_page_config(page_title="Xvortice - Gestión Patrimonial", layout="wide", page_icon="🏛️")

st.title("🏛️ Xvortice: Inteligencia Financiera")
st.divider()

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leer datos y limpiar
    df = conn.read(ttl="0")
    df = df.dropna(how="all")
    
    # --- AJUSTE DE COLUMNAS (Para que no importe la tilde) ---
    # Renombramos las columnas si vienen sin tilde o con nombres parecidos
    columnas_dict = {
        'Categoria': 'Categoría',
        'Descripcion': 'Descripción'
    }
    df = df.rename(columns=columnas_dict)
    df = df.fillna("")

    # Asegurar que Monto sea número
    if 'Monto' in df.columns:
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

    # --- LÓGICA DE NEGOCIO ---
    # Buscamos "Ahorros" o "Ahorro" de forma flexible
    ahorros = df[df['Categoría'].str.contains('Ahorro', case=False, na=False)]['Monto'].sum()
    inversiones = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()
    otros = df[df['Categoría'].str.contains('Otros', case=False, na=False)]['Monto'].sum()
    
    patrimonio_total = ahorros + inversiones + otros

    # --- DASHBOARD ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Patrimonio Actual", f"${patrimonio_total:,.2f}")
    col2.metric("Meta de Ahorro", "$5,000.00", f"{ahorros - 5000:,.2f}")
    col3.metric("En Caja/Ahorros", f"${ahorros:,.2f}")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Gráficas", "📝 Registros", "🤖 IA"])

    with tab1:
        if patrimonio_total > 0:
            fig = px.pie(df, values='Monto', names='Categoría', hole=0.4, title="Distribución de Capital")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Agrega montos en el Excel para ver la gráfica.")

    with tab2:
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.info("Daniel, tu sistema Xvortice está activo. Según tus registros, el ahorro actual es de $" + str(ahorros))

except Exception as e:
    st.error(f"Error detectado: {e}")
    st.write("Columnas que veo en tu Excel:", df.columns.tolist())
