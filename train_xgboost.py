import pandas as pd
import numpy as np
import json
from datetime import timedelta
from xgboost import XGBRegressor

# =========================
# CHARGEMENT DONNÉES
# =========================

df = pd.read_csv("data.csv")

df["date_obs"] = pd.to_datetime(df["date_obs"], errors="coerce")
df["resultat_obs"] = pd.to_numeric(df["resultat_obs"], errors="coerce")

df = df.dropna(subset=["date_obs", "resultat_obs"])
df = df.sort_values("date_obs")

df["y"] = df["resultat_obs"]

# =========================
# MOYENNE HORAIRE
# =========================

hourly = df.groupby(pd.Grouper(key="date_obs", freq="1h")).agg({"y": "mean"}).reset_index()
hourly = hourly.rename(columns={"date_obs": "date_hour"})

# =========================
# FEATURES SIMPLES (robuste)
# =========================

hourly["hour"] = hourly["date_hour"].dt.hour
hourly["weekday"] = hourly["date_hour"].dt.weekday

hourly["hour_sin"] = np.sin(2*np.pi*hourly["hour"]/24)
hourly["hour_cos"] = np.cos(2*np.pi*hourly["hour"]/24)

hourly["lag1"] = hourly["y"].shift(1)
hourly["lag2"] = hourly["y"].shift(2)
hourly["lag3"] = hourly["y"].shift(3)

hourly["roll3"] = hourly["y"].rolling(3).mean()

hourly = hourly.dropna()

# =========================
# MODELE
# =========================

features = [
    "lag1", "lag2", "lag3",
    "roll3",
    "hour_sin", "hour_cos",
    "weekday"
]

X = hourly[features]
y = hourly["y"]

model = XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    objective="reg:squarederror",
    random_state=42
)

model.fit(X, y)

# =========================
# PREVISION 72H
# =========================

history = hourly["y"].tolist()
last_date = hourly["date_hour"].iloc[-1]

forecast = []

for i in range(72):

    dt = last_date + timedelta(hours=i+1)

    row = pd.DataFrame([{
        "lag1": history[-1],
        "lag2": history[-2],
        "lag3": history[-3],
        "roll3": np.mean(history[-3:]),
        "hour_sin": np.sin(2*np.pi*dt.hour/24),
        "hour_cos": np.cos(2*np.pi*dt.hour/24),
        "weekday": dt.weekday()
    }])

    pred = float(model.predict(row)[0])

    history.append(pred)

    forecast.append({
        "date": dt.strftime("%Y-%m-%d %H:%M"),
        "prediction": round(pred, 2)
    })

# =========================
# SAUVEGARDE UNIQUEMENT
# =========================

with open("forecast.json", "w", encoding="utf-8") as f:
    json.dump(forecast, f, indent=2, ensure_ascii=False)

print("forecast.json généré ✔ (uniquement prévisions)")