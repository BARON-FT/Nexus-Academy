import os
from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv # type: ignore

# Charger les variables d'environnement
load_dotenv()

# Initialiser Flask et Supabase
app = Flask(__name__, template_folder='templates', static_folder='static')
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- API pour enregistrer une nouvelle inscription ---
@app.route('/api/register', methods=['POST'])
def create_inscription():
    try:
        data = request.get_json()

        # Validation simple
        if not data or not data.get('nom') or not data.get('prenom') or not data.get('whatsapp'):
            return jsonify({"error": "Données manquantes"}), 400

        # Préparation des données pour Supabase
        inscription_data = {
            'nom': data.get('nom'),
            'prenom': data.get('prenom'),
            'whatsapp': data.get('whatsapp'),
            'id_be': data.get('id_be') # Sera null si non fourni
        }

        # Insertion dans la base de données
        response = supabase.table('inscriptions').insert(inscription_data).execute()

        # Vérifier si l'insertion a réussi
        if response.data:
            return jsonify({"success": True, "data": response.data}), 201
        else:
            return jsonify({"error": "Erreur lors de l'insertion", "details": response.error}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API pour récupérer tous les inscrits (pour le dashboard) ---
@app.route('/api/inscrits', methods=['GET'])
def get_inscrits():
    try:
        response = supabase.table('inscriptions').select("*").order('created_at', desc=True).execute()
        if response.data:
            return jsonify(response.data), 200
        else:
            return jsonify({"error": "Aucun inscrit trouvé", "details": response.error}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# --- Servir la page d'accueil (tunnel) ---
@app.route('/')
def index():
    return render_template('index.html') # Utilise render_template

# --- Servir la page admin ---
@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html') # Utilise render_template

if __name__ == '__main__':
    app.run(debug=True, port=5001)