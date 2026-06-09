import pandas as pd

df = pd.read_csv("data.csv")

# Conversion en datetime
df["date_obs"] = pd.to_datetime(df["date_obs"])

# Première et dernière mesure
print("Première mesure :", df["date_obs"].min())
print("Dernière mesure :", df["date_obs"].max())

# Durée totale
duree = df["date_obs"].max() - df["date_obs"].min()

print("Durée totale :", duree)
print(f"Durée en heures : {duree.total_seconds() / 3600:.2f}")
print(f"Durée en jours  : {duree.total_seconds() / 86400:.2f}")