# app.py

import os
import time
from flask import Flask, request, render_template, redirect, url_for, abort
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv() # Charge les variables d'environnement du fichier .env

app = Flask(__name__)

# --- Configuration de Supabase ---
# Ces variables doivent être dans votre fichier .env ou directement sur Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_CLE = os.environ.get("ADMIN_CLE", "plusULTRA2k1@") # Mettez une clé complexe

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_KEY sont requises.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nom du bucket de stockage sur Supabase
BUCKET_NAME = "preuves-paiement"

@app.route('/')
def home():
    # Redirige vers la page d'accueil principale
    return render_template('index.html')

@app.route('/formation', methods=['GET', 'POST'])
def formation():
    if request.method == 'POST':
        try:
            # 1. Récupérer les données du formulaire
            nom = request.form.get('name')
            whatsapp = request.form.get('whatsapp')
            is_subscriber = request.form.get('is_subscriber')
            id_nexus = request.form.get('baron-id', '') # Champ facultatif

            # 2. Gérer l'upload de la preuve de paiement
            proof_file = request.files.get('proof-upload')
            filename_preuve = None

            if proof_file and proof_file.filename != '':
                # Créer un nom de fichier unique pour éviter les conflits
                extension = proof_file.filename.rsplit('.', 1)[1].lower()
                filename_preuve = f"preuve_{nom.replace(' ', '_')}_{int(time.time())}.{extension}"
                
                # Uploader le fichier vers le bucket Supabase
                supabase.storage.from_(BUCKET_NAME).upload(
                    file=proof_file.read(),
                    path=filename_preuve,
                    file_options={"content-type": proof_file.content_type}
                )
            else:
                # Si aucune preuve n'est fournie (logique de validation côté client a échoué)
                return render_template('formation.html', error="La preuve de paiement est obligatoire.")

            # 3. Insérer les données dans la table Supabase
            data_to_insert = {
                "nom": nom,
                "whatsapp": whatsapp,
                "id_nexus": id_nexus if id_nexus else None,
                "filename_preuve": filename_preuve
            }
            
            data, count = supabase.table('inscriptions_nexus').insert(data_to_insert).execute()

            # 4. Afficher le message de succès
            return render_template('formation.html', message="Félicitations ! Votre inscription a été enregistrée avec succès.")

        except Exception as e:
            print(f"Une erreur est survenue : {e}")
            return render_template('formation.html', error=f"Une erreur technique est survenue. Veuillez réessayer. Erreur: {e}")

    return render_template('formation.html')

@app.route('/admin')
def admin():
    # Authentification simple par clé dans l'URL
    cle_fournie = request.args.get('cle')
    if cle_fournie != ADMIN_CLE:
        abort(403) # Accès interdit

    try:
        # Récupérer toutes les inscriptions depuis Supabase, triées par date
        response = supabase.table('inscriptions_nexus').select("*").order('timestamp', desc=True).execute()
        inscriptions = response.data
        
        # Construire l'URL publique pour les preuves
        for item in inscriptions:
            if item.get('filename_preuve'):
                public_url_response = supabase.storage.from_(BUCKET_NAME).get_public_url(item['filename_preuve'])
                item['preuve_url'] = public_url_response
            else:
                item['preuve_url'] = None

        return render_template('admin.html', inscriptions=inscriptions)
    except Exception as e:
        print(f"Erreur lors de la récupération des données admin : {e}")
        return "<h1>Erreur de connexion à la base de données.</h1>"

if __name__ == '__main__':

    app.run(debug=True)
