from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session  # Importar Flask-Session
import os
import hashlib
import secrets
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

# Configuración mejorada de CORS para garantizar que las cookies se envíen correctamente
CORS(app, 
     supports_credentials=True,
     origins=["https://usm-839u.onrender.com", "http://localhost:5000", "*"],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     expose_headers=["Content-Type", "Authorization", "Accept"],
     max_age=600)

app.secret_key = secrets.token_hex(16)  # Clave secreta para las sesiones

# Configuración para que las sesiones sean permanentes
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'  # Guardar sesiones en el sistema de archivos
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)  # La sesión durará 30 días
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Permitir cookies de sitios cruzados
app.config['SESSION_COOKIE_SECURE'] = True  # Solo enviar cookies por HTTPS

# Inicializar Flask-Session
Session(app)

# Configuración de MongoDB Atlas
# IMPORTANTE: Usa una contraseña que solo tenga letras y números, sin caracteres especiales
MONGODB_URI = "mongodb+srv://padilla31661983:35wNywPCQ5FwuK4i@usm.qh90qid.mongodb.net/?retryWrites=true&w=majority&appName=USM"
# Nombre de la base de datos
DB_NAME = "usm_app_db"

# Conectar a MongoDB
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db["users"]
locations_collection = db["locations"]

# Función auxiliar para hash de contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para generar IDs de usuario simples
def generate_user_id():
    # Buscar el mayor ID numérico existente
    highest_user = users_collection.find_one(
        {"numeric_id": {"$exists": True}},
        sort=[("numeric_id", -1)]  # Ordenar por numeric_id en orden descendente
    )
    
    if highest_user and "numeric_id" in highest_user:
        return highest_user["numeric_id"] + 1
    else:
        return 1  # Comenzar desde 1 si no hay usuarios

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
        # Verificar si el usuario o email ya existen
        if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return jsonify({'error': 'El nombre de usuario o email ya existe'}), 409
        
        # Generar ID numérico simple
        numeric_id = generate_user_id()
        
        # Insertar nuevo usuario
        user_data = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "numeric_id": numeric_id,
            "plain_password": password  # Solo para desarrollo, eliminar en producción
        }
        
        result = users_collection.insert_one(user_data)
        user_id = str(numeric_id)  # Usar ID numérico en lugar de ObjectId
        
        # Hacer que la sesión sea permanente
        session.permanent = True
        
        # Iniciar sesión automáticamente tras registro
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'success': True, 'message': 'Usuario registrado correctamente', 'user_id': user_id, 'username': username})
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
        # Buscar usuario por username y password
        user = users_collection.find_one({
            "username": username,
            "password": hashed_password
        })
        
        if user:
            # Hacer que la sesión sea permanente
            session.permanent = True
            
            # Guardar información del usuario en la sesión
            user_id = str(user.get("numeric_id", user["_id"]))  # Usar numeric_id si existe
            session['user_id'] = user_id
            session['username'] = user["username"]
            return jsonify({'success': True, 'user_id': user_id, 'username': user["username"]})
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

    try:
        # Actualizar o crear ubicación
        location_data = {
            "user_id": user_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": __import__('datetime').datetime.now()
        }
        
        # Actualizamos si existe, si no, creamos una nueva entrada
        locations_collection.update_one(
            {"user_id": user_id},
            {"$set": location_data},
            upsert=True
        )
        
        return jsonify({'message': 'Ubicación actualizada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para obtener la ubicación de un usuario por ID
@app.route('/get-location/<user_id>', methods=['GET'])
def get_location(user_id):
    try:
        location_data = locations_collection.find_one({"user_id": user_id})
        
        if not location_data:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Retornar solo la información de ubicación
        return jsonify(location_data["location"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para ver los usuarios (para administración)
@app.route('/admin/users', methods=['GET'])
def admin_users():
    try:
        # No excluimos passwords para poder verlas
        users = list(users_collection.find({}))
        
        # Convertir ObjectId a string y usar numeric_id como ID principal
        result = []
        for user in users:
            user_data = {
                "id": user.get("numeric_id", str(user["_id"])),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "hashed_password": user.get("password", ""),
                "plain_password": user.get("plain_password", "No disponible"),
                "_id": str(user["_id"])
            }
            result.append(user_data)
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)