from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import bcrypt
import os  # Pour gérer les variables d'environnement (meilleure pratique)

app = Flask(__name__)
# 1. Ajout de CORS pour permettre au Frontend.html de communiquer (comme dans .NET)
CORS(app)

# 2. Configuration de la Base de Données (Adaptée de votre ancienne chaîne de connexion)
# Vous pouvez mettre ces valeurs dans un fichier .env ou les laisser ici pour le test local
DB_HOST = "localhost"  # CHANGER si vous passez à la connexion externe
DB_NAME = "LevKatan"
DB_USER = "dan"
DB_PASSWORD = "rebeccawife"
DB_PORT = "5432"


# Fonction pour établir la connexion à la DB
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"❌ ERREUR DE CONNEXION DB: {e}")
        return None


# --- API ENDPOINTS ---

@app.route('/api/register', methods=['POST'])
def register():
    """
    Endpoint d'inscription. Crée un nouvel utilisateur dans la table personnal_infos.
    """
    data = request.json

    # 3. Extraction des données
    full_name = data.get('fullName')
    username = data.get('username')
    phone = data.get('phone')
    email = data.get('email')
    passwd = data.get('password')

    if not all([full_name, username, phone, email, passwd]):
        return jsonify({"message": "Données manquantes"}), 400


    # Sécurité: Hacher le mot de passe (équivalent BCrypt.Net)
    password_bytes = passwd.encode('utf-8')
    # bcrypt.gensalt() génère un sel aléatoire
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode(
        'utf-8')

    conn = get_db_connection()
    if conn is None:
        return jsonify({
            "message": "Erreur serveur: Impossible de se connecter à la DB"}), 500

    cur = conn.cursor()

    sql = """
        INSERT INTO personnal_infos (full_name, email, username, phone_number, passwd, role)
        VALUES (%s, %s, %s, %s, %s, 'user')
        RETURNING id;
    """

    try:
        cur.execute(sql, (
            full_name, email, username, phone, hashed_password))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(
            {"message": "Registered successfully", "userId": user_id}), 200

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({
            "message": "Email ou Nom d'utilisateur déjà utilisé."}), 409  # Code 409 Conflict (équivalent 23505 Postgres)

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"Erreur d'enregistrement: {e}")
        return jsonify({
            "message": "Erreur interne du serveur lors de l'enregistrement"}), 500


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
            "message": "Erreur serveur: Impossible de se connecter à la DB"}), 500

    cur = conn.cursor()
    sql = "SELECT username, passwd, role FROM personnal_infos WHERE email = %s"

    try:
        cur.execute(sql, (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user is None:
            return jsonify({
                "message": "Non autorisé"}), 401  # Unauthorized (utilisateur non trouvé)

        db_username, db_hashed_password, db_role = user

        # Vérification du mot de passe (équivalent BCrypt.Net.Verify)
        if bcrypt.checkpw(password.encode('utf-8'),
                          db_hashed_password.encode('utf-8')):
            # Succès (vous retournerez ici un JWT token dans une version finale)
            return jsonify({
                "message": "Login successful",
                "username": db_username,
                "role": db_role
            }), 200
        else:
            return jsonify({
                "message": "Non autorisé"}), 401  # Unauthorized (mot de passe incorrect)

    except Exception as e:
        cur.close()
        conn.close()
        print(f"Erreur de connexion: {e}")
        return jsonify({"message": "Erreur interne du serveur"}), 500


if __name__ == '__main__':
    # Le port 5230 est celui que votre frontend attendait, nous allons le réutiliser.
    app.run(debug=True, port=5230)
