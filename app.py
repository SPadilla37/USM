from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import os
import hashlib
import secrets

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = secrets.token_hex(16)  # Clave secreta para las sesiones

# Configuración de la base de datos
DB_PATH = 'users.db'

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Inicializar la base de datos al inicio
init_db()

# Almacenamiento temporal de ubicaciones (en memoria)
user_locations = {}

# Función auxiliar para hash de contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    # Hash de la contraseña
    hashed_password = hash_password(password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                      (username, hashed_password, email))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # Iniciar sesión automáticamente tras registro
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'success': True, 'message': 'Usuario registrado correctamente', 'user_id': user_id, 'username': username})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'El nombre de usuario o email ya existe'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    # Hash de la contraseña para comparar
    hashed_password = hash_password(password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?',
                      (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Guardar información del usuario en la sesión
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({'success': True, 'user_id': user[0], 'username': user[1]})
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para cerrar sesión
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sesión cerrada correctamente'})

# Ruta para verificar estado de sesión
@app.route('/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session['username']
        })
    return jsonify({'authenticated': False})

# Ruta para actualizar la ubicación de un usuario
@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.json
    user_id = data.get('userId')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not user_id or latitude is None or longitude is None:
        return jsonify({'error': 'Faltan datos'}), 400

    user_locations[user_id] = {'latitude': latitude, 'longitude': longitude}
    return jsonify({'message': 'Ubicación actualizada'})

# Ruta para obtener la ubicación de un usuario por ID
@app.route('/get-location/<user_id>', methods=['GET'])
def get_location(user_id):
    location = user_locations.get(user_id)
    if not location:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return jsonify(location)

if __name__ == '__main__':
    app.run(debug=True)