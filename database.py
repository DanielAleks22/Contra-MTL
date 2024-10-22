import sqlite3
import requests
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml
import tweepy
import json
from requests_oauthlib import OAuth1


def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)


config = load_config()


class Database:
    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('db/db.db')
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def backup_current_violations(self):
        """
        Sauvegarde les contraventions actuelles dans un fichier CSV.
        """

        current_violations = self.get_violations()
        with open(
            'violations_backup.csv', 'w', newline='', encoding='utf-8'
        ) as file:
            fieldnames = [
                'id_poursuite', 'business_id', 'date', 'description',
                'adresse', 'date_jugement', 'etablissement', 'montant',
                'proprietaire', 'ville', 'statut', 'date_statut', 'categorie'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for violation in current_violations:
                writer.writerow(
                    {
                        fieldname: violation[i] for i,
                        fieldname in enumerate(fieldnames)
                    }
                )

    def init_db_with_backup(self):
        """
        Initialise la base de données avec une sauvegarde
        après avoir sauvegardé les contraventions actuelles.
        """

        if self.connection is not None:
            self.backup_current_violations()
        self.init_db()

    def compare_and_extract_new_violations(self):
        """
        Compare les contraventions actuelles avec
        une sauvegarde précédente et extrait les nouvelles contraventions.

        Retourne:
            list: Une liste des nouvelles contraventions
            non encore sauvegardées.
        """

        with open('violations_backup.csv', 'r', encoding='utf-8') as file:
            dr = csv.DictReader(file)
            saved_violations = {row['id_poursuite']: row for row in dr}

        current_violations = {row[0]: row for row in self.get_violations()}

        new_violations_ids = set(
            current_violations.keys()
        ) - set(saved_violations.keys())
        new_violations = [
            current_violations[id_poursuite]
            for id_poursuite in new_violations_ids
        ]
        unique_new_violations = list(
            {
                violation[0]: violation
                for violation in new_violations
            }.values())

        print(unique_new_violations)
        return unique_new_violations

    def init_db(self):
        cursor = self.get_connection().cursor()
        with open('db/db.sql', 'r') as queryfile:
            cursor.executescript(queryfile.read())
        self.download_and_insert_data()

    def download_csv(self, url):
        """
        Télécharge un fichier CSV depuis une URL spécifiée.

        Paramètres:
            url (str): L'URL du fichier CSV à télécharger.
        """

        response = requests.get(url)
        if response.status_code == 200:
            with open('violations.csv', 'wb') as file:
                file.write(response.content)
        else:
            error_message = (
                f"Erreur de téléchargement du fichier CSV : "
                f"status {response.status_code}"
            )
            raise Exception(error_message)

    def download_and_insert_data(self):
        """
        Télécharge les données de contraventions depuis
        une URL spécifiée, les insère dans la base de données,
        et notifie des nouvelles contraventions par e-mail et tweet.
        """

        url = (
            'https://data.montreal.ca/dataset/05a9e718-6810-4e73-8bb9-'
            '5955efeb91a0/resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/'
            'download/violations.csv'
        )

        self.download_csv(url)
        self.insert_data_into_db('violations.csv')

        new_violations = self.compare_and_extract_new_violations()
        if new_violations:
            print("Sending email with new violations...")
            self.send_email(new_violations)
            print("Tweeting new violations...")
            self.tweet_new_violations(new_violations)

    def insert_data_into_db(self, csv_path):
        """
        Insère les données de contraventions depuis un
        fichier CSV spécifié dans la base de données.

        Paramètres:
            csv_path (str): Le chemin d'accès au fichier CSV
            contenant les données de contraventions.
        """

        try:
            cursor = self.get_connection().cursor()
            with open(csv_path, 'r', encoding='utf-8') as file:
                dr = csv.DictReader(file)
                #
                # important dexecuter make run en 1er lieu
                # fermer lapp flask avec ctrl+c
                # ensuite decommenter la ligne next(...)
                # faite une sauvegarde de la modif
                # reouvrir lapp flask avec make run
                # la fermer de nouveau avec ctrl+c
                # recomment la ligne next(...)
                # et faire un dernier make run
                # la premiere ligne du db sera envoyer
                # en tant que email et sera tweeter
                # assurer vous que si vous faites se test
                # plus quune fois de supprimer le dernier
                # tweet car tweeter ne permer pas de tweet
                # des message duped
                #
                # next(dr, None)
                #
                to_db = [
                    (
                        i['id_poursuite'], i['business_id'], i['date'],
                        i['description'], i['adresse'], i['date_jugement'],
                        i['etablissement'], i['montant'], i['proprietaire'],
                        i['ville'], i['statut'],
                        i['date_statut'], i['categorie']
                    ) for i in dr
                ]

            if not to_db:
                return

            cursor.executemany(
                """
                INSERT INTO violations (
                    id_poursuite, business_id, date,
                    description, adresse, date_jugement,
                    etablissement, montant, proprietaire,
                    ville, statut, date_statut, categorie
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, to_db
            )
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"An error occurred: {e.args[0]}")

    def get_violations(self):
        """
        Récupère toutes les contraventions de la base de données.

        Retourne:
            list: Une liste de toutes les contraventions
            dans la base de données.
        """

        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM violations")
        violations = cursor.fetchall()
        return violations

    def search_violations(self, search_query):
        """
        Recherche des contraventions basées sur une requête
        de recherche.

        Paramètres:
            search_query (str): La requête de recherche
            pour filtrer les contraventions.

        Retourne:
            list: Une liste de contraventions correspondant
            à la requête de recherche.
        """

        cursor = self.get_connection().cursor()
        query = """
        SELECT * FROM violations
        WHERE etablissement LIKE ?
        OR proprietaire LIKE ?
        OR adresse LIKE ?;
        """
        cursor.execute(query, ('%' + search_query + '%',) * 3)
        return cursor.fetchall()

    def get_violations_by_date(self, start_date, end_date):
        """
        Récupère les contraventions entre deux dates spécifiées.

        Paramètres:
            start_date (str): La date de début pour
            filtrer les contraventions.
            end_date (str): La date de fin pour
            filtrer les contraventions.

        Retourne:
            list: Une liste de contraventions entre
            les deux dates spécifiées.
        """

        cursor = self.get_connection().cursor()
        query = """
        SELECT etablissement, COUNT(*) as nombre_contraventions
        FROM violations
        WHERE date >= ? AND date <= ?
        GROUP BY etablissement;
        """
        cursor.execute(query, (start_date, end_date))
        return cursor.fetchall()

    def get_all_restaurants(self):
        """
        Récupère une liste de tous les établissements
        ayant des contraventions.

        Retourne:
            list: Une liste de tous les établissements
            uniques ayant des contraventions.
        """

        cursor = self.get_connection().cursor()
        cursor.execute("""
        SELECT DISTINCT etablissement FROM violations ORDER BY etablissement
        """)
        return cursor.fetchall()

    def search_violations_by_exact_name(self, establishment_name):
        """
        Recherche des contraventions pour un établissement
        spécifique par nom exact.

        Paramètres:
            establishment_name (str): Le nom exact de
            l'établissement à rechercher.

        Retourne:
            list: Une liste de contraventions pour
            l'établissement spécifié.
        """

        cursor = self.get_connection().cursor()
        query = """
        SELECT etablissement, description
        FROM violations
        WHERE etablissement = ?;
        """
        cursor.execute(query, (establishment_name,))
        return cursor.fetchall()

    def get_establishments_with_violation_counts(self):
        """
        Récupère une liste d'établissements avec
        le nombre de contraventions pour chacun.

        Retourne:
            list: Une liste d'établissements et leur
            nombre respectif de contraventions.
        """
        cursor = self.get_connection().cursor()
        query = """
        SELECT etablissement, COUNT(*) as count
        FROM violations
        GROUP BY etablissement
        ORDER BY count DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results

    def send_email(self, new_violations):
        """
        Envoie un e-mail à un destinataire configuré avec
        la liste des nouvelles contraventions.

        Parametres:
            new_violations (list): Une liste de nouvelles
            contraventions à notifier.
        """
        config = load_config()
        recipient_email = config['email']['recipient']

        msg = MIMEMultipart()
        msg['From'] = 'danieltemp1199@gmail.com'
        msg['To'] = recipient_email
        msg['Subject'] = "Nouvelles contraventions ajoutées"

        body = """
            Les nouvelles contraventions suivantes ont été ajoutées :\n\n
        """ + \
            "\n".join(str(violation) for violation in new_violations)
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('danieltemp1199@gmail.com', 'spoy lzlv skqr nuuv')

        text = msg.as_string()
        server.sendmail('danieltemp1199@gmail.com', recipient_email, text)
        print("Email has been sent!")
        server.quit()

    def tweet_new_violations(self, new_violations):
        """
        Publie des tweets pour chaque nouvelle
        contravention trouvée.

        Paramètres:
            new_violations (list): Une liste des nouvelles
            contraventions à tweeter.
        """

        api_key = config['twitter']['api_key']
        api_secret_key = config['twitter']['api_secret_key']
        access_token = config['twitter']['access_token']
        access_token_secret = config['twitter']['access_token_secret']

        for violation in new_violations:
            date = violation[2]
            description = violation[3]
            adresse = violation[4]
            etablissement = violation[6]

            tweet_text = f"""
                Nouvelle contravention {date} a {etablissement} ({adresse})
                """

            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            url = 'https://api.twitter.com/2/tweets'
            payload = {"text": tweet_text}
            auth = OAuth1(
                api_key, api_secret_key, access_token, access_token_secret
            )
            response = requests.post(url, json=payload, auth=auth)

            if response.status_code == 201:
                print("Successfully posted tweet:", tweet_text)
            else:
                print(
                    "Failed to post tweet:",
                    response.status_code, response.text
                )
