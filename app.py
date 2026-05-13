import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuración Pro
st.set_page_config(page_title="Xvortice", layout="wide", page_icon="🏛️")
st.title("🏛️ Xvortice: Inteligencia Financiera")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # FORZAMOS a que lea la pestaña "Movimientos" que es donde tienes los datos
    df = conn.read(worksheet="Movimientos", ttl=0) 
    
    if df is not None and not df.empty:
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Diccionario para corregir nombres (con o sin tilde)
        df = df.rename(columns={
            'Categoria': 'Categoría', 
            'Monto': 'Monto', 
            'Descripcion': 'Descripción'
        })
        
        df = df.dropna(how="all")
        df = df.fillna("")

        # Asegurar que Monto sea número
        if 'Monto' in df.columns:
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)

            # Cálculos de Patrimonio
            total_ahorro = df[df['Categoría'].str.contains('Ahorro', case=False, na=False)]['Monto'].sum()
            total_otros = df[df['Categoría'].str.contains('Otros', case=False, na=False)]['Monto'].sum()
            patrimonio = total_ahorro + total_otros

            # Dashboard Superior
            col1, col2, col3 = st.columns(3)
            col1.metric("Patrimonio Actual", f"${patrimonio:,.2f}")
            col2.metric("Ahorros Líquidos", f"${total_ahorro:,.2f}")
            col3.metric("Meta 2026", "$5,000.00", f"{(total_ahorro - 5000):,.2f}")

            st.divider()
            
            # Pestañas de Visualización
            tab1, tab2 = st.tabs(["📊 Análisis Visual", "📝 Registro de Movimientos"])
            
            with tab1:
                fig = px.pie(df, values='Monto', names='Categoría', hole=0.4, title="Distribución de Activos")
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                # Buscador rápido
                busqueda = st.text_input("🔍 Buscar por descripción o comentario:")
                if busqueda:
                    df_res = df[df.apply(lambda r: busqueda.lower() in str(r).lower(), axis=1)]
                    st.dataframe(df_res, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
                    
    else:
        st.error("No se pudieron cargar datos de la pestaña 'Movimientos'.")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Asegúrate de que la pestaña en tu Excel se llame exactamente 'Movimientos'.")
