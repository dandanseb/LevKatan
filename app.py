import os
import jwt
import psycopg2
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:  # Forces you to have a secure key in .env. Fails safely if missing.
    raise ValueError("No JWT_SECRET_KEY set for Flask application")

JWT_ALGORITHM = "HS256"

# --- DB Helper ---
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None

# --- Decorators ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS': return jsonify({}), 200
        token_header = request.headers.get('Authorization')
        if not token_header or not token_header.startswith('Bearer '):
            return jsonify({'message': 'Token missing'}), 401
        try:
            token = token_header[7:]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            request.user_data = data # Store user info for the route to use
        except Exception:
            return jsonify({'message': 'Invalid Token'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS': return jsonify({}), 200
        token_header = request.headers.get('Authorization')
        if not token_header: return jsonify({'message': 'Token missing'}), 401
        try:
            token = token_header.split(" ")[1]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if data['role'] != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
        except Exception:
            return jsonify({'message': 'Invalid Token'}), 401
        return f(*args, **kwargs)
    return decorated

def employee_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS': return jsonify({}), 200
        token_header = request.headers.get('Authorization')
        if not token_header: return jsonify({'message': 'Token missing'}), 401
        try:
            token = token_header.split(" ")[1]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if data['role'] not in ['admin', 'employee']:
                return jsonify({'message': 'Employee access required'}), 403
        except Exception:
            return jsonify({'message': 'Invalid Token'}), 401
        return f(*args, **kwargs)
    return decorated

# --- AUTH ROUTES (Login/Register) ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('fullName')
    username = data.get('username')
    phone_number = data.get('phone_number')
    email = data.get('email')
    passwd = data.get('password')
    
    # Basic validation
    if not all([full_name, username, email, passwd]):
        return jsonify({"message": "Missing required fields"}), 400

    password_bytes = passwd.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO personnal_infos (full_name, username, phone_number, email, passwd, role) VALUES (%s, %s, %s, %s, %s, 'user') RETURNING id;", (full_name, username, phone_number, email, hashed_password))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "Registered", "userId": user_id}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, passwd, role FROM personnal_infos WHERE email = %s", (email,))
    user = cur.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        token = jwt.encode({'user_id': user[0], 'username': user[1], 'role': user[3], 'exp': datetime.utcnow() + timedelta(hours=24)}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return jsonify({"message": "Success", "username": user[1], "role": user[3], "token": token}), 200
    return jsonify({"message": "Invalid credentials"}), 401


# ----- USER ROUTES (Catalog / Borrowing requests / Profile / Donation requests) -----

#---- PROFILE------
@app.route('/api/user/me', methods=['GET'])
@token_required
def get_user_profile():
    user_id = request.user_data['user_id']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "INTERNAL SERVOR ERROR (DB)"}), 500
    cur = conn.cursor()
    
    try:
        # Selects the user's personal data
        sql = """
            SELECT username, full_name, email, phone_number 
            FROM personnal_infos 
            WHERE id = %s;
        """
        cur.execute(sql, (user_id,))
        user_info = cur.fetchone()
        
        if user_info:
            columns = ['username', 'full_name', 'email', 'phone_number']
            result = dict(zip(columns, user_info))
            return jsonify(result), 200
        else:
            return jsonify({"message": "User profile not found"}), 404
            
    except Exception as e:
        print(f"Error retrieving profile: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        conn.close()


@app.route('/api/user/me', methods=['PUT'])
@token_required
def update_user_profile():
    user_id = request.user_data['user_id']
    data = request.json
    
    # Editable data sent by the Frontend: The username cannot be changed
    full_name = data.get('full_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "INTERNAL SERVER ERROR (DB)"}), 500
    cur = conn.cursor()
    
    try:
        # Mise à jour des champs modifiables.
        sql = """
            UPDATE personnal_infos 
            SET full_name = %s, 
                email = %s, 
                phone_number = %s
            WHERE id = %s 
            RETURNING id;
        """
        cur.execute(sql, (full_name, email, phone_number, user_id))
        
        updated_id = cur.fetchone()
        
        if updated_id:
            conn.commit()
            return jsonify({"message": "Profil mis à jour"}), 200
        else:
            conn.rollback()
            return jsonify({"message": "Profil non trouvé"}), 404
            
    except Exception as e:
        conn.rollback()
        print(f"Error updating profile: {e}")
        return jsonify({"message": f"update error: {e}"}), 400
    finally:
        conn.close()

#--- CATALOG ----
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # UPDATED: Fetching description and donator_email as well
        cur.execute("SELECT id, product_name, category, status, description, donator_email FROM products WHERE status = 'available';")
        products = [{
            'id': r[0], 
            'name': r[1], 
            'category': r[2], 
            'status': r[3],
            'description': r[4], 
            'owner_email': r[5] # Mapping donator_email to owner_email for frontend compatibility
        } for r in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching products: {e}")
        conn.rollback()
        # Fallback query if columns are missing
        cur.execute("SELECT id, product_name, category, status FROM products WHERE status = 'available';")
        products = [{'id': r[0], 'name': r[1], 'category': r[2], 'status': r[3], 'description': '', 'owner_email': ''} for r in cur.fetchall()]

    conn.close()
    return jsonify(products), 200


@app.route('/api/borrow', methods=['POST'])
@token_required
def borrow_product():
    data = request.json
    product_id = data.get('product_id')
    returned_date_str = data.get('returned_date') # YYYY-MM-DD
    user_id = request.user_data['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Fetch Limits
        cur.execute("SELECT setting_key, setting_value FROM system_settings;")
        rows = cur.fetchall()
        settings = {row[0]: row[1] for row in rows}
        max_items = int(settings.get('max_borrow_items', 3))
        max_days = int(settings.get('max_borrow_days', 14))

        # 2. Check User's Current Limit
        cur.execute("SELECT COUNT(*) FROM borrow_requests WHERE user_id = %s AND status IN ('pending', 'approved', 'confirmation_pending')", (user_id,))
        current_count = cur.fetchone()[0]
        
        if current_count >= max_items:
            return jsonify({"message": f"הגעת למכסת ההשאלות שלך ({max_items} פריטים)."}), 400

        # 3. Validate Date
        if not returned_date_str:
            return jsonify({"message": "Date is required"}), 400
            
        return_date = datetime.strptime(returned_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if return_date <= today:
            return jsonify({"message": "תאריך ההחזרה חייב להיות עתידי"}), 400
            
        delta = return_date - today
        if delta.days > max_days:
            return jsonify({"message": f"תקופת ההשאלה חורגת מהמותר ({max_days} ימים)."}), 400

        # 4. Check Availability & Create Request (Existing Logic)
        cur.execute("SELECT status FROM product WHERE id = %s", (product_id,))
        status = cur.fetchone()
        if not status or status[0] != 'available':
            return jsonify({"message": "Product not available"}), 400
            
        cur.execute("INSERT INTO borrow_requests (user_id, product_id, returned_date) VALUES (%s, %s, %s)", (user_id, product_id, returned_date_str))
        cur.execute("UPDATE product SET status = 'unavailable' WHERE id = %s", (product_id,))
        
        conn.commit()
        return jsonify({"message": "בקשתך נשלחה בהצלחה!"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


#---BORROWING REQUEST---
@app.route('/api/my-requests', methods=['GET'])
@token_required
def get_my_requests():
    user_id = request.user_data['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    sql = """
        SELECT br.id, p.product_name, br.request_date, br.status, br.returned_date
        FROM borrow_requests br
        JOIN products p ON br.product_id = p.id  
        WHERE br.user_id = %s ORDER BY br.request_date DESC
    """
    cur.execute(sql, (user_id,))
    requests = [{'id': r[0], 'product': r[1], 'date': str(r[2]), 'status': r[3], 'returned_date': str(r[4]) if r[4] else None
    } for r in cur.fetchall()]
    
    conn.close()
    return jsonify(requests), 200

#---DONQTION REQUEST---
@app.route('/api/donate', methods=['POST'])
@token_required
def request_donation():
    data = request.json
    p_name = data.get('product_name')
    cat = data.get('category')
    desc = data.get('description')
    email = data.get('donator_email')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO donation_requests (product_name, category, description, donator_email)
            VALUES (%s, %s, %s, %s)
        """, (p_name, cat, desc, email))
        conn.commit()
        return jsonify({"message": "Donation request submitted"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- EMPLOYEE ROUTES (Manage Products - CRUD) ---

@app.route('/api/employee/products', methods=['POST'])
@employee_required
def create_product():
    
    data = request.json
    product_name = data.get('product_name')
    category = data.get('category')
    description = data.get('description')
    donator_email = data.get('donator_email')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Erreur interne du serveur (DB)"}), 500

    cur = conn.cursor()

    try:
        sql = """
            INSERT INTO products 
            (product_name, category, description, donator_email)
            VALUES (%s, %s, %s, %s) 
            RETURNING id;
        """
        cur.execute(sql, (product_name, category, description, donator_email))
        product_id = cur.fetchone()[0]
        conn.commit()

        return jsonify(
            {"message": "Produit créé avec succès", "id": product_id}), 201

    except Exception as e:
        conn.rollback()
        return jsonify(
            {"message": f"Erreur lors de la création du produit: {e}"}), 400
    finally:
        conn.close()

@app.route('/api/employee/products/<int:product_id>', methods=['GET'])
@employee_required
def get_single_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Erreur interne du serveur (DB)"}), 500

    cur = conn.cursor()

    try:
        sql = """
            SELECT id, product_name, category, description, donator_email, status 
            FROM products 
            WHERE id = %s;
        """
        cur.execute(sql, (product_id,))
        product = cur.fetchone()

        if product:
            columns = ['id', 'product_name', 'category', 'description', 'donator_email', 'status']
            result = dict(zip(columns, product))
            return jsonify(result), 200
        else:
            return jsonify({"message": "Produit non trouvé"}), 404

    except Exception as e:
        print(f"Erreur lors de la récupération du produit: {e}")
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        conn.close()


@app.route('/api/employee/products', methods=['GET'])
@employee_required
def get_all_products():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Erreur interne du serveur (DB)"}), 500
        
    cur = conn.cursor()
    
    try:
        sql = """
            SELECT 
                p.id, p.product_name, p.category, p.status, p.donator_email, p.publish_date,
                u.username as borrower_name
            FROM products p
            LEFT JOIN borrow_requests br ON p.id = br.product_id AND br.status = 'approved'
            LEFT JOIN personnal_infos u ON br.user_id = u.id
            ORDER BY p.id DESC;
        """
        cur.execute(sql)
        
        columns = ['id', 'product_name', 'category', 'status', 'donator_email', 'publish_date', 'borrower_name']
        products = [dict(zip(columns, r)) for r in cur.fetchall()]
        
        for p in products:
            p['publish_date'] = str(p['publish_date'])
        
        return jsonify(products), 200
        
    except Exception as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        conn.close()


@app.route('/api/employee/products/<int:product_id>', methods=['PUT'])
@employee_required
def update_product(product_id):
    data = request.json

    product_name = data.get('product_name')
    category = data.get('category')
    description = data.get('description')
    donator_email = data.get('donator_email')
    status = data.get('status')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Erreur interne du serveur (DB)"}), 500

    cur = conn.cursor()

    try:
        sql = """
            UPDATE products 
            SET product_name = %s, 
                category = %s, 
                description = %s, 
                donator_email = %s, 
                status = %s
            WHERE id = %s 
            RETURNING id;
        """
        cur.execute(sql, (product_name, category, description, donator_email, status, product_id ))

        updated_id = cur.fetchone()

        if updated_id:
            conn.commit()
            return jsonify({"message": "Produit mis à jour"}), 200
        else:
            conn.rollback()
            return jsonify({"message": "Produit non trouvé"}), 404

    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la mise à jour du produit: {e}")
        return jsonify({"message": f"Erreur de mise à jour: {e}"}), 400
    finally:
        conn.close()


@app.route('/api/employee/products/<int:product_id>', methods=['DELETE'])
@employee_required
def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Erreur interne du serveur (DB)"}), 500

    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM products WHERE id = %s RETURNING id;",
                    (product_id,))
        deleted_id = cur.fetchone()

        if deleted_id:
            conn.commit()
            return jsonify({
                               "message": "Produit supprimé"}), 204  # 204 No Content pour une suppression réussie
        else:
            return jsonify({"message": "Produit non trouvé"}), 404

    except Exception as e:
        conn.rollback()
        return jsonify(
            {"message": f"Erreur lors de la suppression du produit: {e}"}), 500
    finally:
        conn.close()



# --- EMPLOYEE ROUTES (Manage Requests) ---

@app.route('/api/employee/requests', methods=['GET'])
@employee_required
def get_all_requests():
    conn = get_db_connection()
    cur = conn.cursor()
    sql = """
        SELECT br.id, u.username, p.product_name, br.status, br.request_date, br.returned_date
        FROM borrow_requests br
        JOIN personnal_infos u ON br.user_id = u.id
        JOIN products p ON br.product_id = p.id
        WHERE br.status = 'pending'
    """
    cur.execute(sql)
    # On ajoute r[5] qui est returned_date
    requests = [{
        'id': r[0], 
        'username': r[1], 
        'product': r[2], 
        'status': r[3], 
        'date': str(r[4]),
        'returned_date': str(r[5]) if r[5] else 'לא צוין'
    } for r in cur.fetchall()]
    conn.close()
    return jsonify(requests), 200

@app.route('/api/employee/requests/<int:req_id>', methods=['PUT'])
@employee_required
def update_request_status(req_id):
    data = request.json
    new_status = data.get('status') # 'approved' or 'rejected'
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Mise à jour du statut de la requête
        # Si le statut est 'rejected', on remet returned_date à NULL
        if new_status == 'rejected':
            sql_req = "UPDATE borrow_requests SET status = %s, returned_date = NULL WHERE id = %s RETURNING product_id"
        else:
            sql_req = "UPDATE borrow_requests SET status = %s WHERE id = %s RETURNING product_id"
            
        cur.execute(sql_req, (new_status, req_id))
        result = cur.fetchone()
        
        if result:
            product_id = result[0]
            
            if new_status == 'approved':
                # Produit prêté
                cur.execute("UPDATE products SET status = 'borrowed' WHERE id = %s", (product_id,))
            elif new_status == 'rejected':
                # Produit refusé -> redevient disponible
                cur.execute("UPDATE products SET status = 'available' WHERE id = %s", (product_id,))
                
            conn.commit()
            return jsonify({"message": "Status updated and date cleared if rejected"}), 200
        else:
            return jsonify({"message": "Request not found"}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- EMPLOYEE ROUTES (DONATIONS Requests) ---

@app.route('/api/employee/donations', methods=['GET'])
@employee_required
def get_donations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, product_name, category, description, donator_email, created_at FROM donation_requests WHERE status = 'donation_pending' ORDER BY created_at DESC")
    dons = [{'id':r[0], 'product_name':r[1], 'category':r[2], 'description':r[3], 'donator_email':r[4], 'created_at':str(r[5])} for r in cur.fetchall()]
    conn.close()
    return jsonify(dons), 200

@app.route('/api/employee/donations/<int:don_id>/reject', methods=['DELETE'])
@employee_required
def reject_donation(don_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM donation_requests WHERE id = %s", (don_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/api/employee/donations/<int:don_id>/approve', methods=['POST'])
@employee_required
def approve_donation(don_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO products (product_name, category, description, donator_email, status)
            VALUES (%s, %s, %s, %s, 'available')
        """, (data['product_name'], data['category'], data['description'], data['donator_email']))
        
        cur.execute("UPDATE donation_requests SET status = 'approved' WHERE id = %s", (don_id,))
        
        conn.commit()
        return jsonify({"message": "Donation converted to product"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- Manual Returns ---

@app.route('/api/return', methods=['POST'])
@token_required
def return_product():
    data = request.json
    borrow_id = data.get('borrow_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get product_id from the borrow request
        cur.execute("SELECT product_id FROM borrow_requests WHERE id = %s", (borrow_id,))
        res = cur.fetchone()
        if not res:
            return jsonify({"message": "Request not found"}), 404
        product_id = res[0]

        # Update Request Status to 'returned' and set returned_date to today
        cur.execute("UPDATE borrow_requests SET status = 'returned', returned_date = CURRENT_DATE WHERE id = %s", (borrow_id,))
        
        # Mark Product as Available again
        # Note: Using 'product' (singular) as per your borrow_product function
        cur.execute("UPDATE product SET status = 'available' WHERE id = %s", (product_id,))
        
        conn.commit()
        return jsonify({"message": "המוצר הוחזר בהצלחה! תודה רבה 💖"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- EXTENSION Requests ---

@app.route('/api/extensions', methods=['POST'])
@token_required
def request_extension():
    data = request.json
    borrow_id = data.get('borrow_id')
    new_date_str = data.get('new_returned_date')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Fetch System Limits (Validation Logic)
        cur.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'max_borrow_days'")
        row = cur.fetchone()
        max_days = int(row[0]) if row else 14

        # 2. Validate Date
        today = datetime.now().date()
        try:
            requested_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
        except ValueError:
             return jsonify({"message": "פורמט תאריך לא תקין"}), 400

        if requested_date <= today:
             return jsonify({"message": "תאריך ההחזרה חייב להיות עתידי"}), 400

        # Calculate difference from TODAY (or from original start date? usually extensions are limited from *now*)
        if (requested_date - today).days > max_days:
             return jsonify({"message": f"תאריך זה חורג מהמותר ({max_days} ימים מהיום)."}), 400

        # 3. Check for existing pending request
        cur.execute("SELECT id FROM extension_requests WHERE borrow_id = %s AND status = 'extension_pending'", (borrow_id,))
        if cur.fetchone():
            return jsonify({"message": "כבר קיימת בקשת הארכה ממתינה עבור מוצר זה."}), 400

        # 4. Create Request
        cur.execute("""
            INSERT INTO extension_requests (borrow_id, new_returned_date)
            VALUES (%s, %s)
        """, (borrow_id, new_date_str))
        
        conn.commit()
        return jsonify({"message": "בקשת ההארכה נשלחה בהצלחה! ממתין לאישור עובד."}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# List extension requests
@app.route('/api/employee/extensions', methods=['GET'])
@employee_required
def get_extension_requests():
    conn = get_db_connection()
    cur = conn.cursor()
    sql = """
        SELECT er.id, u.username, p.product_name, br.returned_date, er.new_returned_date
        FROM extension_requests er
        JOIN borrow_requests br ON er.borrow_id = br.id
        JOIN personnal_infos u ON br.user_id = u.id
        JOIN products p ON br.product_id = p.id
        WHERE er.status = 'extension_pending'
    """
    cur.execute(sql)
    results = cur.fetchall()
    extensions = [{
        'id': r[0],
        'username': r[1],
        'product_name': r[2],
        'current_return_date': str(r[3]),
        'new_return_date': str(r[4])
    } for r in results]
    conn.close()
    return jsonify(extensions), 200

#  Approve or Reject the extension
@app.route('/api/employee/extensions/<int:ext_id>', methods=['PUT'])
@employee_required
def update_extension_status(ext_id):
    data = request.json
    status = data.get('status') # 'approved' or 'rejected'
    
    new_status = f"extension_{status}" # Transforme en 'extension_approved' ou 'extension_rejected' -- decision---
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if status == 'approved':
            cur.execute("SELECT borrow_id, new_returned_date FROM extension_requests WHERE id = %s", (ext_id,))
            res = cur.fetchone()
            if res:
                borrow_id, new_date = res
                cur.execute("UPDATE borrow_requests SET returned_date = %s WHERE id = %s", (new_date, borrow_id))
        
        cur.execute("UPDATE extension_requests SET status = %s WHERE id = %s", (new_status, ext_id))
        
        conn.commit()
        return jsonify({"message": f"Extension status updated to {new_status}"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- ADMIN ROUTES (Manage Users) ---
@app.route('/api/admin/users', methods=['GET', 'OPTIONS'])
@admin_required
def get_all_users():
    if request.method == 'OPTIONS': return jsonify({}), 200
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, username, phone_number, email, role FROM personnal_infos ORDER BY id;")
    users = [dict(zip(['id', 'full_name', 'username', 'phone_number', 'email', 'role'], r)) for r in cur.fetchall()]
    conn.close()
    return jsonify(users), 200

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT', 'OPTIONS'])
@admin_required
def update_user_role(user_id):
    if request.method == 'OPTIONS': return jsonify({}), 200
    new_role = request.json.get('role')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE personnal_infos SET role = %s WHERE id = %s;", (new_role, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Role updated"}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@admin_required
def delete_user(user_id):
    if request.method == 'OPTIONS': return jsonify({}), 200
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM personnal_infos WHERE id = %s;", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "User deleted"}), 200

# --- SETTINGS & LIMITS ROUTES ---
@app.route('/api/config', methods=['GET'])
def get_config():
    """Returns the system settings (max days, max items)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT setting_key, setting_value FROM system_settings;")
    rows = cur.fetchall()
    conn.close()
    
    settings = {row[0]: row[1] for row in rows}
    # Provide defaults if missing
    return jsonify({
        "max_borrow_days": int(settings.get('max_borrow_days', 14)),
        "max_borrow_items": int(settings.get('max_borrow_items', 3))
    }), 200

@app.route('/api/admin/config', methods=['POST'])
@admin_required
def update_config():
    """Updates system settings."""
    data = request.json
    max_days = data.get('max_borrow_days')
    max_items = data.get('max_borrow_items')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Upsert logic (Update if exists, Insert if not)
        cur.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('max_borrow_days', %s) ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;", (max_days,))
        cur.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('max_borrow_items', %s) ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;", (max_items,))
        conn.commit()
        return jsonify({"message": "Settings updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/borrow-status', methods=['GET'])
@token_required
def get_borrow_status():
    """Checks how many items the user has currently borrowed vs the limit."""
    user_id = request.user_data['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Limits
    cur.execute("SELECT setting_key, setting_value FROM system_settings;")
    rows = cur.fetchall()
    settings = {row[0]: row[1] for row in rows}
    max_items = int(settings.get('max_borrow_items', 3))
    max_days = int(settings.get('max_borrow_days', 14))

    # Count active requests (pending or approved)
    cur.execute("SELECT COUNT(*) FROM borrow_requests WHERE user_id = %s AND status IN ('pending', 'approved', 'confirmation_pending')", (user_id,))
    current_count = cur.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "current_borrowed": current_count,
        "max_items": max_items,
        "remaining_slots": max_items - current_count,
        "max_days": max_days
    }), 200

if __name__ == '__main__':
    # Reads the string "True" or "False" from .env and converts to boolean
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ('true', '1', 't')

    app.run(debug=debug_mode, port=5230, host='0.0.0.0')














