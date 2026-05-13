import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Xvortice", layout="wide", page_icon="🏛️")
st.title("🏛️ Xvortice: Inteligencia Financiera")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leemos TODO el archivo para ver qué pestañas hay
    df = conn.read(ttl=0) 
    
    if df is not None and not df.empty:
        # Limpieza de columnas
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns={'Categoria': 'Categoría', 'Monto': 'Monto', 'Descripcion': 'Descripción'})
        
        # Si la columna 'Monto' existe, seguimos con la app normal
        if 'Monto' in df.columns:
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # Cálculos
            total_ahorro = df[df['Categoría'].str.contains('Ahorro', case=False, na=False)]['Monto'].sum()
            total_inversion = df[df['Categoría'].str.contains('Inversión|Inversion', case=False, na=False)]['Monto'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Ahorros Líquidos", f"${total_ahorro:,.2f}")
            col2.metric("Inversiones", f"${total_inversion:,.2f}")
            
            st.divider()
            st.dataframe(df, use_container_width=True)
            
            fig = px.pie(df, values='Monto', names='Categoría', title="Tu Patrimonio")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ No veo la columna 'Monto'.")
            st.write("Columnas detectadas:", df.columns.tolist())
    else:
        st.warning("⚠️ La pestaña principal está vacía.")
        st.info("Daniel, mueve la pestaña con tus datos al primer lugar (a la izquierda) en tu Excel.")

except Exception as e:
    st.error(f"Error crítico: {e}")
