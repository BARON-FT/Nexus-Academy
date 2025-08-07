# app.py - VERSION FINALE ET COMPLÈTE

import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv # type: ignore
import datetime

load_dotenv()

app = Flask(__name__)

# --- CONNEXION SUPABASE ---
try:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    ADMIN_CLE = os.environ.get("ADMIN_CLE")
except Exception as e:
    # Gérer le cas où les variables d'environnement ne sont pas définies
    print(f"Erreur de configuration : {e}")
    supabase = None
    ADMIN_CLE = None

# --- ROUTE PRINCIPALE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- ROUTE DE LA FORMATION (GET & POST) ---
@app.route('/formation', methods=['GET', 'POST'])
def formation():
    if request.method == 'POST':
        if not supabase:
            return render_template('formation.html', error="Erreur de configuration du serveur. Veuillez contacter l'administrateur.")

        try:
            nom = request.form.get('name')
            whatsapp = request.form.get('whatsapp')
            id_nexus = request.form.get('baron-id', None)
            preuve_fichier = request.files.get('proof-upload')

            if not all([nom, whatsapp, preuve_fichier]):
                return render_template('formation.html', error="Tous les champs sont requis.")

            # Gérer l'upload de la preuve
            timestamp_unique = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            nom_fichier = f"preuve_{nom.replace(' ', '_')}_{timestamp_unique}.{preuve_fichier.filename.split('.')[-1]}"
            
            # Upload vers Supabase Storage
            supabase.storage.from_('preuves-paiement').upload(nom_fichier, preuve_fichier.read(), {"content-type": preuve_fichier.content_type})
            
            # Obtenir l'URL publique
            preuve_url = supabase.storage.from_('preuves-paiement').get_public_url(nom_fichier)

            # Insérer les données dans la table
            data, count = supabase.table('inscriptions_nexus').insert({
                'nom': nom,
                'whatsapp': whatsapp,
                'id_nexus': id_nexus,
                'preuve_url': preuve_url,
                'statut_paiement': 'en attente'
            }).execute()

            return render_template('formation.html', message="Félicitations ! Votre inscription a été enregistrée avec succès.")

        except Exception as e:
            print(f"ERREUR LORS DE LA SOUMISSION : {e}")
            return render_template('formation.html', error=f"Une erreur technique est survenue : {e}")

    # Si la méthode est GET, afficher simplement le formulaire
    return render_template('formation.html')

# --- ROUTE DE L'ADMINISTRATION ---
@app.route('/admin')
def admin():
    cle_fournie = request.args.get('cle')
    if not ADMIN_CLE or cle_fournie != ADMIN_CLE:
        return "Accès non autorisé.", 403

    if not supabase:
        return "Erreur de configuration du serveur.", 500

    try:
        # Récupérer les inscriptions, triées par date (la plus récente en premier)
        data, count = supabase.table('inscriptions_nexus').select('*').order('timestamp', desc=True).execute()
        inscriptions = data[1] if data and len(data) > 1 else []
        return render_template('admin.html', inscriptions=inscriptions)
    except Exception as e:
        return f"Erreur lors de la récupération des données : {e}", 500

# Cette partie n'est exécutée que localement, pas sur Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)