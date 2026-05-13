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

st.title("🏛️ Xvortice: Balance Maestro")

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

    # --- 2. IDENTIFICACIÓN FLEXIBLE DE COLUMNAS (PORTAFOLIO) ---
    col_tk = [c for c in port.columns if 'ticker' in c.lower()][0]
    col_cant = [c for c in port.columns if 'cant' in c.lower()][0]
    # Busca 'monto' o 'invers' o 'costo'
    cols_monto_search = [c for c in port.columns if any(x in c.lower() for x in ['monto', 'invers', 'costo'])]
    col_monto_inv = cols_monto_search[0] if cols_monto_search else port.columns[2]

    # --- 3. LÓGICA DE BALANCE ---
    port[col_monto_inv] = pd.to_numeric(port[col_monto_inv], errors='coerce').fillna(0)
    port[col_cant] = pd.to_numeric(port[col_cant], errors='coerce').fillna(0)
    
    resumen_acciones = port.groupby(col_tk).agg({
        col_cant: 'sum',
        col_monto_inv: 'sum'
    }).reset_index()

    datos_finales = []
    valor_mkt_total = 0
    costo_base_total = 0

    with st.sidebar:
        st.header("💹 Precios Actuales")
        for _, row in resumen_acciones.iterrows():
            tk = str(row[col_tk]).upper().strip()
            if tk not in ["CASH", "NAN", ""]:
                try:
                    p_hoy = yf.Ticker(tk).history(period="1d")['Close'].iloc[-1]
                    v_actual = row[col_cant] * p_hoy
                    gan_dinero = v_actual - row[col_monto_inv]
                    
                    datos_finales.append({
                        "Ticker": tk,
                        "Acciones": row[col_cant],
                        "Inversión ($)": row[col_monto_inv],
                        "Valor Actual ($)": v_actual,
                        "Ganancia ($)": gan_dinero,
                        "Yield (%)": (gan_dinero/row[col_monto_inv]*100) if row[col_monto_inv]>0 else 0
                    })
                    valor_mkt_total += v_actual
                    costo_base_total += row[col_monto_inv]
                    st.write(f"**{tk}:** ${p_hoy:,.2f}")
                except: continue
        st.divider()
        meta = st.number_input("Meta Patrimonial", value=10000)

    # 4. PATRIMONIO TOTAL
    # Liquidez
    ing = pd.to_numeric(movs[movs['Tipo'].str.contains('Ingreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    gas = pd.to_numeric(movs[movs['Tipo'].str.contains('Gasto|Egreso', case=False, na=False)]['Monto'], errors='coerce').sum()
    liquidez = ing - gas
    
    # Cuentas por Cobrar
    col_s = [c for c in cred.columns if 'saldo' in c.lower() or 'pendiente' in c.lower()][0]
    por_cobrar = pd.to_numeric(cred[col_s], errors='coerce').sum()
    
    patrimonio = liquidez + valor_mkt_total + por_cobrar

    # 5. DASHBOARD
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PATRIMONIO TOTAL", f"${patrimonio:,.2f}")
    c2.metric("Balance Inversión", f"${valor_mkt_total:,.2f}", f"{(valor_mkt_total-costo_base_total):,.2f}")
    c3.metric("Efectivo Neto", f"${liquidez:,.2f}")
    c4.metric("Cuentas x Cobrar", f"${por_cobrar:,.2f}")

    # 6. PANELES
    t1, t2, t3 = st.tabs(["📊 Mi Portafolio", "📝 Registrar", "🤖 IA"])

    with t1:
        if datos_finales:
            df_res = pd.DataFrame(datos_finales)
            st.dataframe(df_res.style.format(precision=2), use_container_width=True)
            fig = px.bar(df_res, x="Ticker", y="Ganancia ($)", color="Ganancia ($)", 
                         title="Ganancia/Pérdida por Acción", color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay acciones registradas con montos válidos.")

    with t2:
        st.subheader("Registrar nueva compra")
        with st.form("add_inv"):
            c1, c2, c3 = st.columns(3)
            nt = c1.text_input("Ticker (Ej: BAC)")
            nc = c2.number_input("Cantidad", min_value=0.0)
            nm = c3.number_input("Inversión Total ($)", min_value=0.0)
            if st.form_submit_button("Guardar"):
                # Aquí usamos los nombres de columnas que detectamos arriba
                new_row = pd.DataFrame([[nt.upper(), nc, nm, 0, ""]], columns=port.columns[:5])
                port = pd.concat([port, new_row], ignore_index=True)
                conn.update(worksheet="Portafolio", data=port)
                st.success(f"Guardado {nt}")

except Exception as e:
    st.error(f"Error: {e}")
