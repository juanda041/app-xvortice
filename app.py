import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

# Estilo Daniel
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Control Maestro")

conn = st.connection("gsheets", type=GSheetsConnection)

def clean_df(df):
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    # 1. CARGA DE DATOS
    movs = clean_df(conn.read(worksheet="Movimientos", ttl=0).dropna(how='all'))
    port = clean_df(conn.read(worksheet="Portafolio", ttl=0).dropna(how='all'))
    cred = clean_df(conn.read(worksheet="Creditos", ttl=0).dropna(how='all'))

    # 2. CÁLCULOS (Portafolio, Liquidez, Cobros)
    valor_acciones_hoy = 0
    port_resumen = port.groupby('Ticker')['Cantidad'].sum().reset_index()
    for _, row in port_resumen.iterrows():
        tk = str(row['Ticker']).upper()
        if tk not in ["CASH", "NAN", ""]:
            try:
                price = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                valor_acciones_hoy += (float(row['Cantidad']) * price)
            except: continue

    ingresos = movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    gastos_p = movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    liquidez = ingresos - gastos_p
    
    col_saldo = [c for c in cred.columns if 'saldo' in c.lower()][0]
    total_por_cobrar = pd.to_numeric(cred[col_saldo], errors='coerce').sum()
    patrimonio = liquidez + valor_acciones_hoy + total_por_cobrar

    # 3. DASHBOARD
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    c2.metric("Portafolio", f"${valor_acciones_hoy:,.2f}")
    c3.metric("Liquidez", f"${liquidez:,.2f}")
    c4.metric("Por Cobrar", f"${total_por_cobrar:,.2f}")

    # 4. PESTAÑAS (Aquí añadimos la EDICIÓN)
    t1, t2, t3, t4 = st.tabs(["📝 Registrar Datos", "📊 Mis Tablas", "💹 Futuro", "🤖 IA"])

    with t1:
        st.subheader("Añadir Nueva Información")
        opcion = st.radio("¿Qué quieres registrar?", ["Movimiento (Efectivo)", "Venta a Crédito", "Compra de Acción"], horizontal=True)
        
        with st.form("form_edicion"):
            if opcion == "Movimiento (Efectivo)":
                fecha = st.date_input("Fecha", datetime.now())
                tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
                cat = st.text_input("Categoría (Ahorros, Comida, etc.)")
                monto = st.number_input("Monto ($)", min_value=0.0)
                if st.form_submit_button("Guardar en Excel"):
                    new_row = pd.DataFrame([[fecha, "Juan", tipo, cat, "", monto, "", ""]], columns=movs.columns)
                    movs = pd.concat([movs, new_row], ignore_index=True)
                    conn.update(worksheet="Movimientos", data=movs)
                    st.success("¡Movimiento guardado!")

            elif opcion == "Venta a Crédito":
                cliente = st.text_input("Nombre del Cliente")
                producto = st.text_input("Producto (Ej: Celular)")
                monto_t = st.number_input("Monto Total", min_value=0.0)
                if st.form_submit_button("Registrar Crédito"):
                    # Esta lógica resta de liquidez y sube a cuentas por cobrar automáticamente al actualizar el Excel
                    new_cred = pd.DataFrame([[cliente, producto, monto_t, monto_t, ""]], columns=cred.columns[:5])
                    cred = pd.concat([cred, new_cred], ignore_index=True)
                    conn.update(worksheet="Creditos", data=cred)
                    st.success(f"Crédito para {cliente} registrado.")

            elif opcion == "Compra de Acción":
                ticker_new = st.text_input("Ticker (Ej: NVDA, BAC)")
                cant_new = st.number_input("Cantidad de acciones", min_value=0.0)
                if st.form_submit_button("Actualizar Portafolio"):
                    new_port = pd.DataFrame([[ticker_new.upper(), cant_new, 0, 0, ""]], columns=port.columns)
                    port = pd.concat([port, new_port], ignore_index=True)
                    conn.update(worksheet="Portafolio", data=port)
                    st.success(f"Portafolio actualizado con {ticker_new}.")

    with t2:
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("**Historial de Movimientos**")
            st.dataframe(movs.tail(10), use_container_width=True)
        with col_r:
            st.write("**Deudas Pendientes**")
            st.dataframe(cred, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
