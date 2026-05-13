import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Xvortice", layout="wide", page_icon="🏛️")

st.title("🏛️ Xvortice: Inteligencia Financiera")
st.divider()

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Forzamos la lectura de la hoja 1 (o la primera con datos)
    # Si tu pestaña tiene un nombre específico, ejemplo "Datos", 
    # puedes poner: worksheet="Datos" dentro de read()
    df = conn.read(ttl="0") 
    
    if df.empty:
        st.warning("⚠️ La conexión es exitosa, pero la hoja parece estar vacía.")
        st.info("Asegúrate de que tus datos estén en la primera pestaña del Excel.")
    else:
        # Limpieza de nombres de columnas (quitar espacios y tildes)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})
        df = df.dropna(how="all")
        df = df.fillna("")

        # Convertir Monto a número de forma segura
        if 'Monto' in df.columns:
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

        # --- CÁLCULOS ---
        # Buscamos de forma flexible (mayúsculas, minúsculas, con o sin tilde)
        filtro_ahorro = df['Categoría'].str.contains('Ahorro', case=False, na=False)
        filtro_inversion = df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)
        
        total_ahorro = df[filtro_ahorro]['Monto'].sum()
        total_inversion = df[filtro_inversion]['Monto'].sum()
        patrimonio = total_ahorro + total_inversion

        # --- INTERFAZ ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Patrimonio Total", f"${patrimonio:,.2f}")
        col2.metric("Ahorros Líquidos", f"${total_ahorro:,.2f}")
        col3.metric("Meta 2026", "$5,000.00", f"{(total_ahorro - 5000):,.2f}")

        tab1, tab2 = st.tabs(["📊 Gráficas", "📝 Datos Reales"])
        
        with tab1:
            fig = px.pie(df, values='Monto', names='Categoría', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Hubo un detalle al leer el Excel: {e}")
    st.info("Intenta refrescar la página de Streamlit.")
