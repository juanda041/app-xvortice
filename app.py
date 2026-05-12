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

# Carga de datos
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
    
    if total_neto > 0:
        st.markdown("---")
        g1, g2 = st.columns([2, 1])
        with g1:
            df_pie = df_grafica.copy()
            if total_creditos > 0:
                df_pie = pd.concat([df_pie, pd.DataFrame([{"Ticker": "CRÉDITOS", "Valor": total_creditos}])])
            if cash_otros > 0:
                df_pie = pd.concat([df_pie, pd.DataFrame([{"Ticker": "EFECTIVO CAJA", "Valor": cash_otros}])])
            fig = px.pie(df_pie, values='Valor', names='Ticker', hole=0.5, title="Distribución del Patrimonio")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.write("### Análisis")
            st.info(f"Faltan ${meta-total_neto:,.2f} para tu meta de $10k.")

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

# --- 3. CUENTAS POR COBRAR (RESTA AUTOMÁTICA) ---
elif mod == "💸 Cuentas por Cobrar":
    st.header("Gestión de Créditos Xvortice")
    st.dataframe(df_c, use_container_width=True)
    with st.expander("➕ Registrar Pago o Nuevo Crédito"):
        with st.form("cred_form", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente").strip()
            monto = st.number_input("Monto ($)", min_value=0.0)
            accion = st.radio("Acción:", ["Nuevo Crédito (Suma)", "Abono/Pago (Resta)"])
            if st.form_submit_button("Ejecutar Operación"):
                if not df_c.empty and cliente in df_c['Cliente'].values:
                    idx = df_c.index[df_c['Cliente'] == cliente][0]
                    if accion == "Nuevo Crédito (Suma)":
                        df_c.at[idx, 'Saldo pendiente'] += monto
                    else:
                        df_c.at[idx, 'Saldo pendiente'] -= monto
                        # Registro en Caja si es un pago
                        nuevo_m = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":"Ingreso", "Categoria":"Cobro Crédito", "Monto":monto, "Comentario":f"Pago de {cliente}"}])
                        conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo_m], ignore_index=True))
                        if df_c.at[idx, 'Saldo pendiente'] <= 0: df_c = df_c.drop(idx)
                else:
                    if accion == "Nuevo Crédito (Suma)":
                        df_c = pd.concat([df_c, pd.DataFrame([{"Cliente":cliente, "Saldo pendiente":monto}])], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_c)
                st.success("Crédito actualizado."); st.rerun()

# --- 4. REGISTRO DE CAJA ---
elif mod == "📝 Registro de Caja":
    st.header("Registro de Movimientos")
    st.dataframe(df_m, use_container_width=True)
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        t = col1.selectbox("Tipo", ["Ingreso", "Gasto"])
        m = col2.number_input("Monto ($)")
        c = col1.selectbox("Categoría", ["Venta Xvortice", "Ahorros", "Gasto Versa", "Comida", "Otros"])
        n = col2.text_input("Nota")
        if st.form_submit_button("Guardar"):
            nuevo = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":t, "Categoria":c, "Monto":m, "Comentario":n}])
            conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo], ignore_index=True))
            st.success("Movimiento registrado."); st.rerun()

# --- 5. PROYECCIÓN ---
elif mod == "🚀 Proyección":
    st.header("Simulador de Interés Compuesto")
    c1, c2 = st.columns(2)
    ini = c1.number_input("Capital Inicial ($)", value=4000.0)
    men = c1.number_input("Aporte Mensual ($)", value=200.0)
    ani = c2.slider("Años", 1, 30, 10)
    tas = c2.slider("Retorno Anual (%)", 1, 20, 10)
    r = tas / 100 / 12
    n_meses = ani * 12
    final = ini * (1 + r)**n_meses + men * (((1 + r)**n_meses - 1) / r)
    st.success(f"### Patrimonio Estimado: ${final:,.2f}")
