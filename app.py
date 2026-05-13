import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

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

    # --- 2. LÓGICA DE BALANCE DE ACCIONES ---
    # Consolidamos: Ticker, Cantidad Total y Costo Total (lo que pagaste)
    # Suponiendo que en tu Excel 'Portafolio' tienes columnas: Ticker, Cantidad, Precio Compra (o Monto Invertido)
    port['Monto_Invertido'] = pd.to_numeric(port['Monto Invertido'], errors='coerce').fillna(0)
    port['Cantidad'] = pd.to_numeric(port['Cantidad'], errors='coerce').fillna(0)
    
    resumen_acciones = port.groupby('Ticker').agg({
        'Cantidad': 'sum',
        'Monto_Invertido': 'sum'
    }).reset_index()

    datos_portafolio = []
    valor_acciones_total_hoy = 0
    costo_total_portafolio = 0

    for _, row in resumen_acciones.iterrows():
        tk = str(row['Ticker']).upper().strip()
        if tk not in ["CASH", "NAN", ""]:
            try:
                p_actual = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                valor_hoy = row['Cantidad'] * p_actual
                ganancia_abs = valor_hoy - row['Monto_Invertido']
                ganancia_pct = (ganancia_abs / row['Monto_Invertido'] * 100) if row['Monto_Invertido'] > 0 else 0
                
                datos_portafolio.append({
                    "Ticker": tk,
                    "Cant.": row['Cantidad'],
                    "Inversión ($)": row['Monto_Invertido'],
                    "Valor Hoy ($)": valor_hoy,
                    "Ganancia ($)": ganancia_abs,
                    "Retorno (%)": f"{ganancia_pct:.2f}%"
                })
                valor_acciones_total_hoy += valor_hoy
                costo_total_portafolio += row['Monto_Invertido']
            except: continue

    df_balance = pd.DataFrame(datos_portafolio)

    # 3. LÓGICA DE PATRIMONIO
    ingresos = pd.to_numeric(movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    gastos_p = pd.to_numeric(movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    liquidez = ingresos - gastos_p
    
    col_saldo = [c for c in cred.columns if 'saldo' in c.lower()][0]
    total_por_cobrar = pd.to_numeric(cred[col_saldo], errors='coerce').sum()
    
    patrimonio = liquidez + valor_acciones_total_hoy + total_por_cobrar

    # 4. MÉTRICAS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    c2.metric("Balance Inversiones", f"${valor_acciones_total_hoy:,.2f}", f"{((valor_acciones_total_hoy/costo_total_portafolio-1)*100 if costo_total_portafolio > 0 else 0):.2f}%")
    c3.metric("Liquidez", f"${liquidez:,.2f}")
    c4.metric("Cuentas por Cobrar", f"${total_por_cobrar:,.2f}")

    # 5. PANELES
    t1, t2, t3 = st.tabs(["📊 Mi Balance de Acciones", "📝 Registro", "🤖 IA"])

    with t1:
        st.subheader("Estado Detallado de Inversiones")
        st.dataframe(df_balance, use_container_width=True)
        
        st.divider()
        st.subheader("Distribución por Activo")
        fig = px.pie(df_balance, values='Valor Hoy ($)', names='Ticker', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        with st.form("registro_portafolio"):
            st.write("Registrar Compra Nueva")
            col1, col2, col3 = st.columns(3)
            nuevo_tk = col1.text_input("Ticker").upper()
            nueva_cant = col2.number_input("Cantidad", min_value=0.0)
            nuevo_costo = col3.number_input("Total Pagado ($)", min_value=0.0)
            if st.form_submit_button("Añadir al Excel"):
                new_data = pd.DataFrame([[nuevo_tk, nueva_cant, nuevo_costo, 0, ""]], columns=port.columns[:5])
                port = pd.concat([port, new_data], ignore_index=True)
                conn.update(worksheet="Portafolio", data=port)
                st.success(f"Registrado: {nuevo_tk}")

except Exception as e:
    st.error(f"Error: {e}")
