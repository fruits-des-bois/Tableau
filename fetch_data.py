import requests
import pandas as pd
import re
import time

BASE_URL = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr"

session = requests.Session()

all_data = []
cursor = None

print("Récupération Hub'Eau...")

while True:

    params = {
        "code_entite": "H774201001",
        "grandeur_hydro": "H",
        "size": 20000
    }

    if cursor:
        params["cursor"] = cursor

    success = False

    for attempt in range(5):

        try:

            r = session.get(
                BASE_URL,
                params=params,
                timeout=60
            )

            if r.status_code in [200, 206]:

                j = r.json()

                data = j.get("data", [])

                all_data.extend(data)

                print(
                    f"{len(all_data)} observations récupérées"
                )

                next_url = j.get("next")

                if not next_url:
                    success = True
                    cursor = None
                    break

                match = re.search(
                    r"cursor=([^&]+)",
                    next_url
                )

                cursor = (
                    match.group(1)
                    if match
                    else None
                )

                success = True
                break

            print(
                f"Tentative {attempt+1}: HTTP {r.status_code}"
            )

        except Exception as e:

            print(
                f"Tentative {attempt+1}: {e}"
            )

        time.sleep(2)

    if not success:
        print("API indisponible")
        break

    if cursor is None:
        break

    time.sleep(0.5)

print(
    f"Observations récupérées : {len(all_data)}"
)

if len(all_data) == 0:
    raise Exception("Aucune donnée")

df = pd.DataFrame(all_data)

df.to_csv(
    "data.csv",
    index=False
)

print("data.csv créé")