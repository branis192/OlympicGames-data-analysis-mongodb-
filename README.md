# 🏅 Olympic & World Athletics Analytics (MongoDB)

## 📌 Présentation du Projet
Ce projet consiste en la création d'une plateforme analytique haute performance pour le traitement et l'analyse des données des **Jeux Olympiques** et des **Championnats du Monde d'Athlétisme**. L'objectif principal est de réconcilier des sources de données hétérogènes (médailles textuelles pour les JO vs positions numériques pour les Mondiaux) au sein d'une base NoSQL **MongoDB**. Le système permet de générer des statistiques avancées, de gérer les ex-aequo historiques et d'alimenter un dashboard interactif via un backend Java.

## 🛠️ Stack Technique
* **Base de données :** MongoDB Server 8.0+ (Architecture NoSQL)
* **Langage de requête :** MongoDB Aggregation Framework (MQL)
* **Backend :** Java (Driver MongoDB Synchrone)
* **Data Engineering :** Bash (scripts `sed` pour le nettoyage), `mongoimport`
* **Documentation :** LaTeX

## 📂 Architecture de la Base de Données
La base `athle_db` est structurée autour de **6 collections** stratégiques conçues pour optimiser les performances en lecture (Query-First Design) :

1. **`results` (JO) :** Performances olympiques détaillées (Année, Athlète, Événement, Médaille, Pays).
2. **`world_results` :** Résultats historiques des Championnats du Monde (Position, Marque chronométrique).
3. **`athletes` :** Référentiel biographique maître (Sexe, Taille, Poids, Pays d'origine, Date de naissance).
4. **`events` :** Nomenclature technique des épreuves (Sport, Genre, Année de début olympique).
5. **`editions` :** Index chronologique des compétitions (Ville hôte, Pays organisateur, Nombre d'épreuves).
6. **`championships_index` :** Table de mapping technique liant les noms des meetings mondiaux aux années civiles.



## 🚀 Pipelines d'Agrégation Avancés
Le projet implémente 10 requêtes analytiques complexes (Q1 à Q10). Ces pipelines exploitent la puissance native de MongoDB pour transformer des milliers de documents en informations stratégiques :

* **Unification des podiums :** Cumul des records JO et Mondiaux en un seul flux de données via `$unionWith`.
* **Gestion des ex-aequo :** Algorithme de détection des records par discipline avec logique de filtrage pour les athlètes à égalité de titres (`$group` + `$filter`).
* **Analyse de parité :** Étude comparative de la croissance de la participation féminine avant et après l'an 2000.
* **Évolution du programme :** Calcul dynamique du nombre de disciplines uniques par édition sur plus d'un siècle d'histoire.

### Exemple : Identification du recordman par discipline (avec gestion des égalités)
```javascript
db.results.aggregate([
  { $match: { medal: { $in: ["Gold", "Silver", "Bronze"] } } },
  { $group: { _id: { d: "$event", n: "$athlete" }, nb: { $sum: 1 } } },
  { $sort: { "nb": -1 } },
  { $group: { 
      _id: "$_id.d", 
      max_medailles: { $first: "$nb" }, 
      candidats: { $push: { nom: "$_id.n", total: "$nb" } } 
  }},
  { $project: {
      _id: 0,
      discipline: "$_id",
      record: "$max_medailles",
      athletes: { $filter: { 
          input: "$candidats", as: "a", cond: { $eq: ["$$a.total", "$max_medailles"] } 
      }}
  }}
])

## Nettoyage et Ingestion des Données

Un pipeline de préparation de données a été mis en place pour corriger les inconsistances JSON (notamment les valeurs NaN invalides issues d'exports de dataframes) :

* **Nettoyage automatisé :** Utilisation de sed pour transformer les tokens invalides en null : sed -i 's/NaN/null/g' data.json

* **Importation massive :** Utilisation de mongoimport avec les flags --jsonArray et --drop pour garantir une base propre et reproductible.

* **Indexation :** Création d'index sur les champs athlete_id, event et year pour garantir des temps de réponse inférieurs à 100ms.
