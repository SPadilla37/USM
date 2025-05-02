from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import hashlib
import secrets
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = secrets.token_hex(16)  # Clave secreta para las sesiones

# Configuración de MongoDB Atlas
# IMPORTANTE: La contraseña no debe tener los símbolos < y >
MONGODB_URI = "mongodb+srv://padilla31661983:Pm181920.@usm.qh90qid.mongodb.net/?retryWrites=true&w=majority&appName=USM"
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
        
        # Insertar nuevo usuario
        user_data = {
            "username": username,
            "password": hashed_password,
            "email": email
        }
        
        result = users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        
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
            # Guardar información del usuario en la sesión
            user_id = str(user["_id"])
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
        users = list(users_collection.find({}, {"password": 0}))  # Excluir contraseñas
        
        # Convertir ObjectId a string para poder serializar a JSON
        for user in users:
            user["_id"] = str(user["_id"])
            
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)