import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar(hoja):
    try:
        return conn.read(worksheet=hoja, ttl="1s")
    except:
        return pd.DataFrame()

df_m = cargar("Movimientos")
df_p = cargar("Portafolio")
df_c = cargar("Creditos")

# --- MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
meta = st.sidebar.number_input("🎯 Meta Patrimonio ($)", value=10000, step=500)
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

    total_neto = cash_otros + total_bolsa
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo (Caja)", f"${cash_otros:,.2f}")
    c2.metric("Bolsa + Liquidez", f"${total_bolsa:,.2f}")
    c3.metric("TOTAL NETO", f"${total_neto:,.2f}")
    st.progress(min(total_neto/meta, 1.0) if meta > 0 else 0)
    
    if total_bolsa > 0:
        st.markdown("---")
        g1, g2 = st.columns([2, 1])
        with g1:
            fig = px.pie(df_grafica, values='Valor', names='Ticker', hole=0.5, title="Distribución de Activos")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            df_grafica['%'] = (df_grafica['Valor'] / total_bolsa * 100).map("{:.1f}%".format)
            st.table(df_grafica.sort_values(by='Valor', ascending=False))

# --- 2. INVERSIONES ---
elif mod == "📈 Inversiones":
    st.header("Gestión de Portafolio")
    st.dataframe(df_p, use_container_width=True)
    with st.expander("➕ Actualizar Acciones"):
        with st.form("inv_form", clear_on_submit=True):
            tk = st.text_input("Ticker").upper().strip()
            cant = st.number_input("Cantidad a sumar", format="%.5f")
            if st.form_submit_button("Actualizar"):
                if not df_p.empty and tk in df_p['Ticker'].astype(str).values:
                    idx = df_p.index[df_p['Ticker'] == tk][0]
                    df_p.at[idx, 'Cantidad'] = float(df_p.at[idx, 'Cantidad']) + cant
                else:
                    df_p = pd.concat([df_p, pd.DataFrame([{"Ticker":tk, "Cantidad":cant}])], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_p)
                st.success("Guardado correctamente"); st.rerun()

# --- 3. CUENTAS POR COBRAR ---
elif mod == "💸 Cuentas por Cobrar":
    st.header("Créditos Pendientes del Negocio")
    st.dataframe(df_c, use_container_width=True)
    with st.expander("➕ Registrar Nuevo Cliente"):
        with st.form("cred_form", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente")
            saldo = st.number_input("Monto adeudado ($)", min_value=0.0)
            if st.form_submit_button("Guardar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": cliente, "Saldo pendiente": saldo}])
                df_c = pd.concat([df_c, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_c)
                st.success(f"Crédito para {cliente} registrado."); st.rerun()

# --- 4. REGISTRO DE CAJA ---
elif mod == "📝 Registro de Caja":
    st.header("Registro de Ingresos y Gastos")
    st.dataframe(df_m, use_container_width=True)
    with st.form("reg_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        tipo = col_f1.selectbox("Tipo", ["Ingreso", "Gasto"])
        monto = col_f2.number_input("Monto ($)", min_value=0.0)
        cat = col_f1.selectbox("Categoría", ["Venta Xvortice", "Ahorros", "Inversión Hapi", "Gasto Versa", "Comida", "Otros"])
        nota = col_f2.text_input("Comentario / Nota")
        if st.form_submit_button("Guardar Movimiento"):
            nuevo = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":tipo, "Categoria":cat, "Monto":monto, "Comentario":nota}])
            conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo], ignore_index=True))
            st.success("Movimiento guardado."); st.rerun()

# --- 5. PROYECCIÓN ---
elif mod == "🚀 Proyección":
    st.header("🚀 Simulador de Libertad Financiera")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        cap_inicial = st.number_input("Capital Inicial ($)", value=4000.0)
        aporte_mensual = st.number_input("Aporte Mensual ($)", value=200.0)
    with col_p2:
        anios = st.slider("Años de espera", 1, 30, 10)
        tasa = st.slider("Tasa de retorno anual (%)", 1, 20, 10)
    
    r = tasa / 100
    n = 12 
    t = anios
    pmt = aporte_mensual
    monto_final = cap_inicial * (1 + r/n)**(n*t) + pmt * (((1 + r/n)**(n*t) - 1) / (r/n))
    
    st.markdown("---")
    st.success(f"### En {anios} años, tu patrimonio sería de: **${monto_final:,.2f}**")
    st.info(f"Asumiendo un rendimiento del {tasa}% anual y aportes constantes.")
