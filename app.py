import os
import datetime
from flask import Flask, render_template, request, url_for, abort, jsonify
from dotenv import load_dotenv  # type: ignore

# Charger les variables d'environnement du fichier .env
load_dotenv()

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Configuration Supabase
# Le code fonctionnera même si les clés ne sont pas définies (utile pour le dev local)
supabase = None
ADMIN_CLE = os.getenv("ADMIN_CLE")

try:
    from supabase import create_client, Client # type: ignore
    SB_URL = os.getenv("SUPABASE_URL")
    SB_KEY = os.getenv("SUPABASE_KEY")
    if SB_URL and SB_KEY:
        supabase = create_client(SB_URL, SB_KEY)
except ImportError:
    print("AVERTISSEMENT: La librairie 'supabase' n'est pas installée. L'upload des preuves sera désactivé.")
except Exception as e:
    print(f"AVERTISSEMENT: Erreur de connexion à Supabase: {e}")


@app.route("/")
def index():
    """Affiche la page d'accueil."""
    return render_template("index.html")


@app.route("/formation", methods=["GET", "POST"])
def formation():
    """Gère l'affichage du formulaire et la soumission des inscriptions."""
    if request.method == "POST":
        try:
            nom = request.form.get("name", "").strip()
            whatsapp = request.form.get("whatsapp", "").strip()
            id_nexus = request.form.get("baron-id", "").strip()
            preuve_fichier = request.files.get("proof-upload")

            if not all([nom, whatsapp, preuve_fichier]):
                return jsonify({"success": False, "error": "Tous les champs sont requis."}), 400

            # Gérer l'upload de la preuve
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            nom_fichier = f"preuve_{nom.replace(' ', '_')}_{timestamp}.{preuve_fichier.filename.split('.')[-1]}"
            
            if supabase:
                # Upload vers Supabase Storage
                supabase.storage.from_('preuves-paiement').upload(
                    nom_fichier,
                    preuve_fichier.read(),
                    {"content-type": preuve_fichier.mimetype}
                )
                preuve_url = supabase.storage.from_('preuves-paiement').get_public_url(nom_fichier)

                # Insérer les données dans la table
                supabase.table('inscriptions_nexus').insert({
                    'nom': nom,
                    'whatsapp': whatsapp,
                    'id_nexus': id_nexus or None,
                    'preuve_url': preuve_url,
                    'statut_paiement': 'en attente'
                }).execute()
            else:
                # Fallback si Supabase n'est pas configuré
                print("AVERTISSEMENT: Supabase non configuré. L'inscription n'a pas été sauvegardée en base de données.")

            return jsonify({"success": True, "message": "Félicitations ! Votre inscription a été enregistrée."})

        except Exception as e:
            print(f"ERREUR SERVEUR: {e}")
            return jsonify({"success": False, "error": f"Une erreur technique est survenue."}), 500

    return render_template("formation.html")


@app.route("/admin")
def admin():
    """Affiche le panneau d'administration avec la liste des inscrits."""
    cle_fournie = request.args.get('cle')
    if ADMIN_CLE and cle_fournie != ADMIN_CLE:
        abort(403, description="Accès non autorisé.")

    inscriptions = []
    if supabase:
        try:
            response = supabase.table('inscriptions_nexus').select('*').order('timestamp', desc=True).execute()
            inscriptions = response.data
        except Exception as e:
            print(f"Erreur de récupération des données admin: {e}")
            # On peut afficher une erreur sur la page admin si nécessaire
    
    return render_template("admin.html", inscriptions=inscriptions)


if __name__ == '__main__':
    # Ne s'exécute que lorsque vous lancez `python app.py`
    app.run(host='0.0.0.0', port=5000, debug=True)