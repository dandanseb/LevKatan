import os
import jwt
import psycopg2
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import wraps

# --- Configuration de l'Application Flask ---
app = Flask(__name__)
CORS(app)  # Active CORS pour permettre la communication avec votre Frontend GitHub Pages

# ----------------------------------------------------
# 🔑 CONFIGURATION ET LECTURE DES SECRETS
# ----------------------------------------------------

# Charge les variables d'environnement à partir du fichier .env (pour le développement local).
# Sur Azure App Service, cette ligne est ignorée, car Azure injecte directement les variables.

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# 🔑 CONFIGURATION JWT
# CRITIQUE: Utilisez une clé SECRÈTE forte. Pour la production, utilisez os.getenv!
# Pour le test local, vous pouvez utiliser une chaîne temporaire.
# Pour la production Azure, ajoutez une variable d'environnement AZURE_JWT_SECRET
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre_cle_secrete_hyper_forte_par_defaut")
JWT_ALGORITHM = "HS256"

# ----------------------------------------------------
# 🧪 FONCTION DE CONNEXION À LA DB (UTILISÉE PAR LES ROUTES)
# ----------------------------------------------------

def get_db_connection():
    # Vérification critique des secrets avant de tenter la connexion
    if not all(DATABASE_URL):
        print(
            "❌ ERREUR FATALE: Une ou plusieurs variables de connexion à la base de données sont manquantes.")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        # Affiche une erreur détaillée pour le diagnostic (mot de passe incorrect, pare-feu, etc.)
        print("--------------------------------------------------")
        print(f"❌ ÉCHEC DE LA CONNEXION À LA BASE DE DONNÉES : {e}")
        print(
            "Vérifiez 1) Votre mot de passe Supabase et 2) Les règles de pare-feu/réseau.")
        print("--------------------------------------------------")
        return None


# ----------------------------------------------------
#  FONCTION DE VÉRIFICATION ET DE DÉMARRAGE DU SERVEUR
# ----------------------------------------------------

def check_db_and_run():
    # 1. Tente une connexion temporaire pour vérifier l'accès
    test_conn = get_db_connection()

    if test_conn is None:
        print(
            "\n🛑 DÉMARRAGE ANNULÉ : Connexion DB échouée. Serveur Flask non lancé.")
        return

    try:
        # 2. Si la connexion réussit, exécute une simple requête de test SQL
        cursor = test_conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        test_conn.close()  # Ferme la connexion de test

        print("--------------------------------------------------")
        print(
            "✅ SUCCÈS : Connexion à Supabase validée ! Serveur Flask démarré.")
        print("--------------------------------------------------")

        # 3. Lance l'API Flask (en mode production pour Azure App Service)
        # host='0.0.0.0' est nécessaire pour écouter toutes les interfaces sur Linux/Azure
        # Le port 5230 est utilisé uniquement pour les tests locaux si vous le lancez directement
        app.run(debug=True, port=5230, host='0.0.0.0')

    except Exception as e:
        print(f"\n🛑 ERREUR LORS DU TEST SQL OU DU DÉMARRAGE : {e}")
        if test_conn:
            test_conn.close()
        return


# ----------------------------------------------------
# --- API ENDPOINTS ---
# ----------------------------------------------------

@app.route('/api/register', methods=['POST'])
def register():
    """
    Endpoint d'inscription. Crée un nouvel utilisateur dans la table personnal_infos.
    """
    data = request.json
    full_name = data.get('fullName')
    username = data.get('username')
    phone = data.get('phone')
    email = data.get('email')
    passwd = data.get('password')

    if not all([full_name, username, phone, email, passwd]):
        return jsonify({"message": "Données manquantes"}), 400

    # Hacher le mot de passe
    password_bytes = passwd.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode(
        'utf-8')

    conn = get_db_connection()
    if conn is None:
        return jsonify({
                           "message": "Erreur serveur: Impossible de connecter à la DB"}), 500

    cur = conn.cursor()

    sql = """
        INSERT INTO personnal_infos (full_name, email, username, phone_number, passwd, role)
        VALUES (%s, %s, %s, %s, %s, 'user')
        RETURNING id;
    """

    try:
        cur.execute(sql, (full_name, email, username, phone, hashed_password))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify(
            {"message": "Registered successfully", "userId": user_id}), 200

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify(
            {"message": "Email ou Nom d'utilisateur déjà utilisé."}), 409

    except Exception as e:
        conn.rollback()
        print(f"Erreur d'enregistrement: {e}")
        return jsonify({
                           "message": "Erreur interne du serveur lors de l'enregistrement"}), 500

    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    """
    Endpoint de connexion. Vérifie les identifiants de l'utilisateur.
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Email ou mot de passe manquant"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({
                           "message": "Erreur serveur: Impossible de connecter à la DB"}), 500

    cur = conn.cursor()
    sql = "SELECT username, passwd, role FROM personnal_infos WHERE email = %s"

    try:
        cur.execute(sql, (email,))
        user = cur.fetchone()

        if user is None:
            return jsonify({"message": "Non autorisé"}), 401

        db_username, db_hashed_password, db_role = user

        # Vérification du mot de passe
        if bcrypt.checkpw(password.encode('utf-8'),
                          db_hashed_password.encode('utf-8')):
            # 1. Créer le contenu du jeton (le payload)
            payload = {
                'user_id': user[0],
                # Supposons que l'ID est la première colonne de la requête SELECT
                'username': db_username,
                'role': db_role,
                'exp': datetime.utcnow() + timedelta(hours=24)
                # Expiration dans 24 heures
            }

            # 2. Encoder le jeton
            token = jwt.encode(
                payload,
                JWT_SECRET_KEY,
                algorithm=JWT_ALGORITHM
            )

            # 3. Retourner le jeton (en plus du rôle)
            return jsonify({
                "message": "Login successful",
                "username": db_username,
                "role": db_role,
                "token": token  # <--- LE VRAI JETON SÉCURISÉ
            }), 200
        else:
            return jsonify({"message": "Non autorisé"}), 401

    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return jsonify({"message": "Erreur interne du serveur"}), 500

    finally:
        if cur: cur.close()
        if conn: conn.close()



def admin_required(f):
    """Décorateur pour exiger un jeton valide avec le rôle 'admin'."""

    @wraps(f)
    def decorated(*args, **kwargs):

        # ----------------------------------------------------
        # CORRECTION : IGNORER LA VÉRIFICATION POUR LE PRÉ-VOL (OPTIONS)
        # ----------------------------------------------------
        if request.method == 'OPTIONS':
            # Si c'est un pré-vol, laissons Flask-CORS gérer la réponse 200/OK
            return f(*args, **kwargs)

        # ----------------------------------------------------
        # Début de la vérification JWT pour GET, PUT, DELETE, etc.
        # ----------------------------------------------------
        token_header = request.headers.get('Authorization')

        if not token_header or not token_header.startswith('Bearer '):
            return jsonify({'message': 'Jeton manquant ou invalide.'}), 401

        token = token_header[7:]

        try:
            # 1. Décoder le jeton
            # ... (le reste de la logique de décodage JWT) ...
            data = jwt.decode(token, JWT_SECRET_KEY,
                              algorithms=[JWT_ALGORITHM])
            user_role = data.get('role')

            # 2. Vérification du Rôle
            if user_role != 'admin':
                return jsonify(
                    {'message': 'Accès refusé. Administrateur requis.'}), 403

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Jeton expiré.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Jeton invalide.'}), 401
        except Exception as e:
            print(f"Erreur de vérification JWT: {e}")
            return jsonify({'message': 'Erreur serveur interne.'}), 500

    return decorated


# DANS app.py

@app.route('/api/admin/users', methods=['GET', 'OPTIONS'])
@admin_required
def get_all_users():
    # Gérer la requête OPTIONS (pré-vol) et le 200 OK
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    # --- Début de la Logique GET ---
    conn = get_db_connection()
    if not conn:
        # CAS D'ERREUR 1 : Connexion DB échouée
        return jsonify(
            {"error": "Erreur de connexion à la base de données."}), 500

    try:
        cur = conn.cursor()
        # Sélectionner toutes les infos sauf le mot de passe hashé
        cur.execute(
            "SELECT id, full_name, username, phone_number, email, role FROM personnal_infos ORDER BY id;")
        users = cur.fetchall()

        # Mettre en forme les résultats pour le JSON
        columns = ['id', 'full_name', 'username', 'phone_number', 'email',
                   'role']
        users_list = [dict(zip(columns, user)) for user in users]

        # CAS DE SUCCÈS : Retourner les données
        return jsonify(users_list), 200

    except Exception as e:
        # CAS D'ERREUR 2 : Erreur SQL ou autre erreur inattendue
        print(f"Erreur DB ou autre exception: {e}")
        return jsonify({
                           "error": "Erreur lors de la récupération des données utilisateurs."}), 500

    finally:
        # Le bloc finally s'exécute toujours pour fermer la connexion
        if conn: conn.close()


# DANS app.py

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT', 'OPTIONS'])
@admin_required
def update_user_role(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.json
    new_role = data.get('role')

    if new_role not in ['user', 'employee', 'admin']:
        return jsonify({"error": "Rôle invalide fourni."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur de connexion à la base de données."}), 500

    try:
        cur = conn.cursor()
        # Requête SQL pour la mise à jour
        cur.execute("UPDATE personnal_infos SET role = %s WHERE id = %s;", (new_role, user_id))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"message": f"Utilisateur ID {user_id} non trouvé."}), 404

        return jsonify({"message": f"Rôle de l'utilisateur {user_id} mis à jour à {new_role}."}), 200
    except Exception as e:
        print(f"Erreur DB: {e}")
        conn.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour du rôle."}), 500
    finally:
        if conn: conn.close()


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@admin_required
def delete_user(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    conn = get_db_connection()
    if not conn:
        return jsonify({
                           "error": "Erreur de connexion à la base de données."}), 500

    try:
        cur = conn.cursor()
        # Requête SQL pour la suppression
        cur.execute("DELETE FROM personnal_infos WHERE id = %s;",
                    (user_id,))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({
                               "message": f"Utilisateur ID {user_id} non trouvé."}), 404

        return jsonify({
                           "message": f"Utilisateur ID {user_id} supprimé avec succès."}), 200
    except Exception as e:
        print(f"Erreur DB: {e}")
        conn.rollback()
        return jsonify({
                           "error": "Erreur lors de la suppression de l'utilisateur."}), 500
    finally:
        if conn: conn.close()




# ----------------- MAIN -----------------------------------

if __name__ == '__main__':
    check_db_and_run()
