from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import secrets
from pymongo import MongoClient
import datetime
import jwt

app = Flask(__name__)

# Configuración CORS
CORS(app, supports_credentials=True)

# Clave secreta para JWT
JWT_SECRET_KEY = secrets.token_hex(32)
# Duración del token (30 días en segundos)
JWT_EXPIRATION = 30 * 24 * 60 * 60

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

# Función para generar token JWT
def generate_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

# Función para verificar token JWT
def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

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

# Rutas API
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    hashed_password = hash_password(password)
    
    try:
        if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return jsonify({'error': 'El nombre de usuario o email ya existe'}), 409
        
        numeric_id = generate_user_id()
        
        user_data = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "numeric_id": numeric_id,
            "plain_password": password  # Solo para desarrollo
        }
        
        users_collection.insert_one(user_data)
        user_id = str(numeric_id)
        
        token = generate_token(user_id, username)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username,
            'token': token
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    hashed_password = hash_password(password)
    
    try:
        user = users_collection.find_one({
            "username": username,
            "password": hashed_password
        })
        
        if user:
            user_id = str(user.get("numeric_id", user["_id"]))
            
            token = generate_token(user_id, user["username"])
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'username': user["username"],
                'token': token
            })
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-session', methods=['GET'])
def check_session():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'authenticated': False})
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if payload:
        return jsonify({
            'authenticated': True,
            'user_id': payload['user_id'],
            'username': payload['username']
        })
    return jsonify({'authenticated': False})

@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.json
    user_id = data.get('userId')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not user_id or latitude is None or longitude is None:
        return jsonify({'error': 'Faltan datos'}), 400

    try:
        location_data = {
            "user_id": user_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": datetime.datetime.now()
        }
        
        locations_collection.update_one(
            {"user_id": user_id},
            {"$set": location_data},
            upsert=True
        )
        
        return jsonify({'message': 'Ubicación actualizada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-location/<user_id>', methods=['GET'])
def get_location(user_id):
    try:
        location_data = locations_collection.find_one({"user_id": user_id})
        
        if not location_data:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify(location_data["location"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/users', methods=['GET'])
def admin_users():
    try:
        users = list(users_collection.find({}))
        
        result = []
        for user in users:
            user_data = {
                "id": user.get("numeric_id", str(user["_id"])),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "plain_password": user.get("plain_password", "No disponible")
            }
            result.append(user_data)
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)