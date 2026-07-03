import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# =====================================================
# Configuración de la página
# =====================================================

st.set_page_config(
    page_title="ECOBICI CDMX",
    page_icon="🚲",
    layout="wide"
)

# =====================================================
# Función para descargar datos
# =====================================================

@st.cache_data(ttl=300)  # Actualiza cada 5 minutos
def obtener_datos_ecobici():

    url_info = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_information.json"
    url_status = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json"

    # Información de estaciones
    resp_info = requests.get(url_info).json()
    df_info = pd.DataFrame(resp_info["data"]["stations"])

    # Estado en tiempo real
    resp_status = requests.get(url_status).json()
    df_status = pd.DataFrame(resp_status["data"]["stations"])

    # Merge
    tabla_final = pd.merge(
        df_info[
            ["station_id", "name", "lat", "lon", "capacity"]
        ],
        df_status[
            [
                "station_id",
                "num_bikes_available",
                "num_docks_available",
                "is_renting"
            ]
        ],
        on="station_id"
    )

    # Renombrar columnas
    tabla_final.columns = [
        "ID",
        "Nombre",
        "Latitud",
        "Longitud",
        "Capacidad_Total",
        "Bicis_Disponibles",
        "Puertos_Libres",
        "Operativa"
    ]

    tabla_final["Operativa"] = tabla_final["Operativa"].map(
        {1: "Sí", 0: "No"}
    )

    return tabla_final

# =====================================================
# Cargar datos
# =====================================================

df_ecobici = obtener_datos_ecobici()

# =====================================================
# Título y Sidebar (Filtros)
# =====================================================

st.title("🚲 Cicloestaciones ECOBICI CDMX")

st.markdown(
    "Disponibilidad de bicicletas y estaciones en tiempo real."
)

# Elemento solicitado: Checkbox en la barra lateral
st.sidebar.header("Filtros de Búsqueda")
solo_con_bicis = st.sidebar.checkbox("Mostrar solo estaciones con bicicletas disponibles", value=False)

# Aplicar el filtro condicionalmente basado en el estado del checkbox
if solo_con_bicis:
    df_filtrado = df_ecobici[df_ecobici["Bicis_Disponibles"] > 0]
else:
    df_filtrado = df_ecobici

# =====================================================
# Métricas (Basadas en los datos filtrados)
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Estaciones mostradas",
        len(df_filtrado)
    )

with col2:
    st.metric(
        "Bicicletas disponibles",
        int(df_filtrado["Bicis_Disponibles"].sum())
    )

with col3:
    st.metric(
        "Puertos libres",
        int(df_filtrado["Puertos_Libres"].sum())
    )

# =====================================================
# Mapa (Cambiado a df_filtrado)
# =====================================================

fig = px.scatter_mapbox(
    df_filtrado,
    lat="Latitud",
    lon="Longitud",
    hover_name="Nombre",
    color="Bicis_Disponibles",          # El color cambia según la cantidad de bicis
    size="Bicis_Disponibles",           # El tamaño del círculo crece si hay más bicis
    color_continuous_scale=px.colors.sequential.Viridis, # Escala de colores vistosa
    size_max=15,                        # Tamaño máximo del círculo
    hover_data={
        "Bicis_Disponibles": True,
        "Puertos_Libres": True,
        "Capacidad_Total": True,
        "Latitud": False,
        "Longitud": False
    },
    zoom=11,
    height=700
)

fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0, "t":0, "l":0, "b":0}
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# Tabla de datos (Cambiado a df_filtrado)
# =====================================================

st.subheader("Datos de las estaciones")

st.dataframe(
    df_filtrado,
    use_container_width=True
)
