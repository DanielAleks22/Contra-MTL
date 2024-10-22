from datetime import datetime
import sqlite3

from flask import Flask, jsonify, render_template
from flask import request, current_app, g, Response
from apscheduler.schedulers.background import BackgroundScheduler
import xml.etree.ElementTree as ET
import csv
import io

from .database import Database

app = Flask(__name__)

has_initialized = False


def get_db():
    if not hasattr(g, '_database'):
        g._database = Database()
        if not current_app.config.get('DB_INITIALIZED', False):
            g._database.get_violations()
            g._database.init_db_with_backup()
            current_app.config['DB_INITIALIZED'] = True
    return g._database


def scheduled_task():
    db = get_db()
    db.download_and_insert_data()


@app.before_request
def before_request():
    global has_initialized
    if not has_initialized:
        scheduler = BackgroundScheduler()
        scheduler.add_job(scheduled_task, 'cron', hour=0)
        scheduler.start()
        has_initialized = True


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.disconnect()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    """
    Route de la page d'accueil qui affiche les
    restaurants et les violations.Récupère la liste des restaurants
    et des contraventions en cours pour les afficher sur la page d'accueil.
    """
    db = get_db()
    restaurants = db.get_all_restaurants()
    violations = db.get_violations()
    return render_template(
        'home.html',
        violations=violations,
        restaurants=restaurants
    )


@app.route('/search')
def search_results():
    """
    Route de recherche qui affiche les résultats de recherche
    pour une requête spécifique.
    Les paramètres de la requête sont utilisés pour rechercher
    dans la base de données les violations correspondantes.
    Gère les erreurs opérationnelles SQLite et enregistre
    les erreurs rencontrées.
    """
    search_query = request.args.get('search', '')
    db = get_db()
    try:
        violations = db.search_violations(search_query)
    except sqlite3.OperationalError as e:
        current_app.logger.error(e)
        violations = []
    return render_template(
        'search_results.html',
        violations=violations,
        search_query=search_query
    )


@app.route('/contrevenants')
def contrevenants():
    """
    Route qui fournit les informations sur les contrevenants entre
    deux dates spécifiées dans les paramètres de requête.
    Si les dates sont fournies et valides, la fonction récupère et
    renvoie les données correspondantes.
    En cas d'erreur, retourne une réponse JSON indiquant l'erreur.
    """
    du = request.args.get('du')
    au = request.args.get('au')
    db = get_db()
    try:
        du_db = datetime.strptime(du, '%Y-%m-%d').strftime('%Y%m%d')
        au_db = datetime.strptime(au, '%Y-%m-%d').strftime('%Y%m%d')
        violations = db.get_violations_by_date(du_db, au_db)
        violations_dict = [
            {
                "etablissement": etablissement,
                "nombre_contraventions": nombre_contraventions
            }
            for etablissement, nombre_contraventions
            in violations
        ]
        return jsonify(violations_dict)
    except sqlite3.Error as e:
        current_app.logger.error(e)
        return jsonify({
            "error": "An error occurred while fetching the data"
        }), 500


@app.route('/doc')
def documentation():
    """
    Route pour afficher la documentation de l'API.
    """
    return render_template('doc.html')


@app.route('/violations_by_name')
def violations_by_name():
    """
    Route qui retourne les violations pour un établissement
    spécifique donné par le nom. Les violations sont recherchées par le
    nom exact de l'établissement passé en paramètre de requête.
    En cas d'erreur de base de données, retourne un message d'erreur JSON.
    """
    establishment_name = request.args.get('name')
    db = get_db()
    try:
        violations = db.search_violations_by_exact_name(establishment_name)
        violations_dict = [
            {"etablissement": etablissement, "description": description}
            for etablissement, description in violations]
        return jsonify(violations_dict)
    except sqlite3.Error as e:
        current_app.logger.error(e)
        return jsonify({
            "error": "An error occurred while fetching the data"
        }), 500


@app.route('/establishments/violations')
def establishments_violations():
    """
    Route qui fournit le nombre de contraventions par établissement.
    En cas de succès, retourne une réponse JSON avec les données.
    En cas d'erreur, retourne une réponse JSON avec un message d'erreur.
    """
    db = get_db()
    try:
        results = db.get_establishments_with_violation_counts()
        establishments = [
            {"etablissement": etablissement, "nombre_contraventions": count}
            for etablissement, count in results
        ]
        return jsonify(establishments)
    except sqlite3.Error as e:
        current_app.logger.error(e)
        return jsonify({
            "error": "An error occurred while fetching the data"
        }), 500


@app.route('/establishments/violations/xml')
def establishments_violations_xml():
    """
    Route qui retourne les données des contraventions
    par établissement au format XML.
    En cas d'erreur, retourne une réponse XML indiquant l'erreur.
    """
    db = get_db()
    try:
        results = db.get_establishments_with_violation_counts()
        establishments = [
            {"etablissement": etablissement, "nombre_contraventions": count}
            for etablissement, count in results
        ]

        root = ET.Element("establishments")
        for establishment in establishments:
            est_element = ET.SubElement(root, "establishment")
            ET.SubElement(
                est_element, "name"
            ).text = establishment["etablissement"]
            ET.SubElement(
                est_element, "violationsCount"
            ).text = str(establishment["nombre_contraventions"])

        xmlstr = ET.tostring(root, encoding='utf8', method='xml')

        return Response(xmlstr, mimetype='text/xml')
    except sqlite3.Error as e:
        current_app.logger.error(e)
        return Response(
            '<error>An error occurred fetching the data</error>',
            status=500, mimetype='text/xml'
        )


@app.route('/establishments/violations/csv')
def establishments_violations_csv():
    """
    Route qui permet de télécharger un fichier CSV contenant
    le nombre de contraventions par établissement.
    En cas de succès, retourne un fichier CSV. En cas d'erreur,
    retourne un texte indiquant l'erreur.
    """
    db = get_db()
    try:
        results = db.get_establishments_with_violation_counts()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['etablissement', 'nombre_contraventions'])
        for etablissement, count in results:
            writer.writerow([etablissement, count])

        output.seek(0)
        return Response(output, mimetype='text/csv',
                        headers={
                            "Content-Disposition":
                            "attachment;filename=establishments_violations.csv"
                        })
    except sqlite3.Error as e:
        current_app.logger.error(e)
        return Response(
            'An error occurred fetching the data',
            status=500, mimetype='text/plain'
        )
