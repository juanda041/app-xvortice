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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
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
    col_inv = cols_monto[0] if cols_monto else port.columns[2]

    valor_mkt_total = 0
    resumen_port = port.groupby(col_tk).agg({col_cant: 'sum', col_inv: 'sum'}).reset_index()
    
    for _, row in resumen_port.iterrows():
        tk = str(row[col_tk]).upper().strip()
        if tk not in ["CASH", "NAN", ""]:
            try:
                p = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                valor_mkt_total += (row[col_cant] * p)
            except: continue

    # --- 3. PATRIMONIO Y LIQUIDEZ ---
    ing = pd.to_numeric(movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    gas = pd.to_numeric(movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    liquidez = ing - gas
    
    col_s = [c for c in cred.columns if 'saldo' in c.lower() or 'pendiente' in c.lower()][0]
    por_cobrar = pd.to_numeric(cred[col_s], errors='coerce').sum()
    
    patrimonio = liquidez + valor_mkt_total + por_cobrar

    # 4. DASHBOARD PRINCIPAL
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    c2.metric("Portafolio", f"${valor_mkt_total:,.2f}")
    c3.metric("Efectivo (Liquidez)", f"${liquidez:,.2f}")
    c4.metric("Por Cobrar", f"${por_cobrar:,.2f}")

    # 5. EL CORAZÓN DE LA APP: PESTAÑAS
    t1, t2, t3, t4 = st.tabs(["📝 Anotar Gastos/Ingresos", "📊 Balance y Tablas", "💹 Proyección Futura", "🤖 IA Xvortice"])

    with t1:
        st.subheader("Nuevo Registro de Caja")
        with st.form("form_gastos"):
            col_f, col_t, col_m = st.columns(3)
            f_reg = col_f.date_input("Fecha", datetime.now())
            t_reg = col_t.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
            m_reg = col_m.number_input("Monto ($)", min_value=0.0)
            c_reg = st.text_input("Categoría / Descripción (Ej: Comida, Venta Celular, Pasaje)")
            
            if st.form_submit_button("Guardar en mi Excel"):
                # Ajustamos la fila para que coincida con las columnas de tu hoja Movimientos
                nueva_fila = pd.DataFrame([[f_reg, "Daniel", t_reg, c_reg, "", m_reg, "", ""]], columns=movs.columns[:8])
                movs = pd.concat([movs, nueva_fila], ignore_index=True)
                conn.update(worksheet="Movimientos", data=movs)
                st.success(f"Registrado: {t_reg} de ${m_reg}")

    with t2:
        st.subheader("Tus Datos Actuales")
        col_m, col_c = st.columns(2)
        with col_m:
            st.write("**Últimos Movimientos**")
            st.dataframe(movs.tail(10), use_container_width=True)
        with col_c:
            st.write("**Cuentas por Cobrar**")
            st.dataframe(cred[['Cliente', col_s]].tail(10), use_container_width=True)

    with t3:
        st.subheader("🔮 Tu Futuro Financiero")
        años = st.slider("¿A cuántos años quieres ver tu futuro?", 1, 40, 10)
        tasa = st.slider("Rendimiento anual estimado (%)", 1, 20, 10)
        
        # Fórmula de Interés Compuesto aplicada a tu Patrimonio Real
        valor_futuro = patrimonio * (1 + (tasa/100))**años
        
        st.markdown(f"### Con un patrimonio actual de **${patrimonio:,.2f}**:")
        st.success(f"En **{años} años**, tendrías un total de **${valor_futuro:,.2f}**")
        
        # Gráfica de crecimiento
        proyeccion = [patrimonio * (1 + (tasa/100))**i for i in range(años + 1)]
        st.line_chart(proyeccion)

    with t4:
        st.subheader("🤖 Consultoría IA Xvortice")
        pregunta = st.text_input("Hazme una pregunta sobre tu situación actual:")
        if pregunta:
            # La IA ahora responde con contexto real
            pct_cobrar = (por_cobrar/patrimonio)*100 if patrimonio > 0 else 0
            st.info(f"Daniel, analizando tus datos: Tu liquidez es de ${liquidez:,.2f}. "
                    f"Tienes un {pct_cobrar:.1f}% de tu patrimonio en cuentas por cobrar. "
                    f"Si mantienes el ritmo, vas por buen camino hacia tu meta de ${patrimonio + 2000:,.0f}.")

except Exception as e:
    st.error(f"Error técnico: {e}")
