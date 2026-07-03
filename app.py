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
    
    # -------------------------------------------------
    # NUEVO: Cálculo del porcentaje de disponibilidad
    # -------------------------------------------------
    # Evitamos división por cero si alguna capacidad total viene en 0
    tabla_final["%_Disponibilidad"] = (tabla_final["Bicis_Disponibles"] / tabla_final["Capacidad_Total"].replace(0, 1)) * 100
    
    # Creamos una columna de texto con formato "%" para el hover
    tabla_final["Porcentaje_Texto"] = tabla_final["%_Disponibilidad"].round(1).astype(str) + "%"

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
    df_filtrado = df_ecobici[df_ecobici["Bicis_Disponibles"] > 0].copy()
else:
    df_filtrado = df_ecobici.copy()

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
# Mapa (Modificado para mostrar Porcentajes)
# =====================================================

# Paleta secuencial sugerida: 'YlGnBu' (Amarillo-Verde-Azul) o 'Blues', 'Viridis', etc.
# Cambiar 'color' a '%_Disponibilidad' y definir rango de 0 a 100
fig = px.scatter_mapbox(
    df_filtrado,
    lat="Latitud",
    lon="Longitud",
    hover_name="Nombre",
    color="%_Disponibilidad",               # El color ahora depende del porcentaje real (0-100)
    size="Capacidad_Total",                 # El tamaño representa la capacidad total de la estación
    color_continuous_scale=px.colors.sequential.YlGnBu, # Paleta secuencial muy clara para mapas
    range_color=[0, 100],                   # Forzamos la barra a ir de 0% a 100%
    size_max=12,                            # Control del tamaño de los círculos
    hover_data={
        "Porcentaje_Texto": True,           # Mostramos la etiqueta formateada como "XX.X%"
        "Bicis_Disponibles": True,          # Valor nominal
        "Puertos_Libres": True,             # Valor nominal
        "Capacidad_Total": True,
        "%_Disponibilidad": False,          # Ocultamos la numérica cruda para que no se duplique
        "Latitud": False,
        "Longitud": False
    },
    zoom=11,
    height=700
)

# Cambiar los títulos de la barra de colores (Colorbar) y Hover
fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0, "t":0, "l":0, "b":0},
    coloraxis_colorbar=dict(
        title="Disponibilidad (%)",
        ticksuffix="%"
    )
)

# Renombrar los labels visibles en la ventanita flotante (Hover)
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br><br>Disponibilidad: %{customdata[0]}<br>Bicis Disponibles: %{customdata[1]}<br>Puertos Libres: %{customdata[2]}<br>Capacidad Total: %{customdata[3]}<extra></extra>"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# Tabla de datos (Cambiado a df_filtrado)
# =====================================================

st.subheader("Datos de las estaciones")

# Mostramos columnas más ordenadas y limpias en el DataFrame
columnas_visibles = [
    "ID", "Nombre", "Bicis_Disponibles", "Puertos_Libres", 
    "Capacidad_Total", "Porcentaje_Texto", "Operativa"
]

st.dataframe(
    df_filtrado[columnas_visibles].rename(columns={"Porcentaje_Texto": "% Disponibilidad"}),
    use_container_width=True
)
