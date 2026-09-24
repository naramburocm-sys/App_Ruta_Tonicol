import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os
import base64

# 1. Configuración de la página
st.set_page_config(page_title="Ruta de Visitas y Venta 📍", page_icon="🚚", layout="wide")

# Función para convertir el logo a Base64
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""

IMAGE_PATH = "Logo_Tonicol_letras.jpeg"
img_base64 = get_image_base64(IMAGE_PATH)

# Estilos CSS optimizados con Grid simétrico de 2 columnas para KPIs y Captura de Productos
st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .stApp { background-color: #FFD600; }
    .brand-header { text-align: center; padding: 0px !important; margin-top: -10px !important; margin-bottom: 5px !important; }
    .brand-logo-img { width: 35%; max-width: 100px; height: auto; }
    .resumen-title { text-align: center; font-size: 20px; font-weight: 800; color: #000000; margin-top: 10px; margin-bottom: 12px; }
    
    /* Estilo Grid para KPIs (5 columnas en escritorio, 2 en móvil) */
    .kpi-grid-container { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 15px; }
    @media (max-width: 768px) { .kpi-grid-container { grid-template-columns: repeat(2, 1fr); gap: 8px; } }
    .kpi-card { background: linear-gradient(135deg, #FFFDF0 0%, #F5F5DC 100%); padding: 10px 6px; border-radius: 12px; box-shadow: 0px 3px 6px rgba(0,0,0,0.12); text-align: center; min-height: 75px; }
    .kpi-title { font-size: 16px; font-weight: 700; color: #333333; text-transform: uppercase; margin-bottom: 3px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #000080; }

    /* Estilo Grid Estricto de 2 Columnas para Captura de Productos (Mitad y Mitad exactas) */
    .sales-grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 15px; }
    .sales-card { background: #FFFDF0; padding: 10px 12px; border-radius: 10px; border: 1px solid #E6D200; box-shadow: 0px 2px 4px rgba(0,0,0,0.08); }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Logotipo de Tonicol Visible
if img_base64:
    st.markdown(f'<div class="brand-header"><img src="data:image/jpeg;base64,{img_base64}" class="brand-logo-img"></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="brand-header"><h2 style="color: black; font-weight: 900; margin:0;">ToniCol</h2></div>', unsafe_allow_html=True)

FILE_PATH = 'prueba app.xlsx'

# Precios oficiales basados en tu tabla de productos (por caja)
PRECIOS_PRODUCTOS = {
    "TONICOL NR PET 355 ML": 160,
    "TONICOL FULL SUGAR PET 600 ML": 230,
    "TONICOL NR PET 2 LTS": 180,
    "AGUA DEL YAUCO NR 1/2 LT": 70,
    "TITAN NR PET 355 ML FRESA": 160,
    "TITAN NR PET 600 ML FRESA": 230,
    "TITAN NR PET 600 ML MANDARINA": 230,
    "TITAN TAMARINDO PET 600 ML": 230,
    "TITAN NR PET 600 ML PIÑA": 230,
    "TITAN NR PET 600 ML MANZANA": 230
}

@st.cache_data(ttl=1)
def load_data():
    if os.path.exists(FILE_PATH):
        try:
            df = pd.read_excel(FILE_PATH)
            if 'ESTATUS' not in df.columns:
                df['ESTATUS'] = 'Pendiente'
            if 'MONTO_COBRADO' not in df.columns:
                df['MONTO_COBRADO'] = 0.0
            if 'CAJAS_VENDIDAS' not in df.columns:
                df['CAJAS_VENDIDAS'] = 0
            if 'NOTAS' not in df.columns:
                df['NOTAS'] = ''
            if 'DIA_SEMANA' not in df.columns:
                df['DIA_SEMANA'] = 'Lunes'
            
            for prod in PRECIOS_PRODUCTOS.keys():
                col_name = f"VEND__{prod}"
                if col_name not in df.columns:
                    df[col_name] = 0

            df['COORD_LAT'] = pd.to_numeric(df['COORD_LAT'], errors='coerce')
            df['COORD_LON'] = pd.to_numeric(df['COORD_LON'], errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    if os.path.exists(FILE_PATH):
        with pd.ExcelWriter(FILE_PATH, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.cache_data.clear()

df = load_data()

# Control seguro de inventario diario en session_state
if 'inventario_inicial' not in st.session_state:
    st.session_state.inventario_inicial = {prod: 0 for prod in PRECIOS_PRODUCTOS.keys()}

if not df.empty and 'COORD_LAT' in df.columns and 'COORD_LON' in df.columns:
    
    # 1. Control de Inventario Inicial Diario
    with st.expander("📦 Control de Inventario Inicial (Carga del Día)", expanded=False):
        st.markdown("### Configura las cajas disponibles para la venta de hoy:")
        items_prod = list(PRECIOS_PRODUCTOS.items())
        for i in range(0, len(items_prod), 2):
            cols_inv = st.columns(2)
            with cols_inv[0]:
                prod1, precio1 = items_prod[i]
                val_inv1 = int(st.session_state.inventario_inicial.get(prod1, 0))
                st.session_state.inventario_inicial[prod1] = st.number_input(
                    f"{prod1} (${precio1}/caja)", min_value=0, value=val_inv1, step=1, key=f"inv_{prod1}"
                )
            if i + 1 < len(items_prod):
                with cols_inv[1]:
                    prod2, precio2 = items_prod[i+1]
                    val_inv2 = int(st.session_state.inventario_inicial.get(prod2, 0))
                    st.session_state.inventario_inicial[prod2] = st.number_input(
                        f"{prod2} (${precio2}/caja)", min_value=0, value=val_inv2, step=1, key=f"inv_{prod2}"
                    )

    # Filtros de Día y Ruta ordenados de Lunes a Domingo
    dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dias_en_df = df['DIA_SEMANA'].dropna().unique().tolist()
    dias_disponibles = [d for d in dias_orden if d in dias_en_df]
    for d in dias_en_df:
        if d not in dias_disponibles:
            dias_disponibles.append(d)

    rutas_disponibles = df['RUTA'].dropna().unique().tolist() if 'RUTA' in df.columns else ['Todas']

    with st.expander("🔍 Filtros de Operación (Día y Ruta)", expanded=False):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            dia_sel = st.selectbox("📅 Selecciona el Día:", ["Todos"] + dias_disponibles)
        with col_f2:
            ruta_sel = st.selectbox("🚚 Selecciona Ruta:", ["Todas"] + rutas_disponibles)

    if 'dia_sel' not in locals():
        dia_sel = "Todos"
    if 'ruta_sel' not in locals():
        ruta_sel = "Todas"

    df_filtrado = df.copy()
    if dia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'] == dia_sel]
    if ruta_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['RUTA'] == ruta_sel]

    st.markdown(f"<div class='resumen-title'>📍 Control de Ruta y Cobertura ({dia_sel})</div>", unsafe_allow_html=True)

    # Tarjetas KPI
    total_clientes = len(df_filtrado)
    visitados = len(df_filtrado[df_filtrado['ESTATUS'] == 'Visitado'])
    pendientes = total_clientes - visitados
    total_cobrado = df_filtrado['MONTO_COBRADO'].sum()
    total_cajas_dia = int(df_filtrado['CAJAS_VENDIDAS'].sum()) if 'CAJAS_VENDIDAS' in df_filtrado.columns else 0

    st.markdown(f"""
        <div class="kpi-grid-container">
            <div class="kpi-card"><div class="kpi-title">🏪 Total Clientes</div><div class="kpi-value">{total_clientes}</div></div>
            <div class="kpi-card"><div class="kpi-title">🟢 Visitados</div><div class="kpi-value">{visitados}</div></div>
            <div class="kpi-card"><div class="kpi-title">🔴 Pendientes</div><div class="kpi-value">{pendientes}</div></div>
            <div class="kpi-card"><div class="kpi-title">📦 Cajas Vendidas</div><div class="kpi-value">{total_cajas_dia}</div></div>
            <div class="kpi-card"><div class="kpi-title">💵 Total Cobrado</div><div class="kpi-value">${total_cobrado:,.2f}</div></div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Módulo de Registro de Venta y Check-in
    st.subheader("📝 Registrar Venta y Check-in por Producto")
    pendientes_list = df_filtrado[df_filtrado['ESTATUS'] != 'Visitado']['NOMBRE COMERCIAL'].dropna().tolist()
    
    if pendientes_list:
        with st.form("form_visita", clear_on_submit=True):
            cliente_sel = st.selectbox("Selecciona Cliente a Visitar:", pendientes_list)
            cliente_info = df[df['NOMBRE COMERCIAL'] == cliente_sel].iloc[0]
            
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={cliente_info['COORD_LAT']},{cliente_info['COORD_LON']}"
            st.markdown(f"🧭 **[Click aquí para navegar con Google Maps a {cliente_sel}]({gmaps_url})**")
            
            with st.expander("Selecciona las cantidades a vender:", expanded=True):
                cantidades_venta = {}
                subtotal_venta = 0.0
                total_cajas_transaccion = 0
                
                for i in range(0, len(items_prod), 2):
                    cols_prod = st.columns(2)
                    with cols_prod[0]:
                        prod1, precio1 = items_prod[i]
                        col_p1 = f"VEND__{prod1}"
                        vendido_total_p1 = df[col_p1].sum() if col_p1 in df.columns else 0
                        disp1 = int(max(0, st.session_state.inventario_inicial.get(prod1, 0) - vendido_total_p1))
                        
                        cant1 = st.number_input(f"{prod1} (Disp: {disp1}) - ${precio1}", min_value=0, max_value=disp1, value=0, step=1, key=f"v_{prod1}")
                        cantidades_venta[prod1] = int(cant1)
                        subtotal_venta += cant1 * precio1
                        total_cajas_transaccion += cant1
                    
                    if i + 1 < len(items_prod):
                        prod2, precio2 = items_prod[i+1]
                        col_p2 = f"VEND__{prod2}"
                        vendido_total_p2 = df[col_p2].sum() if col_p2 in df.columns else 0
                        disp2 = int(max(0, st.session_state.inventario_inicial.get(prod2, 0) - vendido_total_p2))
                        
                        with cols_prod[1]:
                            cant2 = st.number_input(f"{prod2} (Disp: {disp2}) - ${precio2}", min_value=0, max_value=disp2, value=0, step=1, key=f"v_{prod2}")
                            cantidades_venta[prod2] = int(cant2)
                            subtotal_venta += cant2 * precio2
                            total_cajas_transaccion += cant2
            
            st.markdown(f"### 📦 Total Cajas Venta: {int(total_cajas_transaccion)} | 💵 Total a Cobrar: ${subtotal_venta:,.2f}")
            notas = st.text_input("Comentarios / Notas de entrega:")
                
            if st.form_submit_button("✅ Confirmar Venta y Registrar Visita"):
                idx_target = df[df['NOMBRE COMERCIAL'] == cliente_sel].index[0]
                df.loc[idx_target, 'ESTATUS'] = 'Visitado'
                df.loc[idx_target, 'MONTO_COBRADO'] = subtotal_venta
                df.loc[idx_target, 'CAJAS_VENDIDAS'] = int(total_cajas_transaccion)
                df.loc[idx_target, 'NOTAS'] = notas
                
                for prod, cant in cantidades_venta.items():
                    col_p = f"VEND__{prod}"
                    if col_p not in df.columns:
                        df[col_p] = 0
                    df.loc[idx_target, col_p] = int(cant)

                save_data(df)
                st.success(f"🎉 ¡Venta a **{cliente_sel}** registrada ({total_cajas_transaccion} cajas) por ${subtotal_venta:,.2f}!")
                st.rerun()
    else:
        st.success(f"🏆 ¡Felicidades! Todos los clientes de **{dia_sel}** han sido visitados.")

    # Corte de Caja e Inventario del Día + Botón de Ejecución de Corte
    with st.expander("💰 Corte de Caja e Inventario Restante"):
        st.markdown("### 📦 Reporte de Inventario del Día")
        
        reporte_inventario = []
        for prod, precio in PRECIOS_PRODUCTOS.items():
            col_p = f"VEND__{prod}"
            cajas_vendidas_total = int(df[col_p].sum()) if col_p in df.columns else 0
            cajas_iniciales = int(st.session_state.inventario_inicial.get(prod, 0))
            cajas_disponibles = max(0, cajas_iniciales - cajas_vendidas_total)
            
            reporte_inventario.append({
                "Producto": prod,
                "Precio Caja": precio,
                "Inventario Inicial": cajas_iniciales,
                "Cajas Vendidas": cajas_vendidas_total,
                "Cajas Disponibles": cajas_disponibles
            })
            
        df_inv_reporte = pd.DataFrame(reporte_inventario)
        st.dataframe(df_inv_reporte, use_container_width=True)
        
        st.markdown("### 📊 Resumen de Cobros y Cajas por Día")
        resumen_dias = df.groupby('DIA_SEMANA').agg(
            Total_Clientes=('NOMBRE COMERCIAL', 'count'),
            Clientes_Visitados=('ESTATUS', lambda x: (x == 'Visitado').sum()),
            Cajas_Vendidas=('CAJAS_VENDIDAS', 'sum'),
            Total_Cobrado=('MONTO_COBRADO', 'sum')
        ).reset_index()
        st.dataframe(resumen_dias, use_container_width=True)
        
        total_recaudado_dia = df['MONTO_COBRADO'].sum()
        st.metric(label="💵 Dinero Total Recaudado (Día/Semana)", value=f"${total_recaudado_dia:,.2f}")
        
        st.divider()
        st.markdown("### 🔒 Ejecución de Corte Diario y Cierre de Operación")
        st.warning("⚠️ Al presionar el botón de **Ejecutar Corte de Caja**, se guardará toda la información en el archivo Excel y se reiniciarán los contadores y el inventario a cero para comenzar las operaciones del siguiente día.")
        
        confirmar_corte = st.checkbox("Confirmo que deseo realizar el corte y cerrar el día", key="chk_corte")
        if st.button("🚀 Ejecutar Corte y Reiniciar para el Siguiente Día", type="primary", disabled=not confirmar_corte):
            if not df.empty:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"corte_caja_{timestamp}.xlsx"
                with pd.ExcelWriter(backup_filename, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Corte_Diario")
                
                df['ESTATUS'] = 'Pendiente'
                df['MONTO_COBRADO'] = 0.0
                df['CAJAS_VENDIDAS'] = 0
                df['NOTAS'] = ''
                for prod in PRECIOS_PRODUCTOS.keys():
                    col_p = f"VEND__{prod}"
                    if col_p in df.columns:
                        df[col_p] = 0
                save_data(df)
                
                st.session_state.inventario_inicial = {prod: 0 for prod in PRECIOS_PRODUCTOS.keys()}
                for prod in PRECIOS_PRODUCTOS.keys():
                    st.session_state[f"inv_{prod}"] = 0

                st.success(f"✅ ¡Corte ejecutado con éxito! Se guardó el respaldo `{backup_filename}` y el inventario e información se han reiniciado a ceros para el siguiente día.")
                st.rerun()

    # Opciones adicionales de reinicio general
    st.divider()
    with st.expander("⚙️ Opciones de Ruta y Reinicio"):
        confirmar_reinicio = st.checkbox("Estoy seguro de querer reiniciar la ruta completa", key="chk_reinicio")
        if st.button("🔄 Reiniciar Ruta Completa", type="secondary", disabled=not confirmar_reinicio):
            if not df.empty:
                df['ESTATUS'] = 'Pendiente'
                df['MONTO_COBRADO'] = 0.0
                df['CAJAS_VENDIDAS'] = 0
                df['NOTAS'] = ''
                for prod in PRECIOS_PRODUCTOS.keys():
                    col_p = f"VEND__{prod}"
                    if col_p in df.columns:
                        df[col_p] = 0
                save_data(df)
                
                st.session_state.inventario_inicial = {prod: 0 for prod in PRECIOS_PRODUCTOS.keys()}
                for prod in PRECIOS_PRODUCTOS.keys():
                    st.session_state[f"inv_{prod}"] = 0

                st.success("🚀 ¡La ruta y el inventario se han reiniciado por completo!")
                st.rerun()

    # El mapa ubicado obligadamente hasta el último elemento de la pantalla
    st.divider()
    st.markdown("### 🗺️ Mapa de Cobertura de Ruta")
    ocultar_visitados = st.checkbox("Ocultar del mapa clientes ya visitados", value=False)
    df_mapa = df_filtrado.copy()
    if ocultar_visitados:
        df_mapa = df_mapa[df_mapa['ESTATUS'] != 'Visitado']

    df_valid = df_mapa.dropna(subset=['COORD_LAT', 'COORD_LON'])
    if not df_valid.empty:
        centro_lat = df_valid['COORD_LAT'].mean()
        centro_lon = df_valid['COORD_LON'].mean()
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
        
        for idx, row in df_valid.iterrows():
            es_visitado = row['ESTATUS'] == 'Visitado'
            color_punto = "green" if es_visitado else "red"
            nombre_cliente = row.get('NOMBRE COMERCIAL', 'Cliente')
            
            folium.Marker(location=[row['COORD_LAT'], row['COORD_LON']], icon=folium.DivIcon(html=f"""<div style="font-size: 10px; font-weight: bold; color: black; background-color: rgba(255, 255, 255, 0.9); border: 1px solid {'green' if es_visitado else 'red'}; padding: 2px 5px; border-radius: 4px; white-space: nowrap; box-shadow: 0px 1px 3px rgba(0,0,0,0.3); text-align: center;">🏷️ {nombre_cliente}</div>""")).add_to(m)

            popup_html = f"""
            <div style="font-family: Arial; width: 190px;">
                <b>{nombre_cliente}</b><br>
                <small>{row.get('Direccion Completa', '')}</small><br>
                <b>Día:</b> {row.get('DIA_SEMANA', '')}<br>
                <b>Estatus:</b> <span style="color: {color_punto}; font-weight:bold;">{row['ESTATUS']}</span><br>
                <b>Cajas Vendidas:</b> {row.get('CAJAS_VENDIDAS', 0)}<br>
                <b>Cobrado:</b> ${row.get('MONTO_COBRADO', 0):,.2f}<br>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['COORD_LAT']},{row['COORD_LON']}" target="_blank" style="color: blue;">🧭 Abrir en Google Maps</a>
            </div>
            """
            folium.Marker(
                location=[row['COORD_LAT'], row['COORD_LON']],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"Ver detalles de {nombre_cliente}",
                icon=folium.Icon(color=color_punto, icon="shopping-cart", prefix='fa')
            ).add_to(m)
            
        st_folium(m, width="100%", height=450)
    else:
        st.info("No hay ubicaciones para mostrar en el mapa con los filtros seleccionados.")

else:
    st.error("No se pudieron cargar los datos o faltan columnas de coordenadas (`COORD_LAT`, `COORD_LON`).")
