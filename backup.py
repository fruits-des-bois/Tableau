import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
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

st.title("📊 Dashboard hydrologie Beauvais")
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

components.iframe(
    "https://fruits-des-bois.github.io/Tableau/carte_beauvais.html",
    height=500,
    width=500,
    scrolling=False
)

# =========================
# MÉTÉO OPEN-METEO
# =========================
st.subheader("🌧️ Prévisions de précipitations (4 jours)")

url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=49.4465"
    "&longitude=2.127167"
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

st.plotly_chart(fig_rain, use_container_width=False)
