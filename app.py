from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message # Added
import hashlib
import secrets
from pymongo import MongoClient
import datetime
import jwt
import random # Added
import requests # Added

app = Flask(__name__)

# Configuración CORS
CORS(app, supports_credentials=True)

# Clave secreta para JWT
JWT_SECRET_KEY = secrets.token_hex(32)
# Duración del token (30 días en segundos)
JWT_EXPIRATION = 30 * 24 * 60 * 60

# Configuración de Flask-Mail (¡IMPORTANTE: Cambia las credenciales!)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'aglmarquez2005@gmail.com'  # Cambia esto por tu correo real
app.config['MAIL_PASSWORD'] = 'knmxjtcfjtsrktdp'  # Cambia esto por tu contraseña o App Password de Gmail
app.config['MAIL_DEFAULT_SENDER'] = 'tu_correo@gmail.com' # Cambia esto

mail = Mail(app)

# Almacenamiento temporal de códigos de verificación (para producción, considera una solución persistente como Redis)
# verification_codes = {} # REMOVED - Replaced by MongoDB collection

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
verification_codes_collection = db["verification_codes"] # New collection for codes

# Ensure TTL index exists on verification_codes_collection for 10-minute expiration
# MongoDB will automatically delete documents from this collection 600 seconds (10 minutes)
# after the time specified in the "createdAt" field.
verification_codes_collection.create_index("createdAt", expireAfterSeconds=600)


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

# --- Nuevas Rutas para Verificación ---
@app.route('/send-code', methods=['POST'])
def send_code():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Correo no proporcionado'}), 400

    user_exists = False
    if users_collection.find_one({"email": email}):
        user_exists = True

    verification_code = random.randint(100000, 999999)

    try:
        # Store code in MongoDB with a timestamp for TTL
        verification_codes_collection.update_one(
            {"email": email},
            {"$set": {"code": str(verification_code), "createdAt": datetime.datetime.utcnow()}},
            upsert=True
        )
        
        msg = Message('Tu Código de Verificación - Transporte USM', recipients=[email])
        msg.body = f'Tu código de verificación para Transporte USM es: {verification_code}'
        mail.send(msg)
        print(f"Código enviado al correo {email}: {verification_code} (User exists: {user_exists})")
        return jsonify({'message': 'Código enviado por correo correctamente', 'user_exists': user_exists}), 200

    except Exception as e:
        print(f"Error enviando correo o guardando código: {str(e)}")
        return jsonify({'error': 'Error al enviar el código', 'details': str(e)}), 500

@app.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.json
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({'error': 'Correo o código no proporcionado'}), 400

    identifier = email 
    
    # Check code against MongoDB; TTL index handles expiration
    # No need to check createdAt explicitly if TTL index is reliable,
    # as find_one would return None for an expired (auto-deleted) document.
    query_result = verification_codes_collection.find_one({
        "email": identifier,
        "code": str(code).strip()
    })
    
    if query_result:
        # Code is correct and (implicitly) not expired due to TTL.
        # The /register endpoint will delete it upon successful registration.
        # Or, if login path is taken, it might just be left to expire by TTL.
        return jsonify({'message': 'Código verificado correctamente', 'verified_email': identifier}), 200
    else:
        # Could be wrong code, or code was correct but expired and auto-deleted by TTL.
        return jsonify({'error': 'Código incorrecto o expirado'}), 400

# --- Rutas API Modificadas ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') # Este email debería ser el verificado
    phone = data.get('phone')
    firstName = data.get('firstName')
    lastName = data.get('lastName')
    faculty = data.get('faculty')
    career = data.get('career')
    address = data.get('address')
    
    required_fields = [username, password, email, firstName, lastName, phone] # faculty, career, address pueden ser opcionales dependiendo de la lógica de negocio
    if not all(required_fields):
        return jsonify({'error': 'Faltan datos obligatorios (username, password, email, firstName, lastName, phone)'}), 400
    
    # Aquí se podría añadir una validación para asegurar que el email que se está registrando
    # es uno que ha pasado por el proceso de /verify-code recientemente.
    # Esto podría hacerse usando el `verification_codes` o un token temporal emitido por /verify-code.
    # Por simplicidad, esta validación extra no se añade aquí pero es RECOMENDADA.
    # Ejemplo: if email in verification_codes and verification_codes[email] == "VERIFIED_TEMP_TOKEN":

    hashed_password = hash_password(password)
    
    try:
        if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return jsonify({'error': 'El nombre de usuario o email ya existe'}), 409
        
        numeric_id = generate_user_id()
        
        user_data = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "phone": phone,
            "firstName": firstName,
            "lastName": lastName,
            "faculty": faculty,
            "career": career,
            "address": address,
            "numeric_id": numeric_id,
            "email_verified": True # Marcar el email como verificado
            # "plain_password": password  # ¡ELIMINADO! No guardar contraseñas en texto plano.
        }
        
        users_collection.insert_one(user_data)
        user_id_str = str(numeric_id)
        
        # Limpiar el código de verificación de la colección persistente si el registro fue exitoso
        if email:
            verification_codes_collection.delete_one({"email": email})
            
        token = generate_token(user_id_str, username)
        
        return jsonify({
            'success': True,
            'user_id': user_id_str,
            'username': username,
            'token': token
        })
    except Exception as e:
        print(f"Error en registro: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('username') # This can be username or email
    email_provided = data.get('email') # Explicitly get email if sent
    password = data.get('password')
    
    if not (identifier or email_provided) or not password:
        return jsonify({'error': 'Faltan datos obligatorios (usuario/email y contraseña)'}), 400
    
    hashed_password = hash_password(password)
    
    query = {}
    if email_provided: # Prioritize email if explicitly provided (e.g. from new login_password_mobile page)
        query = {"email": email_provided, "password": hashed_password}
    elif identifier: # Fallback to identifier which could be username or email
        query = {"$or": [{"username": identifier}, {"email": identifier}], "password": hashed_password}

    try:
        user = users_collection.find_one(query)
        
        if user:
            user_id = str(user.get("numeric_id", user["_id"]))
            username = user["username"] # Always use the stored username for the token
            
            token = generate_token(user_id, username)
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'username': username,
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