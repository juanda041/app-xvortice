import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de nivel ejecutivo
st.set_page_config(page_title="Xvortice Executive", layout="wide")

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    df_m = conn.read(worksheet="Movimientos", ttl="0")
    try:
        df_p = conn.read(worksheet="Portafolio", ttl="0")
    except:
        df_p = pd.DataFrame(columns=["Ticker", "Cantidad", "Precio de Compra"])
    try:
        df_c = conn.read(worksheet="Creditos", ttl="0")
    except:
        df_c = pd.DataFrame(columns=["Cliente", "Producto", "Monto Total", "Saldo Pendiente", "Fecha Limite"])
    return df_m, df_p, df_c

df_mov, df_port, df_cred = cargar_datos()

# --- NAVEGACIÓN ---
st.sidebar.title("🏛️ Xvortice Menu")
menu = st.sidebar.selectbox("Módulo:", ["Dashboard & Meta", "Ventas a Crédito", "Inversiones (Live)", "Nuevo Registro"])
meta_ahorro = st.sidebar.number_input("Meta Actual ($)", value=5000)

# --- 1. DASHBOARD ---
if menu == "Dashboard & Meta":
    st.header("📊 Resumen General de Patrimonio")
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        ingresos = df_mov[df_mov['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        capital_total = ingresos - gastos
        
        progreso = min(capital_total / meta_ahorro, 1.0)
        st.write(f"**Progreso hacia tu meta de ${meta_ahorro:,.0f}**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital en Caja", f"${capital_total:,.2f}")
        c2.metric("Meta Alcanzada", f"{progreso*100:.1f}%")
        c3.metric("Faltante", f"${max(0, meta_ahorro - capital_total):,.2f}")

# --- 2. VENTAS A CRÉDITO (RECUPERADO) ---
elif menu == "Ventas a Crédito":
    st.header("💸 Cuentas por Cobrar (Dinero en la Calle)")
    
    with st.expander("➕ Registrar Nuevo Crédito"):
        with st.form("form_cred"):
            col_c1, col_c2 = st.columns(2)
            c_cliente = col_c1.text_input("Nombre del Cliente")
            c_prod = col_c2.text_input("Artículo (Ej: Zapatillas, Perfume)")
            c_monto = col_c1.number_input("Monto Total", min_value=0.0)
            c_fecha = col_c2.date_input("Fecha Límite de Pago")
            
            if st.form_submit_button("Guardar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": c_cliente, "Producto": c_prod, "Monto Total": c_monto, "Saldo Pendiente": c_monto, "Fecha Limite": str(c_fecha)}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.success(f"Crédito para {c_cliente} registrado.")

    if not df_cred.empty:
        st.subheader("Listado de Deudores")
        st.dataframe(df_cred, use_container_width=True)
        total_calle = pd.to_numeric(df_cred['Saldo Pendiente'], errors='coerce').sum()
        st.metric("TOTAL POR COBRAR", f"${total_calle:,.2f}")

# --- 3. INVERSIONES LIVE ---
elif menu == "Inversiones (Live)":
    st.header("📈 Mi Portafolio en Tiempo Real")
    with st.expander("➕ Agregar Acción"):
        with st.form("form_inv"):
            t_ticker = st.text_input("Ticker").upper()
            t_cant = st.number_input("Cantidad", min_value=0.0)
            t_pago = st.number_input("Precio Compra", min_value=0.0)
            if st.form_submit_button("Sincronizar"):
                n_acc = pd.DataFrame([{"Ticker": t_ticker, "Cantidad": t_cant, "Precio de Compra": t_pago}])
                df_up_p = pd.concat([df_port, n_acc], ignore_index=True)
                conn.update(worksheet="Portafolio", data=df_up_p)
                st.success("Acción guardada.")

    if not df_port.empty:
        lista_f = []
        for i, row in df_port.iterrows():
            stock = yf.Ticker(row['Ticker'].strip())
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor = precio * row['Cantidad']
            lista_f.append({"Acción": row['Ticker'], "Valor": valor})
        df_fig = pd.DataFrame(lista_f)
        fig = px.pie(df_fig, values='Valor', names='Acción', hole=0.4, title="Diversificación")
        st.plotly_chart(fig)

# --- 4. NUEVO REGISTRO ---
elif menu == "Nuevo Registro":
    st.header("📝 Registro de Operaciones")
    with st.form("main_form"):
        f_fecha = st.date_input("Fecha")
        f_tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría", ["Venta de Artículo", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_desc = st.text_area("Detalle")
        if st.form_submit_button("Guardar en Xvortice"):
            n_mov = pd.DataFrame([{"Fecha": str(f_fecha), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Detalle": f_desc}])
            df_up_m = pd.concat([df_mov, n_mov], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.success("Registro guardado.")
