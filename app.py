import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Ruta de Visitas y Venta 📍", layout="wide")

st.title("Ruta de Visitas y Venta 📍")

# --- SIMULACIÓN DE DATOS DE CLIENTES ---
if "df_clientes" not in st.session_state:
    data = {
        "CLIENTE": [
            "EL TÚNEL - CENADURÍA",
            "ABARROTES EL PASO",
            "MINISUPER LA ISLA",
            "FRUTERÍA DON CHUY",
        ],
        "DIA": ["JUEVES", "JUEVES", "VIERNES", "VIERNES"],
        "RUTA": ["Ruta 1", "Ruta 1", "Ruta 2", "Ruta 2"],
        "ESTATUS": ["Pendiente", "Pendiente", "Pendiente", "Pendiente"],
    }
    st.session_state["df_clientes"] = pd.DataFrame(data)

# Asegurar estrictamente que la columna ESTATUS sea de tipo texto (string)
st.session_state["df_clientes"]["ESTATUS"] = st.session_state["df_clientes"][
    "ESTATUS"
].astype(str)

df = st.session_state["df_clientes"]

# --- 1. CONTROL DE INVENTARIO INICIAL ---
st.subheader("📦 Control de Inventario Inicial (Carga del Día)")
st.write("Configura las cajas disponibles para la venta de hoy:")

col1, col2 = st.columns(2)
with col1:
    inv_t355 = st.number_input(
        "TONICOL NR PET 355 ML ($160/caja)", min_value=0, value=6
    )
    inv_t600 = st.number_input(
        "TONICOL FULL SUGAR PET 600 ML ($230/caja)", min_value=0, value=6
    )
with col2:
    inv_t2l = st.number_input(
        "TONICOL NR PET 2 LTS ($180/caja)", min_value=0, value=6
    )
    inv_agua = st.number_input(
        "AGUA DEL YAUCO NR 1/2 LT ($70/caja)", min_value=0, value=0
    )

# Precios unitarios por caja
precios = {
    "TONICOL NR PET 355 ML": 160,
    "TONICOL FULL SUGAR PET 600 ML": 230,
    "TONICOL NR PET 2 LTS": 180,
    "AGUA DEL YAUCO NR 1/2 LT": 70,
}

# --- 2. FILTROS DE OPERACIÓN ---
st.subheader("🔍 Filtros de Operación (Día y Ruta)")
col_f1, col_f2 = st.columns(2)
with col_f1:
    dia_sel = st.selectbox("📅 Selecciona el Día:", ["JUEVES", "VIERNES"])
with col_f2:
    ruta_sel = st.selectbox("🚚 Selecciona Ruta:", ["Ruta 1", "Ruta 2"])

# Filtrar clientes según selección
df_filtrado = df[(df["DIA"] == dia_sel) & (df["RUTA"] == ruta_sel)]

total_clientes = len(df_filtrado)
visitados = len(df_filtrado[df_filtrado["ESTATUS"] == "Visitado"])
pendientes = total_clientes - visitados

st.markdown(
    f"**📍 Control de Ruta y Cobertura ({dia_sel})** | 🏪 **TOTAL CLIENTES:** {total_clientes} | 🟢 **VISITADOS:** {visitados} | 🔴 **PENDIENTES:** {pendientes}"
)

# --- 3. REGISTRAR VENTA Y CHECK-IN ---
st.subheader("📝 Registrar Venta y Check-in por Producto")

if total_clientes > 0:
    cliente_sel = st.selectbox(
        "Selecciona Cliente a Visitar:", df_filtrado["CLIENTE"].tolist()
    )

    st.markdown(
        f"🧭 [Click aquí para navegar con Google Maps a {cliente_sel}](https://maps.google.com/?q={cliente_sel})"
    )

    st.write("Selecciona las cantidades a vender:")
    c_v1, c_v2 = st.columns(2)
    with c_v1:
        v_t355 = st.number_input(
            f"TONICOL NR PET 355 ML (Disp: {inv_t355}) - $160",
            min_value=0,
            max_value=inv_t355,
            value=0,
        )
        v_t600 = st.number_input(
            f"TONICOL FULL SUGAR PET 600 ML (Disp: {inv_t600}) - $230",
            min_value=0,
            max_value=inv_t600,
            value=0,
        )
    with c_v2:
        v_t2l = st.number_input(
            f"TONICOL NR PET 2 LTS (Disp: {inv_t2l}) - $180",
            min_value=0,
            max_value=inv_t2l,
            value=0,
        )
        v_agua = st.number_input(
            f"AGUA DEL YAUCO NR 1/2 LT (Disp: {inv_agua}) - $70",
            min_value=0,
            max_value=inv_agua,
            value=0,
        )

    total_cajas = v_t355 + v_t600 + v_t2l + v_agua
    total_cobrar = (
        (v_t355 * precios["TONICOL NR PET 355 ML"])
        + (v_t600 * precios["TONICOL FULL SUGAR PET 600 ML"])
        + (v_t2l * precios["TONICOL NR PET 2 LTS"])
        + (v_agua * precios["AGUA DEL YAUCO NR 1/2 LT"])
    )

    st.markdown(
        f"### 📦 Total Cajas Venta: {total_cajas} | 💵 Total a Cobrar: ${total_cobrar:,.2f}"
    )

    comentarios = st.text_area("Comentarios / Notas de entrega:")

    if st.button("✅ Confirmar Venta y Registrar Visita"):
        # Localizar índice exacto en el DataFrame original asegurando tipos compatibles
        idx_target = df.index[df["CLIENTE"] == cliente_sel]
        if len(idx_target) > 0:
            # Asignación segura sin error de tipo gracias a .astype(str) previo
            df.loc[idx_target, "ESTATUS"] = "Visitado"
            st.session_state["df_clientes"] = df
            st.success(
                f"¡Visita registrada con éxito para **{cliente_sel}**! Total cobrado: ${total_cobrar:,.2f}"
            )
            st.rerun()
else:
    st.info("No hay clientes registrados para los filtros seleccionados.")
