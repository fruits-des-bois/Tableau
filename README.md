````markdown
📊 Projet Streamlit

Une application web développée en Python offrant une interface interactive pour visualiser et traiter des données, sur un Dashboard Streamlit.
L'application affiche un dashboard contenant un historique des 5 dernières mesures de débits et hauteurs d'eau,
les prévisions de pluies pour 3 jours et une prévision des hauteurs d'eau à 3 jours basées sur un modèle XGBoost.
Il est possible d'afficher les dernières pluies sur  jours, et un historique plus anciens des hauteurs d'eat et débits.

🚀 Fonctionnalités

- Interface utilisateur intuitive
- Visualisation interactive des données
- Traitement automatisé des informations
- Exécution depuis l'invite de commande et affichage dans le navigateur
- Développée entièrement avec Python et Streamlit

📂 Structure de la branche Bis (c'est le chantier)
.
├── Readme.md          # documentation partielle
├── backup.py          # Backup - Dashboard
├── app_sup.py         # Application principale - Dashboard    
````
Sans oublier la branche main, ici c'est Bis

 🛠️ Prérequis mini

* Python 3.10 ou supérieur
* pip
* bibliothèques

 📥 Installation

Clonez le dépôt :

```bash
git clone https://github.com/votre-utilisateur/votre-projet.git
cd votre-projet
```

 ▶️ Exécution

Lancez l'application avec :

```bash
py -m streamlit run {nom_app}.py
```
ou
```bash
python -m streamlit run {nom_app}.py
```
Par défaut, l'application sera disponible à l'adresse :
```
http://localhost:8501
```

📚 Bibliothèques requises (13) : 
* datetime 
* folium
* matplotlib
* numpy 
* pandas 
* plotly
* pyproj
* pytz
* requests
* seaborn
* streamlit 
* streamlit_folium 
* xgboost 

 🤝 Contribution

Moi ! et beaucoup de monde (j'ai pas tous les noms en tête)

 📄 Licence libre
