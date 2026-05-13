import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar(hoja):
    try:
        return conn.read(worksheet=hoja, ttl="1s")
    except:
        return pd.DataFrame()

# Carga inicial
df_m = cargar("Movimientos")
df_p = cargar("Portafolio")
df_c = cargar("Creditos")

st.sidebar.title("🏛️ Xvortice Corp")
meta = st.sidebar.number_input("🎯 Meta Patrimonio ($)", value=10000)
mod = st.sidebar.selectbox("Módulo:", ["📊 Estado Patrimonial", "📈 Inversiones", "💸 Cuentas por Cobrar", "📝 Registro de Caja", "🚀 Proyección"])

def obtener_precios(tickers):
    precios = {}
    for t in tickers:
        if t == "CASH" or pd.isna(t) or t == "": continue
        try:
            precios[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
        except:
            precios[t] = 0
    return precios

# --- 1. ESTADO PATRIMONIAL ---
if mod == "📊 Estado Patrimonial":
    st.header("Resumen de Patrimonio Real")
    cash_otros = 0
    if not df_m.empty:
        df_m['Monto'] = pd.to_numeric(df_m['Monto'], errors='coerce').fillna(0)
        cash_otros = df_m[df_m['Tipo']=='Ingreso']['Monto'].sum() - df_m[df_m['Tipo']=='Gasto']['Monto'].sum()
    
    total_bolsa = 0
    df_grafica = pd.DataFrame()
    if not df_p.empty:
        df_p['Cantidad'] = pd.to_numeric(df_p['Cantidad'], errors='coerce').fillna(0)
        acc = df_p[df_p['Ticker'] != 'CASH'].copy()
        cash_hapi = df_p[df_p['Ticker'] == 'CASH']['Cantidad'].sum()
        precios = obtener_precios(acc['Ticker'].unique())
        acc['Valor'] = acc['Cantidad'] * acc['Ticker'].map(precios)
        df_grafica = acc[['Ticker', 'Valor']].copy()
        if cash_hapi > 0:
            df_grafica = pd.concat([df_grafica, pd.DataFrame([{"Ticker": "CASH", "Valor": cash_hapi}])])
        total_bolsa = df_grafica['Valor'].sum()

    total_creditos = 0
    if not df_c.empty:
        total_creditos = pd.to_numeric(df_c['Saldo pendiente'], errors='coerce').fillna(0).sum()

    total_neto = cash_otros + total_bolsa + total_creditos
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Efectivo", f"${cash_otros:,.2f}")
    c2.metric("Inversiones", f"${total_bolsa:,.2f}")
    c3.metric("Por Cobrar", f"${total_creditos:,.2f}")
    c4.metric("TOTAL NETO", f"${total_neto:,.2f}")
    st.progress(min(total_neto/meta, 1.0) if meta > 0 else 0)

# --- 2. INVERSIONES ---
elif mod == "📈 Inversiones":
    st.header("Portafolio Hapi")
    st.dataframe(df_p, use_container_width=True)
    with st.expander("➕ Sumar Acciones"):
        with st.form("inv"):
            tk = st.text_input("Ticker").upper()
            ct = st.number_input("Cantidad", format="%.5f")
            if st.form_submit_button("Guardar"):
                if not df_p.empty and tk in df_p['Ticker'].values:
                    df_p.loc[df_p['Ticker'] == tk, 'Cantidad'] += ct
                else:
                    df_p = pd.concat([df_p, pd.DataFrame([{"Ticker":tk, "Cantidad":ct}])])
                conn.update(worksheet="Portafolio", data=df_p)
                st.rerun()

# --- 3. CUENTAS POR COBRAR ---
elif mod == "💸 Cuentas por Cobrar":
    st.header("Créditos Xvortice")
    st.dataframe(df_c, use_container_width=True)
    with st.form("cred"):
        cli = st.text_input("Cliente")
        mon = st.number_input("Monto ($)")
        acc = st.radio("Acción", ["Nuevo Crédito", "Pago (Resta)"])
        if st.form_submit_button("Ejecutar"):
            if not df_c.empty and cli in df_c['Cliente'].values:
                idx = df_c.index[df_c['Cliente'] == cli][0]
                if acc == "Nuevo Crédito": df_c.at[idx, 'Saldo pendiente'] += mon
                else: 
                    df_c.at[idx, 'Saldo pendiente'] -= mon
                    if df_c.at[idx, 'Saldo pendiente'] <= 0: df_c = df_c.drop(idx)
            else:
                if acc == "Nuevo Crédito": df_c = pd.concat([df_c, pd.DataFrame([{"Cliente":cli, "Saldo pendiente":mon}])])
            conn.update(worksheet="Creditos", data=df_c)
            st.rerun()

# --- 4. REGISTRO CAJA ---
elif mod == "📝 Registro de Caja":
    st.header("Ingresos y Gastos")
    st.dataframe(df_m, use_container_width=True)
    with st.form("caja"):
        tp = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        mt = st.number_input("Monto ($)")
        ct = st.selectbox("Categoría", ["Venta Xvortice", "Ahorros", "Gasto Versa", "Comida", "Otros"])
        if st.form_submit_button("Registrar"):
            nuevo = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":tp, "Categoria":ct, "Monto":mt}])
            conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo]))
            st.rerun()

# --- 5. PROYECCIÓN ---
elif mod == "🚀 Proyección":
    st.header("Camino al Éxito")
    ini = st.number_input("Capital Inicial", value=4000.0)
    men = st.number_input("Aporte Mensual", value=200.0)
    ani = st.slider("Años", 1, 30, 10)
    tas = st.slider("Retorno (%)", 1, 20, 10)
    r = tas / 100 / 12
    n = ani * 12
    final = ini * (1 + r)**n + men * (((1 + r)**n - 1) / r)
    st.success(f"### Patrimonio Estimado: ${final:,.2f}")
