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
st.sidebar.title("🏛️ Xvortice Corporate")
menu = st.sidebar.selectbox("Módulo Estratégico:", ["Estado Patrimonial", "Gestión de Créditos", "Cartera de Inversiones", "Registro de Operaciones"])
meta_ahorro = st.sidebar.number_input("Objetivo de Capital ($)", value=5000)

# --- 1. ESTADO PATRIMONIAL (DASHBOARD CON IA) ---
if menu == "Estado Patrimonial":
    st.header("🏛️ Análisis de Activos y Patrimonio")
    
    if not df_mov.empty:
        df_mov['Monto'] = pd.to_numeric(df_mov['Monto'], errors='coerce').fillna(0)
        
        ventas_totales = df_mov[df_mov['Categoria'] == 'Venta de Artículo']['Monto'].sum()
        reserva_capital = df_mov[df_mov['Categoria'] == 'Reserva de Capital']['Monto'].sum()
        gastos = df_mov[df_mov['Tipo'] == 'Gasto']['Monto'].sum()
        
        patrimonio_liquido = ventas_totales + reserva_capital - gastos
        progreso = min(patrimonio_liquido / meta_ahorro, 1.0) if meta_ahorro > 0 else 0
        
        st.write(f"**Nivel de Consecución de Meta (${meta_ahorro:,.0f})**")
        st.progress(progreso)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimonio Líquido", f"${patrimonio_liquido:,.2f}")
        c2.metric("Reserva de Capital", f"${reserva_capital:,.2f}")
        c3.metric("Rendimiento de Meta", f"{progreso*100:.1f}%")
        
        # --- EL REGRESO DE LA IA ---
        st.markdown("---")
        st.subheader("🤖 Analista IA Xvortice")
        
        porcentaje_reserva = (reserva_capital / patrimonio_liquido * 100) if patrimonio_liquido > 0 else 0
        faltante = max(0, meta_ahorro - patrimonio_liquido)
        
        if progreso >= 1.0:
            mensaje_ia = f"¡Objetivo Cumplido! Juan, has alcanzado la meta de ${meta_ahorro:,.0f}. Es momento de evaluar la apertura del Plazo Fijo que tenías planeado para maximizar el interés compuesto."
        elif progreso > 0.5:
            mensaje_ia = f"Excelente ritmo. Ya superaste el 50% de la meta. Tu Reserva de Capital representa el {porcentaje_reserva:.1f}% de tu liquidez. Sugiero mantener el enfoque en la venta de artículos para cubrir los ${faltante:,.2f} restantes."
        else:
            mensaje_ia = f"Buen inicio, Juan. Estás construyendo los cimientos. Te faltan ${faltante:,.2f} para tu objetivo. Recuerda que cada 'Entrada de Capital' o ahorro del supermercado cuenta para la libertad financiera."
            
        st.info(mensaje_ia)

# --- 2. GESTIÓN DE CRÉDITOS ---
elif menu == "Gestión de Créditos":
    st.header("💸 Cuentas Activas (Capital en Circulación)")
    with st.expander("➕ Apertura de Nuevo Crédito"):
        with st.form("form_cred"):
            c_cliente = st.text_input("Nombre del Deudor")
            c_prod = st.text_input("Activo Entregado")
            c_monto = st.number_input("Monto de la Deuda", min_value=0.0)
            c_fecha = st.date_input("Vencimiento")
            if st.form_submit_button("Sincronizar Crédito"):
                nuevo_c = pd.DataFrame([{"Cliente": c_cliente, "Producto": c_prod, "Monto Total": c_monto, "Saldo Pendiente": c_monto, "Fecha Limite": str(c_fecha)}])
                df_up_c = pd.concat([df_cred, nuevo_c], ignore_index=True)
                conn.update(worksheet="Creditos", data=df_up_c)
                st.success("Crédito registrado.")

    if not df_cred.empty:
        st.table(df_cred)

# --- 3. CARTERA DE INVERSIONES ---
elif menu == "Cartera de Inversiones":
    st.header("📈 Rendimiento de Capital en Bolsa")
    if not df_port.empty:
        lista_f = []
        for i, row in df_port.iterrows():
            stock = yf.Ticker(row['Ticker'].strip())
            precio = stock.history(period="1d")['Close'].iloc[-1]
            valor = precio * row['Cantidad']
            lista_f.append({"Activo": row['Ticker'], "Valorización": valor})
        df_fig = pd.DataFrame(lista_f)
        fig = px.pie(df_fig, values='Valorización', names='Activo', hole=0.5, title="Distribución del Portafolio")
        st.plotly_chart(fig)

# --- 4. REGISTRO DE OPERACIONES ---
elif menu == "Registro de Operaciones":
    st.header("📝 Consignación de Movimientos")
    with st.form("main_form"):
        f_fecha = st.date_input("Fecha")
        f_tipo = st.selectbox("Naturaleza", ["Ingreso", "Gasto"])
        f_cat = st.selectbox("Categoría Estratégica", ["Venta de Artículo", "Reserva de Capital", "Entrada de Capital", "Inversión (ETFs)", "Gasto Operativo", "Gasto Personal"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_desc = st.text_area("Detalle")
        if st.form_submit_button("Sincronizar"):
            n_mov = pd.DataFrame([{"Fecha": str(f_fecha), "Tipo": f_tipo, "Categoria": f_cat, "Monto": f_monto, "Detalle": f_desc}])
            df_up_m = pd.concat([df_mov, n_mov], ignore_index=True)
            conn.update(worksheet="Movimientos", data=df_up_m)
            st.success("Consolidado.")
