import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")
conn = st.connection("gsheets", type=GSheetsConnection)

# Función de carga de datos estable
def cargar(hoja):
    try:
        return conn.read(worksheet=hoja, ttl="1s")
    except:
        return pd.DataFrame()

# Cargar todas las fuentes de datos
df_m = cargar("Movimientos")
df_p = cargar("Portafolio")
df_c = cargar("Creditos")

# --- MENÚ LATERAL ---
st.sidebar.title("🏛️ Xvortice Corp")
meta = st.sidebar.number_input("🎯 Meta Patrimonio ($)", value=10000, step=500)
mod = st.sidebar.selectbox("Módulo:", ["📊 Estado Patrimonial", "📈 Inversiones", "💸 Cuentas por Cobrar", "📝 Registro de Caja"])

# --- FUNCIÓN DE PRECIOS LIVE ---
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
    
    # Cálculos de Efectivo (Movimientos)
    cash_otros = 0
    if not df_m.empty:
        df_m['Monto'] = pd.to_numeric(df_m['Monto'], errors='coerce').fillna(0)
        cash_otros = df_m[df_m['Tipo']=='Ingreso']['Monto'].sum() - df_m[df_m['Tipo']=='Gasto']['Monto'].sum()
    
    # Cálculos de Bolsa e Inversiones
    total_bolsa = 0
    df_grafica = pd.DataFrame()
    
    if not df_p.empty:
        df_p['Cantidad'] = pd.to_numeric(df_p['Cantidad'], errors='coerce').fillna(0)
        acc = df_p[df_p['Ticker'] != 'CASH'].copy()
        cash_hapi = df_p[df_p['Ticker'] == 'CASH']['Cantidad'].sum()
        
        precios = obtener_precios(acc['Ticker'].unique())
        acc['Valor'] = acc['Cantidad'] * acc['Ticker'].map(precios)
        
        # Preparar datos para gráfica y total
        df_grafica = acc[['Ticker', 'Valor']].copy()
        if cash_hapi > 0:
            df_grafica = pd.concat([df_grafica, pd.DataFrame([{"Ticker": "CASH", "Valor": cash_hapi}])])
        
        total_bolsa = df_grafica['Valor'].sum()

    total_neto = cash_otros + total_bolsa
    
    # MÉTRICAS PRINCIPALES
    c1, c2, c3 = st.columns(3)
    c1.metric("Efectivo (Ahorro/Caja)", f"${cash_otros:,.2f}")
    c2.metric("Bolsa + Liquidez Hapi", f"${total_bolsa:,.2f}")
    c3.metric("TOTAL NETO ACTUAL", f"${total_neto:,.2f}")
    st.progress(min(total_neto/meta, 1.0) if meta > 0 else 0)
    
    # GRÁFICA Y TABLA
    if total_bolsa > 0:
        st.markdown("---")
        g1, g2 = st.columns([2, 1])
        with g1:
            fig = px.pie(df_grafica, values='Valor', names='Ticker', hole=0.5, title="Distribución de Activos")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            df_grafica['%'] = (df_grafica['Valor'] / total_bolsa * 100).map("{:.1f}%".format)
            st.write("### Pesos del Portafolio")
            st.table(df_grafica.sort_values(by='Valor', ascending=False))

    # ANALISTA IA
    st.markdown("---")
    st.subheader("🤖 Analista IA Xvortice")
    if total_neto < meta:
        st.info(f"Daniel, estás al {(total_neto/meta*100):.1f}% de tu meta. Sigue enfocado en el flujo de caja del negocio.")
    else:
        st.success("¡Meta de $10k alcanzada! Xvortice está en nivel ejecutivo.")

# --- 2. INVERSIONES ---
elif mod == "📈 Inversiones":
    st.header("Gestión de Portafolio Hapi")
    st.dataframe(df_p, use_container_width=True)
    with st.expander("➕ Actualizar Acciones"):
        with st.form("inv_form", clear_on_submit=True):
            tk = st.text_input("Ticker (Ej: VOO, NVDA, CASH)").upper().strip()
            cant = st.number_input("Cantidad a sumar", format="%.5f")
            if st.form_submit_button("Actualizar Portafolio"):
                if tk in df_p['Ticker'].values:
                    df_p.loc[df_p['Ticker']==tk, 'Cantidad'] += cant
                else:
                    df_p = pd.concat([df_p, pd.DataFrame([{"Ticker":tk, "Cantidad":cant}])], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_p)
                st.success(f"{tk} actualizado."); st.rerun()

# --- 3. CUENTAS POR COBRAR ---
elif mod == "💸 Cuentas por Cobrar":
    st.header("Créditos del Negocio")
    st.dataframe(df_c, use_container_width=True)
    with st.expander("➕ Nuevo Crédito"):
        with st.form("cred_form"):
            cli = st.text_input("Cliente")
            monto = st.number_input("Monto Pendiente")
            if st.form_submit_button("Registrar"):
                df_c = pd.concat([df_c, pd.DataFrame([{"Cliente":cli, "Saldo pendiente":monto}])], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_c)
                st.rerun()

# --- 4. REGISTRO DE CAJA ---
elif mod == "📝 Registro de Caja":
    st.header("Movimientos de Efectivo")
    st.dataframe(df_m, use_container_width=True)
    with st.form("reg_form", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        cat = st.selectbox("Categoría", ["Ahorros", "Venta Xvortice", "Versa", "Comida", "Otros"])
        val = st.number_input("Monto")
        nota = st.text_input("Comentario")
        if st.form_submit_button("Guardar Movimiento"):
            nuevo = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":tipo, "Categoria":cat, "Monto":val, "Comentario":nota}])
            conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo], ignore_index=True))
            st.rerun()
