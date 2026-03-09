# Application Streamlit - Gestion des Menus et Satisfaction

Application web pour gérer les menus de la semaine avec évaluation de la qualité et quantité des plats livrés.

## Fonctionnalités

- 📅 Planification des menus par jour de la semaine
- 🍴 Sélection des plats depuis le fichier Excel (FS.xlsx)
- 😊 Évaluation avec emojis (0-3) pour quantité et qualité
- 📊 Graphiques de moyennes par plat
- 📈 Évolution dans le temps par site et semaine
- 💾 Sauvegarde automatique des données

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app_streamlit.py
```

L'application sera accessible sur `http://localhost:8501`

## Utilisation

1. **Sélection du site et de la semaine** dans la barre latérale
2. **Planification** : Pour chaque jour, sélectionnez un plat et cliquez sur "➕ Ajouter"
3. **Évaluation** : Cliquez sur les emojis pour noter la quantité et la qualité (0-3)
4. **Visualisation** : Consultez les graphiques dans les onglets "Graphiques" et "Évolution"
5. **Sauvegarde** : Cliquez sur "💾 Sauvegarder" pour enregistrer vos données

## Structure des données

Les données sont sauvegardées dans `menu_data.json` avec la structure suivante :
- Site (1-3)
- Semaine (1-5)
- Jour (Lundi-Vendredi)
- Plat
- Quantité (0-3)
- Qualité (0-3)

## Emojis et notes

- 😢 (0) = Très mauvais / Non satisfait
- 😞 (1) = Mauvais / Peu satisfait
- 😐 (2) = Correct / Satisfait
- 😊 (3) = Excellent / Très satisfait


