import os
import io
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import openpyxl

# Charger les variables d'environnement
load_dotenv()

# --- MODIFICATION : Connexion à la base de données Neon ---
app = Flask(__name__, template_folder='templates', static_folder='static')
DATABASE_URL = os.environ.get("DATABASE_URL") # L'URL de connexion Neon
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL n'est pas configurée !")
engine = create_engine(DATABASE_URL)


# --- MODIFICATION : API pour enregistrer une nouvelle inscription avec cohorte ---
@app.route('/api/register', methods=['POST'])
def create_inscription():
    try:
        data = request.get_json()
        required_fields = ['nom', 'prenom', 'whatsapp', 'cohorte']
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Données manquantes"}), 400

        # Préparation des données
        inscription_data = {
            'nom': data.get('nom'),
            'prenom': data.get('prenom'),
            'whatsapp': data.get('whatsapp'),
            'id_be': data.get('id_be'),
            'cohorte': data.get('cohorte')
        }

        # Insertion avec SQLAlchemy pour se protéger des injections SQL
        with engine.connect() as connection:
            query = text("""
                INSERT INTO inscriptions (nom, prenom, whatsapp, id_be, cohorte)
                VALUES (:nom, :prenom, :whatsapp, :id_be, :cohorte)
            """)
            connection.execute(query, inscription_data)
            connection.commit() # Important: valider la transaction

        return jsonify({"success": True}), 201

    except Exception as e:
        print(f"Erreur: {e}") # Pour le débogage sur le serveur
        return jsonify({"error": "Erreur interne du serveur"}), 500


# --- MODIFICATION : API pour récupérer les inscrits par cohorte ---
@app.route('/api/inscrits', methods=['GET'])
def get_inscrits():
    cohorte = request.args.get('cohorte')
    if not cohorte:
        return jsonify({"error": "Le paramètre 'cohorte' est requis"}), 400
    
    with engine.connect() as connection:
        query = text("SELECT * FROM inscriptions WHERE cohorte = :cohorte ORDER BY created_at DESC")
        result = connection.execute(query, {'cohorte': cohorte})
        inscrits = [dict(row._mapping) for row in result]
        return jsonify(inscrits), 200

# --- NOUVEAUTÉ : API pour lister les cohortes existantes ---
@app.route('/api/cohortes', methods=['GET'])
def get_cohortes():
    with engine.connect() as connection:
        query = text("SELECT DISTINCT cohorte FROM inscriptions ORDER BY cohorte DESC")
        result = connection.execute(query)
        cohortes = [row[0] for row in result]
        return jsonify(cohortes), 200

# --- NOUVEAUTÉ : API pour exporter en Excel ---
@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    cohorte = request.args.get('cohorte')
    if not cohorte:
        return jsonify({"error": "Le paramètre 'cohorte' est requis pour l'export"}), 400

    # 1. Récupérer les données
    with engine.connect() as connection:
        query = text("SELECT * FROM inscriptions WHERE cohorte = :cohorte ORDER BY created_at ASC")
        result = connection.execute(query, {'cohorte': cohorte})
        inscrits = [dict(row._mapping) for row in result]

    # 2. Créer le fichier Excel en mémoire
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Inscriptions {cohorte}"

    # En-têtes
    headers = ["Date d'inscription", "Nom", "Prénom", "Numéro WhatsApp", "ID Baron Enterprise"]
    ws.append(headers)

    # Données
    for inscrit in inscrits:
        row = [
            inscrit['created_at'].strftime("%d/%m/%Y %H:%M:%S"),
            inscrit['nom'],
            inscrit['prenom'],
            inscrit['whatsapp'],
            inscrit['id_be'] or 'Non'
        ]
        ws.append(row)

    # 3. Sauvegarder le fichier dans un buffer mémoire
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'inscriptions_{cohorte.replace(" ", "_")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# --- Servir les pages HTML (inchangé) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

if __name__ == '__main__':

    app.run(debug=True, port=5001)
