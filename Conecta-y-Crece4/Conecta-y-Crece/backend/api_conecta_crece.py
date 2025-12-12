# ==================== API CONECTA Y CRECE - VERSIÓN FINAL ====================
# Autor: Zack Sandon
# Fecha: 10 de noviembre de 2025
# Proyecto: Plataforma de networking para emprendedores, mentores e inversores
# Tecnologías: Flask, MySQL, JWT, CORS, Glassmorphism UI
# Funcionalidades clave:
#   - Registro/Login con JWT
#   - Perfil propio y público
#   - Comunidad + Ver perfil
#   - Conexiones (solicitudes)
#   - Admin con token fijo
#   - Proyectos + Reacciones + Crear proyecto
#   - PDF con jsPDF

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector as mysql
from mysql.connector import Error
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import jwt
from datetime import datetime, timedelta

# ==================== CONFIGURACIÓN DE LOGS ====================
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
from backend.config import DB_CONFIG

app = Flask(__name__)

# ==================== CORS ====================
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ==================== CONFIG JWT Y FOTOS ====================
SECRET_KEY = "conecta_y_crece_2025_sena"
app.config['SECRET_KEY'] = SECRET_KEY

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

def get_db_connection():
    try:
        connection = mysql.connect(**DB_CONFIG)
        logger.info("Conexión MySQL exitosa")
        return connection
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        return None

# ==================== ADMIN HARDCODEADO ====================
ADMIN_CREDENTIALS = {
    "correo": "admin@conecta-crece.com",
    "password_hash": generate_password_hash("admin123"),
    "nombre": "Admin", "apellido": "Sistema", "rol": "administrador", "id": 1
}

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
            (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
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

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, rol, foto_url, password FROM usuarios WHERE correo = %s AND activo = 1", (correo,))
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

# ==================== PERFIL PROPIO ====================
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
            SELECT nombre, apellido, correo, rol, ubicacion, bio, habilidades, experiencia_años, foto_url 
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

# ==================== PERFIL PÚBLICO ====================
@app.route('/api/perfil-publico/<int:user_id>', methods=['GET'])
def get_perfil_publico(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT nombre, apellido, rol, ubicacion, bio, habilidades, foto_url 
            FROM usuarios WHERE id = %s AND activo = 1
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except Error as e:
        logger.error(f"Error al obtener perfil público: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== ACTUALIZAR PERFIL ====================
@app.route('/api/perfil/<int:user_id>', methods=['PUT'])
def update_perfil(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload['id'] != user_id:
        return jsonify({"error": "No autorizado"}), 401

    foto_url = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            foto_url = f"/assets/uploads/{filename}"

    campos = ['nombre', 'apellido', 'ubicacion', 'bio', 'habilidades', 'experiencia_años']
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
            SELECT p.id, p.titulo, p.descripcion, 
                   COALESCE(c.nombre, 'Sin categoría') AS categoria,
                   CONCAT(u.nombre, ' ', u.apellido) AS emprendedor,
                   p.fecha_inicio AS fecha,
                   COALESCE(p.progreso, 0) AS progreso
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.estado = 'publicado' AND p.activo = 1
            ORDER BY p.fecha_inicio DESC
        """)
        proyectos = cursor.fetchall()
        return jsonify(proyectos), 200
    except Error as e:
        logger.error(f"Error al obtener proyectos: {e}")
        return jsonify({"error": "Error en consulta de proyectos"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== CREAR PROYECTO ====================
@app.route('/api/proyectos', methods=['POST'])
def crear_proyecto():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    required = ['titulo', 'descripcion', 'categoria_id']
    if not all(k in data for k in required):
        return jsonify({"error": "Faltan datos: titulo, descripcion, categoria_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = conn.cursor()
        progreso = data.get('progreso', 0)
        cursor.execute("""
            INSERT INTO proyectos 
            (usuario_id, titulo, descripcion, categoria_id, progreso, estado, activo)
            VALUES (%s, %s, %s, %s, %s, 'publicado', 1)
        """, (payload['id'], data['titulo'], data['descripcion'], data['categoria_id'], progreso))
        conn.commit()
        return jsonify({"message": "Proyecto creado", "id": cursor.lastrowid}), 201
    except Error as e:
        logger.error(f"Error al crear proyecto: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ==================== REACCIONES ====================
@app.route('/api/reacciones', methods=['POST'])
def create_reaccion():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    proyecto_id = data.get('proyecto_id')
    tipo = data.get('tipo_reaccion') or data.get('tipo')

    if not proyecto_id or not tipo:
        return jsonify({"error": "Faltan datos"}), 400
    if tipo not in ['me_gusta', 'me_encanta', 'me_interesa', 'apoyo']:
        return jsonify({"error": "Reacción no válida"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reacciones WHERE proyecto_id = %s AND usuario_id = %s AND tipo = %s",
                       (proyecto_id, payload['id'], tipo))
        cursor.execute("INSERT INTO reacciones (proyecto_id, usuario_id, tipo) VALUES (%s, %s, %s)",
                       (proyecto_id, payload['id'], tipo))
        conn.commit()
        return jsonify({"message": "Reacción actualizada"}), 200
    except Error as e:
        logger.error(f"Error en reacción: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/reacciones/<int:proyecto_id>', methods=['GET'])
def get_reacciones(proyecto_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT tipo, COUNT(*) as count 
            FROM reacciones 
            WHERE proyecto_id = %s 
            GROUP BY tipo
        """, (proyecto_id,))
        rows = cursor.fetchall()
        counts = {r['tipo']: r['count'] for r in rows}
        for t in ['me_gusta', 'me_encanta', 'me_interesa', 'apoyo']:
            counts.setdefault(t, 0)
        return jsonify(counts), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ==================== COMUNIDAD ====================
@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios_publicos():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, apellido, rol, ubicacion, bio, habilidades, foto_url 
            FROM usuarios WHERE activo = 1
        """)
        usuarios = cursor.fetchall()
        return jsonify({"usuarios": usuarios}), 200
    except Error as e:
        logger.error(f"Error al listar usuarios: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ==================== CONEXIONES ====================
@app.route('/api/conexiones', methods=['POST'])
def crear_conexion():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    usuario_destino_id = data.get('usuario_destino_id')
    if not usuario_destino_id:
        return jsonify({"error": "Falta usuario destino"}), 400
    if int(usuario_destino_id) == payload['id']:
        return jsonify({"error": "No puedes conectarte contigo mismo"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM conexiones 
            WHERE (usuario_origen_id = %s AND usuario_destino_id = %s) 
               OR (usuario_origen_id = %s AND usuario_destino_id = %s)
        """, (payload['id'], usuario_destino_id, usuario_destino_id, payload['id']))
        if cursor.fetchone():
            return jsonify({"error": "Ya existe una solicitud"}), 409

        cursor.execute("""
            INSERT INTO conexiones (usuario_origen_id, usuario_destino_id, estado) 
            VALUES (%s, %s, 'pendiente')
        """, (payload['id'], usuario_destino_id))
        conn.commit()
        return jsonify({"message": "Solicitud enviada"}), 201
    except Error as e:
        logger.error(f"Error al crear conexión: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/conexiones/existe/<int:destino_id>', methods=['GET'])
def existe_conexion(destino_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM conexiones 
            WHERE (usuario_origen_id = %s AND usuario_destino_id = %s) 
               OR (usuario_origen_id = %s AND usuario_destino_id = %s)
        """, (payload['id'], destino_id, destino_id, payload['id']))
        existe = cursor.fetchone() is not None
        return jsonify({"existe": existe}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

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

# ==================== INICIO ====================
if __name__ == '__main__':
    logger.info("API Conecta y Crece iniciada - ¡Listo para exponer!")
    app.run(debug=True, host='0.0.0.0', port=5000)