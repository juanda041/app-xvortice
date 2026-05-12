import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Xvortice Executive", layout="wide", page_icon="🏛️")
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar(hoja):
    try: return conn.read(worksheet=hoja, ttl="1s")
    except: return pd.DataFrame()

df_m = cargar("Movimientos")
df_p = cargar("Portafolio")
df_c = cargar("Creditos")

st.sidebar.title("🏛️ Xvortice Corp")
meta = st.sidebar.number_input("🎯 Meta Patrimonio ($)", value=10000)
mod = st.sidebar.selectbox("Módulo:", ["📊 Estado Patrimonial", "📈 Inversiones", "💸 Cuentas por Cobrar", "📝 Registro de Caja", "🚀 Proyección"])

# --- 1. ESTADO PATRIMONIAL (Suma todo) ---
if mod == "📊 Estado Patrimonial":
    st.header("Resumen de Patrimonio Real")
    cash_otros = 0
    if not df_m.empty:
        df_m['Monto'] = pd.to_numeric(df_m['Monto'], errors='coerce').fillna(0)
        cash_otros = df_m[df_m['Tipo']=='Ingreso']['Monto'].sum() - df_m[df_m['Tipo']=='Gasto']['Monto'].sum()
    
    total_bolsa = 0
    if not df_p.empty:
        df_p['Cantidad'] = pd.to_numeric(df_p['Cantidad'], errors='coerce').fillna(0)
        # (Lógica simplificada de precios para rapidez)
        total_bolsa = df_p['Cantidad'].sum() * 1 # Valor base (ajustar con yfinance si deseas)

    total_creditos = 0
    if not df_c.empty:
        df_c['Saldo pendiente'] = pd.to_numeric(df_c['Saldo pendiente'], errors='coerce').fillna(0)
        total_creditos = df_c['Saldo pendiente'].sum()

    total_neto = cash_otros + total_bolsa + total_creditos
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Efectivo", f"${cash_otros:,.2f}")
    c2.metric("Inversiones", f"${total_bolsa:,.2f}")
    c3.metric("Por Cobrar", f"${total_creditos:,.2f}")
    c4.metric("TOTAL NETO", f"${total_neto:,.2f}")
    st.progress(min(total_neto/meta, 1.0) if meta > 0 else 0)

# --- 3. CUENTAS POR COBRAR (CON RESTA AUTOMÁTICA) ---
elif mod == "💸 Cuentas por Cobrar":
    st.header("Gestión de Créditos")
    st.dataframe(df_c, use_container_width=True)
    
    with st.expander("➕ Registrar Pago o Nuevo Crédito"):
        with st.form("cred_form", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente (Escribe igual para restar)").strip()
            monto = st.number_input("Monto ($)", min_value=0.0)
            accion = st.radio("Acción:", ["Nuevo Crédito (Suma)", "Abono/Pago (Resta)"])
            
            if st.form_submit_button("Actualizar Saldo"):
                if not df_c.empty and cliente in df_c['Cliente'].values:
                    idx = df_c.index[df_c['Cliente'] == cliente][0]
                    if accion == "Nuevo Crédito (Suma)":
                        df_c.at[idx, 'Saldo pendiente'] += monto
                    else:
                        df_c.at[idx, 'Saldo pendiente'] -= monto
                        # Si pagó todo, lo quitamos
                        if df_c.at[idx, 'Saldo pendiente'] <= 0:
                            df_c = df_c.drop(idx)
                    
                    # Guardar en Movimientos también si es un pago
                    if accion == "Abono/Pago (Resta)":
                        nuevo_m = pd.DataFrame([{"Fecha":str(pd.Timestamp.now().date()), "Tipo":"Ingreso", "Categoria":"Cobro Crédito", "Monto":monto, "Comentario":f"Pago de {cliente}"}])
                        conn.update(worksheet="Movimientos", data=pd.concat([df_m, nuevo_m], ignore_index=True))
                else:
                    if accion == "Nuevo Crédito (Suma)":
                        df_c = pd.concat([df_c, pd.DataFrame([{"Cliente":cliente, "Saldo pendiente":monto}])], ignore_index=True)
                
                conn.update(worksheet="Creditos", data=df_c)
                st.success("Saldo actualizado y registrado en caja."); st.rerun()

# (Los demás módulos se mantienen igual para no fallar)
