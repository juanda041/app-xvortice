import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Xvortice Pro", layout="wide", page_icon="🏛️")

# Estilo Daniel
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Xvortice: Sistema Integral")

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

    # --- 2. CÁLCULOS DE INVERSIONES ---
    col_tk = [c for c in port.columns if 'ticker' in c.lower()][0]
    col_cant = [c for c in port.columns if 'cant' in c.lower()][0]
    cols_monto = [c for c in port.columns if any(x in c.lower() for x in ['monto', 'invers', 'costo'])]
    col_inv_val = cols_monto[0] if cols_monto else port.columns[2]

    resumen_port = port.groupby(col_tk).agg({col_cant: 'sum', col_inv_val: 'sum'}).reset_index()
    valor_mkt_total = 0
    datos_balance = []

    for _, row in resumen_port.iterrows():
        tk = str(row[col_tk]).upper().strip()
        if tk not in ["CASH", "NAN", ""]:
            try:
                p = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                v_hoy = row[col_cant] * p
                valor_mkt_total += v_hoy
                datos_balance.append({
                    "Ticker": tk, "Cant": row[col_cant], "Inversión": row[col_inv_val], "Valor Hoy": v_hoy
                })
            except: continue

    # --- 3. PATRIMONIO ---
    ing = pd.to_numeric(movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    gas = pd.to_numeric(movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    liquidez = ing - gas
    col_s = [c for c in cred.columns if 'saldo' in c.lower() or 'pendiente' in c.lower()][0]
    por_cobrar = pd.to_numeric(cred[col_s], errors='coerce').sum()
    patrimonio = liquidez + valor_mkt_total + por_cobrar

    # 4. MÉTRICAS ARRIBA
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    m2.metric("Portafolio", f"${valor_mkt_total:,.2f}")
    m3.metric("Liquidez", f"${liquidez:,.2f}")
    m4.metric("Por Cobrar", f"${por_cobrar:,.2f}")

    # 5. PESTAÑAS DEFINITIVAS
    t1, t2, t3, t4, t5 = st.tabs(["📝 Anotar Todo", "📈 Mi Inversión", "📊 Tablas Reales", "💹 Futuro", "🤖 IA"])

    with t1:
        tipo_reg = st.radio("¿Qué vas a registrar?", ["Gasto/Ingreso de Caja", "Compra de Acción", "Venta a Crédito"], horizontal=True)
        with st.form("form_universal"):
            if tipo_reg == "Gasto/Ingreso de Caja":
                c1, c2 = st.columns(2)
                t_mov = c1.selectbox("Tipo", ["Gasto", "Ingreso"])
                m_mov = c2.number_input("Monto ($)", min_value=0.0)
                d_mov = st.text_input("Descripción")
                if st.form_submit_button("Guardar Movimiento"):
                    row = pd.DataFrame([[datetime.now(), "Daniel", t_mov, d_mov, "", m_mov, "", ""]], columns=movs.columns[:8])
                    conn.update(worksheet="Movimientos", data=pd.concat([movs, row], ignore_index=True))
                    st.success("Guardado en Movimientos")

            elif tipo_reg == "Compra de Acción":
                c1, c2, c3 = st.columns(3)
                tk_inv = c1.text_input("Ticker (Ej: NVDA)").upper()
                ct_inv = c2.number_input("Cantidad", min_value=0.0)
                mt_inv = c3.number_input("Monto Invertido ($)", min_value=0.0)
                if st.form_submit_button("Guardar Inversión"):
                    row = pd.DataFrame([[tk_inv, ct_inv, mt_inv, 0, ""]], columns=port.columns[:5])
                    conn.update(worksheet="Portafolio", data=pd.concat([port, row], ignore_index=True))
                    st.success(f"Inversión en {tk_inv} anotada")

            elif tipo_reg == "Venta a Crédito":
                cli = st.text_input("Cliente")
                prod = st.text_input("Producto")
                pago = st.number_input("Monto a Cobrar", min_value=0.0)
                if st.form_submit_button("Registrar Crédito"):
                    row = pd.DataFrame([[cli, prod, pago, pago, ""]], columns=cred.columns[:5])
                    conn.update(worksheet="Creditos", data=pd.concat([cred, row], ignore_index=True))
                    st.success(f"Crédito para {cli} guardado")

    with t2:
        st.subheader("Balance de tus Acciones")
        if datos_balance:
            st.table(pd.DataFrame(datos_balance))
        else: st.info("Registra tu primera compra en la pestaña de 'Anotar Todo'")

    with t3:
        st.subheader("Historial de Movimientos")
        st.dataframe(movs.tail(15), use_container_width=True)

    with t4:
        st.subheader("Crecimiento Proyectado")
        años = st.slider("Años", 1, 30, 10)
        tasa = st.slider("Tasa Anual %", 1, 20, 10)
        st.write(f"En {años} años tendrías: **${patrimonio * (1 + tasa/100)**años:,.2f}**")
        st.line_chart([patrimonio * (1 + tasa/100)**i for i in range(años+1)])

    with t5:
        st.subheader("IA Xvortice")
        if st.text_input("Pregunta:"):
            st.info(f"Daniel, tienes ${por_cobrar:,.2f} en la calle. Eso es el {(por_cobrar/patrimonio)*100:.1f}% de tu capital.")

except Exception as e:
    st.error(f"Error: {e}")
