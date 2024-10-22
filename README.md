# Contra-MTL

## Description
Le projet consiste à récupérer un ensemble de données provenant de la ville de Montréal et d'offrir des
services à partir de ces données. Il s'agit de données ouvertes à propos d'établissements ayant reçu des
constats d'infraction lors d'inspections alimentaires. 
Ce projet, réalisé dans le cadre du cours de programmation web avancée (INF5190), utilise une combinaison de 
technologies Flask, Jinja, et un peu de JavaScript pour enrichir l'interaction client-serveur.

## Auteur
Daniel Aleksandrov 

## Fonctionnement
Pour exécuter ce projet, suivez ces étapes :

1. **Prérequis :**  
   - Assurez-vous d'avoir Python 3 et pip installés sur votre système.

2. **Installation :**
   - Installez les dépendances nécessaires en exécutant :
     ```
     pip install -r requirements.txt
     ```

3. **Démarrage de l'application :**
   - Utilisez le fichier `Makefile` pour démarrer facilement l'application en exécutant :
     ```
     make run
     ```

## Contenu du projet

- **/db :** Dossier contenant la base de données SQLite et les scripts SQL.
  - `db.db` : Le fichier de la base de données SQLite.
  - `db.sql` : Script SQL pour la création de la structure de la base de données.

- **/static :** Dossier pour les fichiers statiques tels que les feuilles de style CSS et les scripts JavaScript.
  - `script.js` : Script JavaScript pour dynamiser les pages web.

- **/templates :** Dossier contenant les templates Jinja2 utilisés pour le rendu des pages HTML.

- **/__init__.py :** Fichier qui transforme le dossier en un package Python.

- **/config.yaml :** Fichier de configuration pour l'application Flask.

- **/database.py :** Module Python gérant les interactions avec la base de données.

- **/doc.raml :** Documentation RAML pour l'API de l'application.

- **/index.py :** Fichier principal de l'application Flask contenant les routes et la logique métier.

- **/Makefile :** Fichier utilisé pour automatiser des commandes comme le démarrage de l'application.

- **/Procfile :** Fichier utilisé pour définir les commandes qui doivent être exécutées par les applications sur la plateforme Heroku.



## Dépendances
- **Flask :** Un micro-framework pour le développement d'applications web en Python.
- **APScheduler :** Une bibliothèque Python qui permet de planifier des tâches.
- **requests et requests_oauthlib :** Pour intégrer des fonctionnalités liées aux requêtes HTTP et à l'authentification OAuth.


## Références
Les concepts et techniques utilisés dans ce projet sont principalement basés sur la documentation officielle de Flask.
