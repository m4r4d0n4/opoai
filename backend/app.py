from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
import requests  # Para hacer peticiones HTTP al servidor privado

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Cambia esto en producción
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

DB_FILE = "database.db"
PRIVATE_SERVER = "http://192.168.1.137:15678"  # Cambia esto por la IP de tu servidor privado

# Función para conectar con SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear la base de datos con usuario admin por defecto
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()

    # Crear usuario admin por defecto si no existe
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       ("admin", hashed_password, "admin"))
        conn.commit()
    conn.close()

init_db()

# Endpoint de login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user["password"], data["password"]):
        token = create_access_token(identity={"username": user["username"], "role": user["role"]})
        return jsonify(token=token, role=user["role"])
    
    return jsonify({"message": "Invalid credentials"}), 401

# Endpoint de registro (solo accesible por admin)
@app.route('/register', methods=['POST'])
@jwt_required()
def register():
    current_user = get_jwt_identity()
    if current_user["role"] != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       (data["username"], hashed_password, "user"))
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists"}), 400

# Endpoint para redirigir a un servidor privado
@app.route('/proxy', methods=['GET'])
@jwt_required()
def proxy():
    user = get_jwt_identity()
    print(f"Usuario autenticado: {user['username']} está accediendo al servidor privado.")

    # Reenvía la solicitud al servidor privado
    try:
        response = requests.get(PRIVATE_SERVER)
        return (response.content, response.status_code, response.headers.items())
    except requests.RequestException as e:
        return jsonify({"error": "No se pudo conectar al servidor privado"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=("/ssl/opoai.es_ssl_certificate.cer", "/ssl/opoai.key"))
