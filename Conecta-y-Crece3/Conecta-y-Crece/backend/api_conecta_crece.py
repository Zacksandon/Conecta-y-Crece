from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector as mysql
from mysql.connector import Error
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import jwt  # pip install PyJWT
from datetime import datetime, timedelta

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Añadir ruta al directorio padre
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar configuración
from backend.config import DB_CONFIG

app = Flask(__name__)
CORS(app, resources={
    r"/login": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/registro": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/admin/reportes": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/admin/eliminar/*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/proyectos*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/reacciones*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/perfil*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/assets/uploads/*": {"origins": "*"}
}, supports_credentials=True)

# ==================== JWT CONFIG ====================
SECRET_KEY = "conecta_y_crece_2025_sena"
app.config['SECRET_KEY'] = SECRET_KEY

# CARPETA PARA FOTOS
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_token(user_id):
    return jwt.encode({
        'id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return None

# ==================== ADMIN HARDCODEADO ====================
ADMIN_CREDENTIALS = {
    "correo": "admin@conecta-crece.com",
    "password_hash": generate_password_hash("admin123"),
    "nombre": "Admin",
    "apellido": "Sistema",
    "rol": "admin",
    "id": 1
}

def get_db_connection():
    try:
        connection = mysql.connect(**DB_CONFIG)
        logger.info("Conexión MySQL exitosa")
        return connection
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        return None

# ==================== REGISTRO ====================
@app.route('/registro', methods=['POST'])
def registrar_usuario():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        correo = data.get('correo')
        password = data.get('password')
        rol = data.get('rol', 'emprendedor')
        ubicacion = data.get('ubicacion')
        bio = data.get('bio')
        habilidades = data.get('habilidades')

        if correo == ADMIN_CREDENTIALS['correo']:
            return jsonify({"error": "Este correo está reservado para admin"}), 403

        if not all([nombre, apellido, correo, password]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        if rol not in ['emprendedor', 'mentor', 'inversor']:
            return jsonify({"error": "Rol no válido"}), 400

        cursor = connection.cursor()
        hashed_password = generate_password_hash(password)
        consulta = """
            INSERT INTO usuarios 
            (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades, experiencia, intereses, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, '', 1)
        """
        valores = (nombre, apellido, correo, hashed_password, rol, ubicacion, bio, habilidades)
        cursor.execute(consulta, valores)
        connection.commit()
        user_id = cursor.lastrowid
        token = generate_token(user_id)
        logger.info(f"Usuario registrado: {correo}")
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "id": user_id,
            "token": token
        }), 201

    except Error as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "El correo ya está registrado"}), 409
        logger.error(f"Error al registrar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== LOGIN ====================
@app.route('/login', methods=['POST'])
def login_usuario():
    data = request.get_json()
    correo = data.get('correo')
    password = data.get('password')

    if not all([correo, password]):
        return jsonify({"error": "Faltan datos requeridos"}), 400

    # ADMIN
    if correo == ADMIN_CREDENTIALS['correo']:
        if check_password_hash(ADMIN_CREDENTIALS['password_hash'], password):
            token = generate_token(ADMIN_CREDENTIALS['id'])
            usuario = {k: v for k, v in ADMIN_CREDENTIALS.items() if k != 'password_hash'}
            logger.info("Admin logueado")
            return jsonify({
                "message": "Inicio de sesión exitoso",
                "usuario": usuario,
                "token": token,
                "redirect": "admin.html"
            }), 200
        else:
            return jsonify({"error": "Contraseña incorrecta"}), 401

    # USUARIOS
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, rol, password, foto_url FROM usuarios WHERE correo = %s AND activo = 1", (correo,))
        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario['password'], password):
            del usuario['password']
            token = generate_token(usuario['id'])
            logger.info(f"Login exitoso: {correo}")
            return jsonify({
                "message": "Inicio de sesión exitoso",
                "usuario": usuario,
                "token": token
            }), 200
        else:
            return jsonify({"error": "Credenciales incorrectas"}), 401

    except Error as e:
        logger.error(f"Error al iniciar sesión: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== PERFIL: OBTENER ====================
@app.route('/api/perfil/<int:user_id>', methods=['GET'])
def get_perfil(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload['id'] != user_id:
        return jsonify({"error": "No autorizado"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT nombre, apellido, correo, rol, ubicacion, bio, habilidades, experiencia, intereses, foto_url 
            FROM usuarios WHERE id = %s AND activo = 1
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except Error as e:
        logger.error(f"Error al obtener perfil: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== PERFIL: ACTUALIZAR + FOTO ====================
@app.route('/api/perfil/<int:user_id>', methods=['PUT'])
def update_perfil(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload['id'] != user_id:
        return jsonify({"error": "No autorizado"}), 401

    foto_url = None

    # PROCESAR FOTO
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            foto_url = f"/assets/uploads/{filename}"

    # CAMPOS DE TEXTO
    campos = ['nombre', 'apellido', 'ubicacion', 'bio', 'habilidades', 'experiencia', 'intereses']
    valores = []
    set_parts = []

    for campo in campos:
        valor = request.form.get(campo, '')
        valores.append(valor)
        set_parts.append(f"{campo}=%s")

    if foto_url:
        valores.append(foto_url)
        set_parts.append("foto_url=%s")

    valores.append(user_id)
    set_clause = ', '.join(set_parts)

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()
        query = f"UPDATE usuarios SET {set_clause} WHERE id = %s"
        cursor.execute(query, valores)
        connection.commit()
        logger.info(f"Perfil actualizado: ID {user_id}, foto: {foto_url}")
        response = {"message": "Perfil actualizado"}
        if foto_url:
            response["foto_url"] = foto_url
        return jsonify(response), 200
    except Error as e:
        logger.error(f"Error al actualizar perfil: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== SERVIR FOTOS ====================
@app.route('/assets/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== PROYECTOS ====================
@app.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.titulo, p.descripcion, c.nombre AS categoria, u.nombre AS emprendedor, 
                   p.fecha_inicio AS fecha, p.progreso
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            JOIN categorias c ON p.categoria_id = c.id
            WHERE p.estado = 'activo'
        """)
        proyectos = cursor.fetchall()
        return jsonify(proyectos), 200
    except Error as e:
        logger.error(f"Error al obtener proyectos: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== REACCIONES ====================
@app.route('/api/reacciones', methods=['POST'])
def create_reaccion():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        proyecto_id = data.get('proyecto_id')
        usuario_id = data.get('usuario_id')
        tipo_reaccion = data.get('tipo_reaccion')

        if not all([proyecto_id, usuario_id, tipo_reaccion]):
            return jsonify({"error": "Faltan datos"}), 400

        if tipo_reaccion not in ['me-gusta', 'me-encanta', 'me-interesa', 'apoyo']:
            return jsonify({"error": "Reacción no válida"}), 400

        cursor = connection.cursor()
        cursor.execute("INSERT INTO reacciones (proyecto_id, usuario_id, tipo_reaccion) VALUES (%s, %s, %s)",
                       (proyecto_id, usuario_id, tipo_reaccion))
        connection.commit()
        return jsonify({"message": "Reacción registrada"}), 201
    except Error as e:
        logger.error(f"Error al registrar reacción: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/reacciones/<int:proyecto_id>', methods=['GET'])
def get_reacciones(proyecto_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT tipo_reaccion, COUNT(*) as count 
            FROM reacciones 
            WHERE proyecto_id = %s 
            GROUP BY tipo_reaccion
        """, (proyecto_id,))
        reacciones = cursor.fetchall()
        counts = {r['tipo_reaccion']: r['count'] for r in reacciones}
        return jsonify(counts), 200
    except Error as e:
        logger.error(f"Error al obtener reacciones: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== ADMIN ====================
@app.route('/admin/reportes', methods=['GET'])
def get_reportes():
    auth = request.headers.get('Authorization')
    if auth != 'Bearer admin123':
        return jsonify({"error": "Acceso denegado"}), 403

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, correo, rol, ubicacion, bio, habilidades, activo FROM usuarios WHERE activo = 1")
        reportes = cursor.fetchall()
        return jsonify({"reportes": reportes}), 200
    except Error as e:
        logger.error(f"Error al obtener reportes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/admin/eliminar/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    auth = request.headers.get('Authorization')
    if auth != 'Bearer admin123':
        return jsonify({"error": "Acceso denegado"}), 403

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = %s", (user_id,))
        if cursor.rowcount > 0:
            connection.commit()
            return jsonify({"message": "Usuario eliminado"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
    except Error as e:
        logger.error(f"Error al eliminar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== ACTUALIZAR (LEGACY) ====================
@app.route('/actualizar', methods=['PUT'])
def actualizar_usuario():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        user_id = data.get('id')
        campos = ['nombre', 'apellido', 'correo', 'ubicacion', 'bio', 'habilidades', 'experiencia', 'intereses']
        valores = [data.get(c, '') for c in campos]
        valores.append(user_id)

        cursor = connection.cursor()
        set_clause = ', '.join([f"{c}=%s" for c in campos])
        cursor.execute(f"UPDATE usuarios SET {set_clause} WHERE id = %s", valores)
        connection.commit()
        return jsonify({"message": "Perfil actualizado"}), 200
    except Error as e:
        logger.error(f"Error al actualizar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    logger.info("API Conecta y Crece iniciada")
    app.run(debug=True, host='0.0.0.0', port=5000)