import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

# Estilo Negro Daniel
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Control Maestro")

conn = st.connection("gsheets", type=GSheetsConnection)

def clean_df(df):
    """Limpia columnas repetidas para evitar el error de las fotos 6 y 7"""
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    # 1. CARGA SEGURA
    movs = clean_df(conn.read(worksheet="Movimientos", ttl=0).dropna(how='all'))
    port = clean_df(conn.read(worksheet="Portafolio", ttl=0).dropna(how='all'))
    cred = clean_df(conn.read(worksheet="Creditos", ttl=0).dropna(how='all'))

    # 2. MONITOR LATERAL (Solo tus tickers de la foto 2)
    valor_acciones_hoy = 0
    with st.sidebar:
        st.header("📈 Mercado Real")
        # Consolidamos: si tienes BAC en varias filas, las suma
        port_resumen = port.groupby('Ticker')['Cantidad'].sum().reset_index()
        for _, row in port_resumen.iterrows():
            tk = str(row['Ticker']).upper()
            cant = float(row['Cantidad'])
            if tk not in ["CASH", "NAN", ""]:
                try:
                    price = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                    valor_acciones_hoy += (cant * price)
                    st.write(f"**{tk}:** ${price:,.2f}")
                except: continue
        st.divider()
        meta = st.number_input("🎯 Meta Personal", value=10000)

    # 3. LÓGICA DE PATRIMONIO (Fórmula Daniel)
    # Liquidez: Ingresos - Gastos Personales (de la foto 1)
    ingresos = movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'].sum()
    gastos_p = movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'].sum()
    liquidez = ingresos - gastos_p
    
    # Cuentas por Cobrar: La suma de lo que te deben (foto 3)
    # Buscamos la columna de saldo sin que importen las repetidas
    col_saldo = [c for c in cred.columns if 'saldo' in c.lower()][0]
    total_por_cobrar = pd.to_numeric(cred[col_saldo], errors='coerce').sum()

    # PATRIMONIO TOTAL
    patrimonio = liquidez + valor_acciones_hoy + total_por_cobrar

    # 4. MÉTRICAS LIMPIAS
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    c2.metric("Portafolio Actual", f"${valor_acciones_hoy:,.2f}")
    c3.metric("Liquidez (Efectivo)", f"${liquidez:,.2f}")
    c4.metric("Por Cobrar (Negocio)", f"${total_por_cobrar:,.2f}")

    # 5. PANEL DE CONTROL
    t1, t2, t3 = st.tabs(["📊 Mis Datos", "💹 Futuro", "🤖 IA"])
    
    with t1:
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Tus Acciones")
            st.dataframe(port_resumen, use_container_width=True)
        with col_right:
            st.subheader("Deudas de Clientes")
            st.dataframe(cred.tail(10), use_container_width=True)

    with t2:
        st.subheader("Simulación a 10% anual")
        años = st.slider("Años", 1, 20, 5)
        st.write(f"En {años} años tendrías: **${patrimonio * (1.10)**años:,.2f}**")

    with t3:
        if st.text_input("Pregunta a Xvortice:"):
            st.info(f"Daniel, hoy tu negocio (por cobrar) representa el {(total_por_cobrar/patrimonio)*100:.1f}% de tu riqueza.")

except Exception as e:
    st.error(f"Error detectado: {e}")
    st.warning("Consejo: En tu hoja 'Creditos', borra las columnas F y G que están repetidas para que todo fluya mejor.")
