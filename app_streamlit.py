import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# =========================
# CONFIG (UNE SEULE FOIS)
# =========================
st.set_page_config(page_title="Dashboard Eau", layout="wide")

st.title("📊 Dashboard")
# =========================
# IFRAME (GitHub Pages)
# =========================
col1, col2 = st.columns(2)

with col1:
    components.iframe(
        "https://fruits-des-bois.github.io/Tableau/debit_d_eau.html",
        height=320,
        scrolling=True
    )

with col2:
    components.iframe(
        "https://fruits-des-bois.github.io/Tableau/hauteur_d_eau.html",
        height=320,
        scrolling=True
    )

    # =========================
# CARTE FOLIUM
# =========================

st.subheader("🗺️ Carte")

# -------------------------
# CENTRE DE LA CARTE
# -------------------------

center_lat, center_lon = 49.436120, 2.083986

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    control_scale=True,
    tiles=None
)

# -------------------------
# FONDS DE CARTE
# -------------------------

folium.TileLayer(
    tiles="OpenStreetMap",
    name="OpenStreetMap"
).add_to(m)

# -------------------------
# FONCTION AJOUT POINT
# -------------------------

def add_point(lat, lon, label, color):

    folium.CircleMarker(
        location=[lat, lon],
        radius=3,
        color=color,
        weight=3,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        tooltip=folium.Tooltip(
            label,
            permanent=False,
            sticky=True
        ),
        popup=folium.Popup(
            f"<b>{label}</b>",
            max_width=300
        )
    ).add_to(m)

# -------------------------
# STATIONS
# -------------------------

add_point(
    49.426120,
    2.083986,
    "Station hydrométrique de Beauvais",
    "blue"
)

add_point(
    49.434482,
    2.085117,
    "Station météo",
    "red"
)

# -------------------------
# POLYGONE GEOJSON
# -------------------------

folium.GeoJson(
    "beauvais.geojson",
    name="Limites de Beauvais",
    style_function=lambda feature: {
        "fillColor": "none",
        "color": "black",
        "weight": 2,
        "fillOpacity": 0
    },
    tooltip="Limites de Beauvais"
).add_to(m)

# -------------------------
# FLECHE NORD
# -------------------------

north_arrow = """
<div style="
position: fixed;
top: 20px;
left: 60px;
z-index:9999;
font-size:40px;
font-weight:bold;
background:white;
padding:5px;
border-radius:5px;
">
N<br>↑
</div>
"""

m.get_root().html.add_child(
    folium.Element(north_arrow)
)

# -------------------------
# LEGENDE
# -------------------------

layers = [
    {"symbol": "🔵", "label": "Station hydrométrique"},
    {"symbol": "🔴", "label": "Station météo"},
    {"symbol": "➖", "label": "Limites de Beauvais"}
]

# -------------------------
# AFFICHAGE
# -------------------------

with st.expander("🗺️ Afficher / Masquer la carte", expanded=False):

    col_map, col_leg = st.columns(
            [0.7, 1],
            gap="small"
        )

    with col_map:

        st_folium(
            m,
            width=650,
            height=450
        )

    with col_leg:

        st.markdown("### Légende")

        for layer in layers:
            st.markdown(
                f"{layer['symbol']} {layer['label']}"
            )
# =========================
# MÉTÉO OPEN-METEO
# =========================
st.subheader("🌧️ Prévisions de précipitations (4 jours)")

url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=49.4333"
    "&longitude=2.0833"
    "&hourly=precipitation"
    "&timezone=Europe/Paris"
)

r = requests.get(url)
data = r.json()

times = pd.to_datetime(data["hourly"]["time"])
rain = data["hourly"]["precipitation"]

df = pd.DataFrame({
    "datetime": times,
    "precipitation_mm": rain
})

now = pd.Timestamp.now()
end = now + pd.Timedelta(days=4)

df = df[(df["datetime"] >= now) & (df["datetime"] <= end)]

df["label"] = df["datetime"].dt.strftime("%d/%m - %Hh")

fig_rain = go.Figure()

fig_rain.add_trace(
    go.Bar(
        x=df["datetime"],
        y=df["precipitation_mm"],
        name="Précipitations"
    )
)

fig_rain.update_layout(
    width=800,
    height=450,
    xaxis_title="Date - Heure",
    yaxis_title="Précipitations (mm)",
    hovermode="x unified"
)

fig_rain.update_xaxes(
    dtick=6 * 60 * 60 * 1000,  # 6 heures en millisecondes
    tickformat="%d/%m\n%Hh",
    tickangle=0
)


# =========================
# FORECAST LOCAL
# =========================

try:
    with open("forecast.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=df["date"],
        y=df["prediction"],
        mode="lines",
        name="Prévisions"
    ))

    fig2.update_layout(
        width=800,
        height=500,
        xaxis_title="Temps",
        yaxis_title="Hauteur d'eau (mm)"
    )



except FileNotFoundError:
    st.error("forecast.json introuvable. Lance d'abord ton script de génération.")

# =========================
# GRAPHIQUES CÔTE À CÔTE
# =========================

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_rain, use_container_width=False)

with col2:
    st.subheader("📈 Prévisions de hauteur d'eau")
    st.plotly_chart(fig2, use_container_width=False)