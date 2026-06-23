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
import numpy as np

st.set_page_config(
    page_title="Prévisions de Hauteur d'Eau",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# CONFIG (UNE SEULE FOIS)
# =========================
st.set_page_config(page_title="Dashboard Eau", layout="wide")

st.title("📊 Dashboard hydrologie Beauvais")
# =========================
# IFRAME (GitHub Pages)
# =========================
if "tableaux_alternatifs" not in st.session_state:
    st.session_state.tableaux_alternatifs = False

if st.button("Afficher les tableaux actuels"):
    st.session_state.tableaux_alternatifs = not st.session_state.tableaux_alternatifs

col1, col2, col3 = st.columns(3)

with col1:

    if not st.session_state.tableaux_alternatifs:
        components.iframe(
            "https://fruits-des-bois.github.io/Tableau/debit_d_eau.html",
            height=320,
            scrolling=True
        )
    else:
        components.iframe(
            "https://fruits-des-bois.github.io/Tableau/debit_eau.html",
            height=320,
            scrolling=True
        )

with col2:

    if not st.session_state.tableaux_alternatifs:
        components.iframe(
            "https://fruits-des-bois.github.io/Tableau/hauteur_d_eau.html",
            height=320,
            scrolling=True
        )
    else:
        components.iframe(
            "https://fruits-des-bois.github.io/Tableau/hauteur_eau.html",
            height=320,
            scrolling=True
        )

with col3:
    components.iframe(
        "https://fruits-des-bois.github.io/Tableau/carte_beauvais.html",
        height=500,
        width=500,
        scrolling=False
    )

# =========================
# MÉTÉO OPEN-METEO
# =========================

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("Prévisions de pluies"):
        st.session_state.vue_pluie = "horaire"

with col_btn2:
    if st.button("pluie historiques"):
        st.session_state.vue_pluie = "journaliere"

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

# -----------------------------
# Graphique précipitations
# -----------------------------
if "vue_pluie" not in st.session_state:
    st.session_state.vue_pluie = "horaire"


# -----------------------------
# INITIALISATION
# -----------------------------
fig = None

# -----------------------------
# Vue horaire (prévisions)
# -----------------------------
if st.session_state.vue_pluie == "horaire":

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["datetime"],
            y=df["precipitation_mm"],
            name="Précipitations"
        )
    )

    fig.update_layout(
        width=800,
        height=450,
        title="Précipitations horaires sur 4 jours (prévisions)",
        xaxis_title="Date - Heure",
        yaxis_title="Précipitations (mm)"
    )

    fig.update_xaxes(
        dtick=6 * 60 * 60 * 1000,
        tickformat="%d/%m\n%Hh"
    )


# -----------------------------
# Vue historique (4 jours passés)
# -----------------------------
else:

    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=4)).strftime("%Y-%m-%d")

    url_hist = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude=49.4465"
        f"&longitude=2.127167"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
        "&hourly=precipitation"
        "&timezone=Europe/Paris"
    )

    r_hist = requests.get(url_hist)
    data_hist = r_hist.json()

    times_hist = pd.to_datetime(data_hist["hourly"]["time"])
    rain_hist = data_hist["hourly"]["precipitation"]

    df_hist = pd.DataFrame({
        "datetime": times_hist,
        "precipitation_mm": rain_hist
    })

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_hist["datetime"],
            y=df_hist["precipitation_mm"],
            name="Précipitations observées"
        )
    )

    fig.update_layout(
        width=800,
        height=450,
        title="Précipitations horaires des 4 derniers jours",
        xaxis_title="Date - Heure",
        yaxis_title="Précipitations (mm)",
        hovermode="x unified"
    )

    fig.update_xaxes(
        dtick=6 * 60 * 60 * 1000,
        tickformat="%d/%m\n%Hh"
    )

# -----------------------------
# AFFICHAGE UNIQUE (IMPORTANT)
# -----------------------------
st.plotly_chart(fig, use_container_width=False, key="pluie_chart")

# Début du code Streamlit
@st.cache_data(ttl=3600) # mise en cache des données pour 1 heure
def fetch_data():
    # --- 1. Récupération des hauteurs d'eau ---
    size_hauteur = 20000 # récupération des hauteurs d'eau
    # Construction de l'API Hub'Eau - Hauteur d'eau
    url_height = f"https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=H774201001&size={size_hauteur}&pretty&grandeur_hydro=H&fields=code_station,date_debut_serie,date_fin_serie,date_obs,resultat_obs,continuite_obs_hydro"
    # Envoi de la requête
    response_height = requests.get(url_height)
    # création d'un dataframe vide
    height_data_df = pd.DataFrame()
    # Gestion de la réponse si succès ou non
    if response_height.status_code == 200 or response_height.status_code == 206:
        # conversion du json réponse 
        data_height = response_height.json()
        if 'data' in data_height and data_height['data']:
            # transformation en dataframe pandas
            height_data_df = pd.DataFrame(data_height['data'])
            # On renomme les colonnes 'ini' : 'fin'
            rename_map = {
                'date_obs': 'Date d\'Observation',
                'resultat_obs': 'Hauteur d\'eau (mm)',
                'code_station': 'Code Station',
            }
            if 'continuite_obs_hydro' in height_data_df.columns:
                rename_map['continuite_obs_hydro'] = 'Continuité Obs Hydro'
            # renommage effectif
            height_data_df = height_data_df.rename(columns=rename_map)
            # Conversion des dates
            height_data_df['Date d\'Observation'] = pd.to_datetime(height_data_df['Date d\'Observation'])
            # Rééchantillonnage horaire
            height_data_df = height_data_df.set_index('Date d\'Observation').resample('1h')['Hauteur d\'eau (mm)'].mean().reset_index()
            height_data_df = height_data_df.dropna(subset=['Hauteur d\'eau (mm)'])
            # # Qte de données après resample 1h (donc total/5)
            print(f"Nombre de données de hauteur d'eau après resample : {len(height_data_df)}")

    # --- 2. Récupération des données de débit ---
    size_flow_historic = 20000
    # Construction de l'API Hub'Eau - Débit
    url_flow = f"https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=H774201001&size={size_flow_historic}&pretty&grandeur_hydro=Q&fields=code_station,date_obs,resultat_obs"
    # Envoie de la requête
    response_flow = requests.get(url_flow)
    df_flow_data = pd.DataFrame()
    # Gestion de la réponse
    if response_flow.status_code == 200 or response_flow.status_code == 206:
        data_flow = response_flow.json()
        if 'data' in data_flow and data_flow['data']:
            df_flow_data = pd.DataFrame(data_flow['data'])
            df_flow_data = df_flow_data.rename(columns={
                'date_obs': 'Date d\'Observation',
                'resultat_obs': 'Débit (l/s)'
            })
            df_flow_data['Date d\'Observation'] = pd.to_datetime(df_flow_data['Date d\'Observation'])
            # Rééchantillonnage horaire
            df_flow_data = df_flow_data.set_index('Date d\'Observation').resample('1h')['Débit (l/s)'].mean().reset_index()
            df_flow_data = df_flow_data.dropna(subset=['Débit (l/s)'])
            # Qte de données après resample 1h (donc total/5)
            print(f"Nombre de données de débit : {len(df_flow_data)}")

    # --- 3. Récupération des données historiques de pluies ---
    # Définition du lieu de mesure pour l'API etdes dates de crues (hors API)
    latitude = 49.4333
    longitude = 2.0833
    # 3 ans et demis de données avec les crues
    flood_days = {
        1999 : ["1999-12-24", "1999-12-29"],
        2001 : ["2001-03-24", "2001-03-24"],
        2018 : ["1999-12-24", "1999-12-29"],
        2021 : ["1999-06-21", "1999-06-29"]
    }
    all_precipitation_historical_dfs = []
    euro_paris_tz = pytz.timezone('Europe/Paris')
    # Boucle crue : attribue un début et une fin de période en fonction des dates données
    for year, days in flood_days.items():
            start_date = days[0]
            end_date = days[1]
            # Construction de l'API Météo données anciennes, définition de l'url
            url_open_meteo_archive = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={latitude}&longitude={longitude}"
                f"&start_date={start_date}&end_date={end_date}"
                f"&hourly=precipitation&timezone=Europe/Paris"
            )
            # La requête est envoyée à l'API météo
            response_archive = requests.get(url_open_meteo_archive)
            # Récation en cas de succès (code 200)
            if response_archive.status_code == 200:
                # Extraction du json des données météo
                data_archive = response_archive.json()
                # Boucle extraction dse dates des données météo
                if 'hourly' in data_archive:
                    hourly_archive_data = data_archive['hourly']
                    if 'time' in hourly_archive_data and 'precipitation' in hourly_archive_data:
                        # Création d'un dataframe avec les données météo
                        df_precipitation_year = pd.DataFrame({
                            'Date': pd.to_datetime(hourly_archive_data['time'], utc=True),
                            'Precipitation (mm)': hourly_archive_data['precipitation']
                        })
                        # Normalisation
                        df_precipitation_year["Hour"] = df_precipitation_year["Date"].dt.hour
                        # Tri temporel
                        df_precipitation_year = df_precipitation_year.sort_values("Date")
                        df_precipitation_year = df_precipitation_year.set_index("Date")
                        # Création des variables de pluies cumulées
                        df_precipitation_year["rain_24h"] = df_precipitation_year["Precipitation (mm)"].rolling(24).sum()
                        df_precipitation_year["rain_6h"] = df_precipitation_year["Precipitation (mm)"].rolling(6).sum()
                        df_precipitation_year["rain_lag_6h"] = df_precipitation_year["Precipitation (mm)"].shift(6)
                        df_precipitation_year["rain_max_12h"] = df_precipitation_year["Precipitation (mm)"].rolling(12).max()
                        #colonne date
                        df_precipitation_year = df_precipitation_year.reset_index()
                        # Gestion du fuseau horaire
                        all_precipitation_historical_dfs.append(df_precipitation_year)

    # --- 4. Récupératoin des prévisions météo ---
    # Construction de l'API prévisions météo, définition de l'url
    url_open_meteo = "https://api.open-meteo.com/v1/forecast?latitude=49.4333&longitude=2.0833&hourly=precipitation&timezone=Europe/Paris"
    response_open_meteo = requests.get(url_open_meteo)
    df_filtered = pd.DataFrame()
    # Réaction en cas de succès (code 200)
    if response_open_meteo.status_code == 200:
        data_open_meteo = response_open_meteo.json()
        if 'hourly' in data_open_meteo:
            hourly_data = data_open_meteo['hourly']
            if 'time' in hourly_data and 'precipitation' in hourly_data:
                df_precipitation = pd.DataFrame({
                    'Time': pd.to_datetime(hourly_data['time']),
                    'Precipitation (mm)': hourly_data['precipitation']
                })
                europe_paris_tz = pytz.timezone('Europe/Paris')
                df_precipitation['Time'] = df_precipitation['Time'].dt.tz_localize(europe_paris_tz, ambiguous='NaT')
                # gestion du fuseau horaire
                current_time_paris = datetime.now(europe_paris_tz)
                # Filtre appliqué sur les données pour conserver les prévisions pour j0+2h à j3
                j0_plus_2h = current_time_paris + timedelta(hours=2)
                j3 = current_time_paris + timedelta(days=3)
                df_filtered = df_precipitation[(df_precipitation['Time'] >= j0_plus_2h) & (df_precipitation['Time'] <= j3)]

    # Vérification et préparation dese données historiques
    if height_data_df.empty:
        st.error("Aucune donnée de hauteur d'eau actuelle n'a pu être récupérée. Impossible de continuer.")
        st.stop()

    # Cas où la  liste de pluie contient des donnée : fusion des dataframe 
    # Range les dataframe en ordre chronologique, réinitialise l'index
    # Mise en forme
    if len(all_precipitation_historical_dfs) > 0:
        df_historical_precipitation = (
            pd.concat(all_precipitation_historical_dfs)
            .sort_values('Date')
            .reset_index(drop=True)
        )
    # Cas où la liste est vide : un dataframe vide est crée
    else:
        df_historical_precipitation = pd.DataFrame(columns=['Date', 'Precipitation (mm)'])

    # Préparation des données de débit
    df_flow_data_for_merge = (
        df_flow_data.copy()
        # Vérifie si le dataframe débit est pas vide et dans ce cas les copient
        if not df_flow_data.empty 
        # Sinon on crée un dataframe rempli de 0
        else height_data_df[['Date d\'Observation']]
            .copy()
            .assign(**{'Débit (l/s)': 0.0})
    )

    # Vérifie si le dataframe météo ancienne est pas vide et dans ce cas les copient
    if not df_historical_precipitation.empty:
        df_historical_precipitation_for_merge = df_historical_precipitation.copy()
    # Sinon on crée un dataframe rempli de 0
    else:
        df_historical_precipitation_for_merge = height_data_df[['Date d\'Observation']].copy()
        df_historical_precipitation_for_merge = df_historical_precipitation_for_merge.rename(columns={'Date d\'Observation': 'Date'})
        df_historical_precipitation_for_merge['Precipitation (mm)'] = 0.0

    # Uniformisation des formats de date pour les données de hauteur d'eau
    # D'abord le fuseau horaire
    if height_data_df['Date d\'Observation'].dt.tz is None:
        height_data_df.loc[:, 'Date d\'Observation'] = height_data_df['Date d\'Observation'].dt.tz_localize(pytz.utc)
    else:
        height_data_df.loc[:, 'Date d\'Observation'] = height_data_df['Date d\'Observation'].dt.tz_convert(pytz.utc)

    # Uniformisation des formats de date pour les données de débit
    if df_flow_data_for_merge['Date d\'Observation'].dt.tz is None:
        df_flow_data_for_merge.loc[:, 'Date d\'Observation'] = df_flow_data_for_merge['Date d\'Observation'].dt.tz_localize(pytz.utc)
    else:
        df_flow_data_for_merge.loc[:, 'Date d\'Observation'] = df_flow_data_for_merge['Date d\'Observation'].dt.tz_convert(pytz.utc)

    df_historical_precipitation_resampled = df_historical_precipitation_for_merge
    df_historical_precipitation_resampled = df_historical_precipitation_resampled.rename(columns={'Date': "Date d'Observation"})

    # Fusion des sources de données : hauteur d'eau et débit
    historical_data = pd.merge(height_data_df[['Date d\'Observation', 'Hauteur d\'eau (mm)']],
                               df_flow_data_for_merge[['Date d\'Observation', 'Débit (l/s)']],
                               on='Date d\'Observation', how='outer')
    # Fusion des sources de données : débit et hauteur d'eau passées et précipitations passées
    historical_data = pd.merge(historical_data,
                               df_historical_precipitation_resampled,
                               on='Date d\'Observation', how='outer')

    # Tri et nettoyage des données 
    historical_data = historical_data.sort_values('Date d\'Observation').ffill()
    historical_data = historical_data.dropna(subset=['Hauteur d\'eau (mm)'])
    historical_data = historical_data.dropna()

    # Création de variables temporelles
    # Extraction des doonnées depuis les dates : an, mois, jour, heue, minutes...
    # pour rendre une date complète compréhensible opur un modèle
    historical_data.loc[:, 'year'] = historical_data['Date d\'Observation'].dt.year
    historical_data.loc[:, 'month'] = historical_data['Date d\'Observation'].dt.month
    historical_data.loc[:, 'day'] = historical_data['Date d\'Observation'].dt.day
    historical_data.loc[:, 'hour'] = historical_data['Date d\'Observation'].dt.hour
    historical_data.loc[:, 'minute'] = historical_data['Date d\'Observation'].dt.minute
    historical_data.loc[:, 'dayofweek'] = historical_data['Date d\'Observation'].dt.dayofweek
    historical_data.loc[:, 'dayofyear'] = historical_data['Date d\'Observation'].dt.dayofyear
    historical_data.loc[:, 'weekofyear'] = historical_data['Date d\'Observation'].dt.isocalendar().week.astype(int)

    # Création de variables de retard : hauteur précédente, débit précédent...
    # Insiste sur la dynamique d'une ou plusieurs variables
    historical_data.loc[:, "Hauteur_t-1"] = historical_data["Hauteur d'eau (mm)"].shift(1)
    historical_data.loc[:, "Hauteur_t-3"] = historical_data["Hauteur d'eau (mm)"].shift(3)
    historical_data.loc[:, "Hauteur_t-24"] = historical_data["Hauteur d'eau (mm)"].shift(24)
    historical_data.loc[:, "Débit_t-1"] = historical_data["Débit (l/s)"].shift(1)
    historical_data.loc[:, "Débit_t-6"] = historical_data["Débit (l/s)"].shift(6)
    # Pareil pour la pluie retardée historique
    historical_data["Pluie_lag_3h"] = historical_data["Precipitation (mm)"].shift(3)
    historical_data["Pluie_lag_6h"] = historical_data["Precipitation (mm)"].shift(6)
    historical_data["Pluie_lag_12h"] = historical_data["Precipitation (mm)"].shift(12)


    # Introduction des pluies cumulées : 6h et 24h
    historical_data.loc[:, "Pluie_6h"] = (
        historical_data["Precipitation (mm)"]
        .rolling(6)
        .sum()
    )
    historical_data.loc[:, "Pluie_24h"] = (
        historical_data["Precipitation (mm)"]
        .rolling(24)
        .sum()
    )
    # variable hydro  : décale la pluie de 3 heures, cumule sur 6 heures. Donc impact plus lent de la pluie
    historical_data["Pluie_cum_shifted"] = (
    historical_data["Precipitation (mm)"].shift(3).rolling(6).sum()
    )
    # Interaction pui- débit
    historical_data.loc[:, "Impact_pluie"] = (
    historical_data["Precipitation (mm)"] * historical_data["Débit (l/s)"]
    )
    # amplifie l'impact de la pluie (*1.5)
    historical_data.loc[:, "Pluie_effective"] = np.log1p(historical_data["Precipitation (mm)"]
    )
    # Introduction et définition de la variable crue
    historical_data.loc[:, "Crue"] = (
        historical_data["Hauteur d'eau (mm)"] > 175
    ).astype(int)

    # Définition des variables d''entrées (feature_new) et de sorties/cible (target_new)
    # variables temporelles : 'year', 'month', 'day', 'hour' et hydro : débit/hauteur d'eau
    features_new = [
        'year', 'month', 'day', 'hour', 'minute', 'dayofweek', 'dayofyear', 'weekofyear',
        'Débit (l/s)', 'Precipitation (mm)',
        "Hauteur_t-1", "Hauteur_t-3", "Hauteur_t-24",
        "Débit_t-1", "Débit_t-6","rain_24h","rain_6h",
        "rain_lag_6h","rain_max_12h"
    ]
    # LA variable à estimer : target_new (variable cible)
    target_new = 'Hauteur d\'eau (mm)'

    # Sélection des données dans le dataset, définition input-output
    # x_new => input, y_new => output 
    X_new = historical_data[features_new]
    y_new = historical_data[target_new]
    # Attribue un poids plus lourd aux crues 
    sample_weights = np.where(
        historical_data["Hauteur d'eau (mm)"] > 200,
        5,
        1
    )
    # Attribue un poids plus lourd aux pluies
    sample_weights = np.where(
        historical_data["Precipitation (mm)"] > 2,
        3,
        1
    )

    # Création d'un XGBoost (XGBRgressor) avec objective='reg:squarederror' (fonction de perte), n_estimator=nb d'arbres de décision et random_state rend les résultats reproductibles
    #Le 1er arbre fait une première approximation de la hauteur d’eau
    #Le 2e arbre corrige les erreurs du 1er
    #Le 3e arbre corrige encore les erreurs restantes, jusqu'au bout (100)
    #le random_state correspond à une graine de hasard, qui contrôle :
    #l’ordre aléatoire des données
    ##certaines décisions internes du modèle
    #la reproductibilité du résultat
    # Sans le random_state, le modèle change à chaque exécution ce qui diminue grandement sa fiabilité
    # Avec un random state = 42, le modèle reste plus ou moins le même à chaque exécution
    # Le random_state peux assurer la stabilité du modèle, le nombre d'estimateurs sa complexité
    model_enhanced = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)
        # Entraînement du modèle avec les inputs (x_new), pour générer des ouputs (y_new)
    model_enhanced.fit(
        X_new,
        y_new,
        sample_weight=sample_weights
    )


    # valeurs de hauteur d'eau générées
    # Récupère les dates les plus récentes
    last_observation_date = height_data_df['Date d\'Observation'].max()
    # Définition de la période de prévision
    future_period_hours = 3 * 24
    # Création des dates futures avec un pas de 1h, qui commence 1h après le dernière observation
    future_dates = pd.date_range(
        start=last_observation_date + pd.Timedelta(hours=1),
        periods=future_period_hours,
        freq='1h'
    )

    # Création des colonne du dataframe prévisions, avec une caractéristique par colonne
    # Permet au modèle d'exploiter la date, comme plus haut
    df_future = pd.DataFrame({'Date d\'Observation': future_dates})
    df_future.loc[:, 'year'] = df_future['Date d\'Observation'].dt.year
    df_future.loc[:, 'month'] = df_future['Date d\'Observation'].dt.month
    df_future.loc[:, 'day'] = df_future['Date d\'Observation'].dt.day
    df_future.loc[:, 'hour'] = df_future['Date d\'Observation'].dt.hour
    df_future.loc[:, 'minute'] = df_future['Date d\'Observation'].dt.minute
    df_future.loc[:, 'dayofweek'] = df_future['Date d\'Observation'].dt.dayofweek
    df_future.loc[:, 'dayofyear'] = df_future['Date d\'Observation'].dt.dayofyear
    df_future.loc[:, 'weekofyear'] = df_future['Date d\'Observation'].dt.isocalendar().week.astype(int)

    # Estimation du débit futur
    # Si le dataframe débit est pas vide, le dataframe prévision débit prend sa valeur, sinon c'est la valeur 0
    # Si on met estimated_future_flow = df_flow_data['Débit (l/s)'].mean(), seul un débit moyen est conservé
    # Si le dataframe débit est pas vide, on calcule la colonne débit puis sa moyenne ou non 
    # Si vide, c'est 0
    estimated_future_flow = df_flow_data['Débit (l/s)'] if not df_flow_data.empty else 0.0

    # Vérification du fuseau horaire pour le débit future
    # Si il n'y a pas de fuseau définit, on définit en UTC. Sinon on convertit
    if df_future['Date d\'Observation'].dt.tz is None:
        df_future.loc[:, 'Date d\'Observation'] = df_future['Date d\'Observation'].dt.tz_localize(pytz.utc)
    else:
        df_future.loc[:, 'Date d\'Observation'] = df_future['Date d\'Observation'].dt.tz_convert(pytz.utc)

    # Vérification du fuseau horaire pour les prévisions météo
    # Si il n'y a pas de fuseau définit, on définit en UTC. Sinon on convertit
    if df_filtered['Time'].dt.tz is None:
        df_filtered.loc[:, 'Time'] = df_filtered['Time'].dt.tz_localize(pytz.timezone('Europe/Paris'), ambiguous='NaT').dt.tz_convert(pytz.utc)
    elif df_filtered['Time'].dt.tz != pytz.utc:
        df_filtered.loc[:, "Time"] = df_filtered["Time"].dt.tz_convert(pytz.utc)

    # Rééchantillonnage des précipitations
    # Time passe en index, rééchantillonnage sur 1h plus moyenne horaire
    future_precipitation_resampled = df_filtered.set_index('Time').resample('1h').mean().reset_index()
    # Renommage de la colonne
    future_precipitation_resampled = future_precipitation_resampled.rename(columns={'Time': 'Date d\'Observation'})
    # Fusion avec les dates futures
    df_future_enhanced = pd.merge(df_future,
                                  future_precipitation_resampled,
                                  on='Date d\'Observation',
                                  how='left')

    # Création des variables de cumul
    df_future_enhanced["Date"] = df_future_enhanced["Date d'Observation"]
    df_future_enhanced = df_future_enhanced.sort_values("Date d'Observation")
    df_future_enhanced = df_future_enhanced.set_index("Date d'Observation")

    df_future_enhanced["rain_24h"] = df_future_enhanced["Precipitation (mm)"].rolling(24).sum()
    df_future_enhanced["rain_6h"] = df_future_enhanced["Precipitation (mm)"].rolling(6).sum()
    df_future_enhanced["rain_lag_6h"] = df_future_enhanced["Precipitation (mm)"].shift(6)
    df_future_enhanced["rain_max_12h"] = df_future_enhanced["Precipitation (mm)"].rolling(12).max()
    # Normalisation
    df_future_enhanced = df_future_enhanced.reset_index()
    # Gestion des NaN
    df_future_enhanced = df_future_enhanced.fillna(0)
    # On remplace les valeurs manquantes
    df_future_enhanced.loc[:, 'Precipitation (mm)'] = df_future_enhanced['Precipitation (mm)'].fillna(0.0)
    # Prévoit un débit constant sur la durée des prévision
    df_future_enhanced.loc[:, 'Débit (l/s)'] = estimated_future_flow

    # Créatiopn des variables prédictives fictives (dummy_predictions)
    # Récupère la dernière observation : iloc[-1], et applique sa valeur aux prédictions futures
    dummy_predictions = pd.DataFrame({'Hauteur d\'eau prévue (mm)': [historical_data["Hauteur d'eau (mm)"].iloc[-1]] * len(df_future_enhanced)})
    # Récupère les dernières observations (t-1,t-3...) le shift décale les valeurs d'une ou plusieurs ligns
    df_future_enhanced.loc[:, "Hauteur_t-1"] = dummy_predictions['Hauteur d\'eau prévue (mm)'].shift(1)
    df_future_enhanced.loc[:, "Hauteur_t-3"] = dummy_predictions['Hauteur d\'eau prévue (mm)'].shift(3)
    df_future_enhanced.loc[:, "Hauteur_t-24"] = dummy_predictions['Hauteur d\'eau prévue (mm)'].shift(24)
    df_future_enhanced.loc[:, "Débit_t-1"] = df_future_enhanced["Débit (l/s)"].shift(1)
    df_future_enhanced.loc[:, "Débit_t-6"] = df_future_enhanced["Débit (l/s)"].shift(6)

    last_historical_height = historical_data["Hauteur d'eau (mm)"].iloc[-1]
    last_historical_debit = historical_data["Débit (l/s)"].iloc[-1]

    df_future_enhanced.loc[:, "Hauteur_t-1"] = df_future_enhanced["Hauteur_t-1"].fillna(last_historical_height)
    df_future_enhanced.loc[:, "Hauteur_t-3"] = df_future_enhanced["Hauteur_t-3"].fillna(last_historical_height)
    df_future_enhanced.loc[:, "Hauteur_t-24"] = df_future_enhanced["Hauteur_t-24"].fillna(last_historical_height)
    df_future_enhanced.loc[:, "Débit_t-1"] = df_future_enhanced["Débit_t-1"].fillna(last_historical_debit)
    df_future_enhanced.loc[:, "Débit_t-6"] = df_future_enhanced["Débit_t-6"].fillna(last_historical_debit)

    # Somme des précipitations sur 6h puis 24h
    df_future_enhanced["Pluie_6h"] = (
    df_future_enhanced["Precipitation (mm)"].rolling(6, min_periods=1).sum()
    )
    df_future_enhanced["Pluie_24h"] = (
        df_future_enhanced["Precipitation (mm)"].rolling(24, min_periods=1).sum()
    )

    # Interaction pui- débit
    df_future_enhanced.loc[:, "Impact_pluie"] = (
    df_future_enhanced["Precipitation (mm)"] * df_future_enhanced["Débit (l/s)"]
    )
    # amplifie l'impact de la pluie 
    df_future_enhanced["Pluie_effective"] = np.log1p(df_future_enhanced["Precipitation (mm)"])
    # Sélection des variables du modèle
    # On garde les colonnes utiilisées lors de l'entraînement
    X_future_enhanced = df_future_enhanced[features_new]

    # Vérification s'il y a des valeurs manquantes, si oui on remplit de 0
    if X_future_enhanced.isnull().any().any():
        X_future_enhanced = X_future_enhanced.fillna(0)

    # Prédictions du modèle, avec réinjection des variables
    # Le modèle prend en compte les variables en sa possession (features_new) et renvoie la hauteur d'eau
    # Plus initialise un historique hauteur d'eau, débit, précipitation
    historique_hauteur = list(historical_data["Hauteur d'eau (mm)"].tail(24))
    historique_debit = list(historical_data["Débit (l/s)"].tail(6))
    historique_pluie = list(historical_data["Precipitation (mm)"].tail(24))

    predictions = []
    # Boucle variables historiques
    for i in range(len(df_future_enhanced)):

        row = df_future_enhanced.iloc[[i]].copy()

        # ----- Variables retardées hauteur -----
        row["Hauteur_t-1"] = historique_hauteur[-1]
        row["Hauteur_t-3"] = historique_hauteur[-3]
        row["Hauteur_t-24"] = historique_hauteur[-24]

        def safe_get(hist, k):
            return hist[-k] if len(hist) >= k else hist[0]

        # ----- Variables retardées débit -----
        row["Débit_t-1"] = historique_debit[-1]
        row["Débit_t-6"] = historique_debit[-6]

        # ----- Pluie cumulée -----
        row["Pluie_6h"] = sum(historique_pluie[-6:])
        row["Pluie_24h"] = sum(historique_pluie[-24:])

        # ----- Prédiction -----
        prediction = model_enhanced.predict(row[features_new])[0]

        predictions.append(prediction)

        # Mise à jour de l'historique hauteur
        historique_hauteur.append(prediction)
        historique_hauteur = historique_hauteur[-24:]
        # On suppose le débit constant
        nouveau_debit = historique_debit[-1]
        historique_debit.append(nouveau_debit)
        historique_debit = historique_debit[-6:]
        # Mise à jour des précipitations
        pluie = row["Precipitation (mm)"].iloc[0]
        historique_pluie.append(pluie)
        historique_pluie = historique_pluie[-24:]

    # Construire le dataframe
    df_predictions_future_enhanced = pd.DataFrame({
    "Date et heure": df_future_enhanced["Date d'Observation"],
    "Hauteur d'eau prévue (mm)": predictions
    })
    

    return df_predictions_future_enhanced


with st.spinner('Chargement des données et calcul des prévisions...'):
    predictions_df = fetch_data()

fig = px.line(
    predictions_df,
    width=800,
    height=500,
    x="Date et heure",
    y="Hauteur d'eau prévue (mm)",
    title="Prévisions futures des hauteurs d'eau",
    labels={
        "Date et heure": "Date et Heure",
        "Hauteur d'eau prévue (mm)": "Hauteur d'eau (mm)"
    }
)
fig.update_traces(
    mode="lines",
    hovertemplate="%{y:.2f} mm<extra></extra>"
)
fig.update_layout(
    xaxis_title="Date et Heure",
    yaxis_title="Hauteur d'eau (mm)",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# l.27 : Construction de l'API Hub'Eau - Hauteur d'eau
# l.49 : # Construction de l'API Hub'Eau - Débit
# l.67 : définition des dates pour les crues
# l.81 : Construction de l'API Météo pour les pluies passées
# l.108 : Construction de l'API météo prévisions pluies
# l. 272-278 :  Création d'un XGBoost (XGBRgressor) avec objective='reg:squarederror' (fonction de perte), n_estimator=nb d'arbres de décision et random_state rend les résultats reproductibles
#Le 1er arbre fait une première approximation de la hauteur d’eau
#Le 2e arbre corrige les erreurs du 1er
#Le 3e arbre corrige encore les erreurs restantes, jusqu'au bout (100)
#le random_state correspond à une graine de hasard, qui contrôle :
#l’ordre aléatoire des données
##certaines décisions internes du modèle
#la reproductibilité du résultat
# Sans le random_state, le modèle change à chaque exécution ce qui diminue grandement sa fiabilité
# Avec un random state = 42, le modèle reste plus ou moins le même à chaque exécution
# Le random_state peux assurer la stabilité du modèle, le nombre d'estimateurs sa complexité
# l.284 : définition des plages de prévisions
# l. 286 : moyenne horaire pour les prévisions
# l.379 : Affichage et conception du graphique