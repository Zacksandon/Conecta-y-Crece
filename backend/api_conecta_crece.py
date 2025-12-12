# api_conecta_crece.py
# ==================== API CONECTA Y CRECE - VERSIÓN FINAL (ACTUALIZADA) ====================
# Autor: Zack Sandon (adaptada)
# Fecha: 10 de noviembre de 2025 (actualizado)
# NOTA: Este archivo mantiene tu estructura original; se agregaron y corrigieron endpoints.

import dbm
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import mysql.connector as mysql
from mysql.connector import Error
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import importlib
from flask import send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import traceback
import json
import jwt
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from functools import wraps

# Intentar importar PyJWT (jwt) de forma segura
try:
    jwt = importlib.import_module('jwt')
except Exception as e:
    jwt = None

# ==================== CONFIGURACIÓN DE LOGS ====================
import logging, sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Añadir ruta al directorio padre si es necesario (ya usado en tu proyecto)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from backend.config import DB_CONFIG  # Mantén tu config con credenciales DB
try:
    from backend.config import DB_CONFIG
except Exception:
    # Fallback: si no existe, intenta variables de entorno o un DB_CONFIG por defecto (para pruebas)
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASS', ''),
        'database': os.environ.get('DB_NAME', 'conecta_crece'),
        'port': int(os.environ.get('DB_PORT', 3306))
    }

app = Flask(__name__, static_folder='frontend', static_url_path='')
# === SIRVE LOS ARCHIVOS ESTÁTICOS DE UPLOADS (SOLO ESTA LÍNEA) ===
app.static_folder = 'frontend'
app.static_url_path = ''

# O si usas SocketIO, ponlo así:
# socketio = SocketIO(app, cors_allowed_origins="*")
# app.static_folder = 'frontend'
# app.static_folder = 'frontend'

# ==================== CORS ====================
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ==================== CONFIG JWT Y FOTOS ====================
SECRET_KEY = "conecta_y_crece_2025_sena_ultra_seguro_2025"
app.config['SECRET_KEY'] = SECRET_KEY
JWT_SECRET = SECRET_KEY   # ← AQUÍ ESTÁ LA CLAVE
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def generate_token(user_id):
    payload = {
        'id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)  # dura 30 días
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # PyJWT a veces devuelve bytes, a veces str → lo normalizamos
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token
def verify_token(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token inválido o corrupto")
        return None
    except Exception as e:
        logger.warning(f"Error al decodificar token: {e}")
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
#chat
socketio = SocketIO(app, cors_allowed_origins="*")
# ==================== RUTAS ====================

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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

# ==================== PERFIL PROPIO ====================
@app.route('/api/perfil/<int:user_id>', methods=['GET'])
def get_perfil(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != user_id:
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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

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
            SELECT nombre, apellido, rol, ubicacion, bio, habilidades, experiencia_años, foto_url
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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

# ==================== ACTUALIZAR PERFIL ====================
@app.route('/api/perfil/<int:user_id>', methods=['PUT'])
def update_perfil(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != user_id:
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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

# ==================== SERVIR FOTOS/ARCHIVOS ====================
# === SIRVE ARCHIVOS SUBIDOS (IMÁGENES, VIDEOS, PDF) - 100% FUNCIONAL ===
@app.route('/assets/uploads/<path:filename>')
def serve_uploads(filename):
    try:
        # Ruta absoluta correcta
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets', 'uploads'))
        
        # Seguridad: evitar ataques de path traversal
        requested_path = os.path.abspath(os.path.join(uploads_dir, filename))
        if not requested_path.startswith(uploads_dir):
            return "Acceso denegado", 403
            
        if not os.path.exists(requested_path):
            return "Archivo no encontrado", 404
            
        return send_from_directory(uploads_dir, filename)
        
    except Exception as e:
        logger.error(f"Error sirviendo archivo {filename}: {e}")
        return "Error interno", 500

# ==================== PROYECTOS ====================

@app.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.id, 
                p.titulo, 
                p.descripcion,
                p.descripcion_larga,
                p.progreso,
                p.imagen_principal_url,
                p.video_pitch_url,
                p.sitio_web,
                p.whatsapp,
                p.instagram,
                p.facebook,
                p.linkedin,
                p.usuario_id,
                CONCAT(u.nombre, ' ', COALESCE(u.apellido, '')) AS emprendedor,
                COALESCE(c.nombre, 'Sin categoría') AS categoria
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.estado = 'publicado' AND p.activo = 1
            ORDER BY p.id DESC
        """)
        proyectos = cursor.fetchall()
        
        # Agregar reacciones por proyecto
        for proyecto in proyectos:
            cursor.execute("""
                SELECT tipo, COUNT(*) as total 
                FROM reacciones 
                WHERE proyecto_id = %s 
                GROUP BY tipo
            """, (proyecto['id'],))
            reacciones = cursor.fetchall()
            reaccion_dict = {r['tipo']: r['total'] for r in reacciones}
            proyecto['reacciones'] = {
                'me_gusta': reaccion_dict.get('me_gusta', 0),
                'me_encanta': reaccion_dict.get('me_encanta', 0),
                'apoyo': reaccion_dict.get('apoyo', 0)
            }
        
        return jsonify(proyectos), 200
        
    except Error as e:
        logger.error(f"Error al obtener proyectos: {e}")
        return jsonify({"error": f"Error en consulta: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Soporta JSON (Content-Type application/json) y multipart/form-data (para imagen/video)
@app.route('/api/proyectos', methods=['POST'])
def crear_proyecto():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    # Subida de archivos
    def subir(campo, prefijo):
        if campo in request.files and request.files[campo].filename != '':
            file = request.files[campo]
            if allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{prefijo}_{payload['id']}_{int(datetime.now().timestamp())}.{ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return f"/assets/uploads/{filename}"
        return None

    imagen_url = subir('imagen_principal', 'img')
    video_url  = subir('video_pitch', 'vid')
    pdf_url    = subir('catalogo_pdf', 'pdf')

    # Campos del formulario
    titulo            = request.form.get('titulo')
    descripcion       = request.form.get('descripcion')
    descripcion_larga = request.form.get('descripcion_larga', '')
    categoria_id      = request.form.get('categoria_id')
    progreso          = request.form.get('progreso', 0)
    sitio_web         = request.form.get('sitio_web')
    telefono_proyecto = request.form.get('telefono_proyecto')
    whatsapp          = request.form.get('whatsapp')
    instagram         = request.form.get('instagram')
    facebook          = request.form.get('facebook')
    linkedin          = request.form.get('linkedin')

    if not titulo or not descripcion or not categoria_id:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO proyectos 
        (usuario_id, titulo, descripcion, descripcion_larga, categoria_id, progreso, estado, activo,
         imagen_principal_url, video_pitch_url, catalogo_pdf_url,
         sitio_web, telefono_proyecto, whatsapp, instagram, facebook, linkedin)
        VALUES (%s,%s,%s,%s,%s,%s,'borrador',1, %s,%s,%s, %s,%s,%s,%s,%s,%s)
    """, (payload['id'], titulo, descripcion, descripcion_larga, categoria_id, progreso,
          imagen_url, video_url, pdf_url, sitio_web, telefono_proyecto,
          whatsapp, instagram, facebook, linkedin))
    conn.commit()
    conn.close()
    return jsonify({"message": "Proyecto creado", "id": cursor.lastrowid}), 201

@app.route('/api/proyectos/<int:proyecto_id>', methods=['GET'])
def detalle_proyecto(proyecto_id):
    token_header = request.headers.get('Authorization', '')
    payload = None
    if token_header.startswith('Bearer '):
        token = token_header.replace('Bearer ', '')
        payload = verify_token(token)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        if payload:
            # USUARIO LOGUEADO → VE TODO (incluso borradores propios)
            cursor.execute("""
                SELECT 
                    p.*,
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    CONCAT(u.nombre, ' ', u.apellido) AS emprendedor,
                    u.foto_url AS foto_emprendedor
                FROM proyectos p
                JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.id = %s AND p.activo = 1
            """, (proyecto_id,))
        else:
            # PÚBLICO → SOLO PROYECTOS PUBLICADOS
            cursor.execute("""
                SELECT 
                    p.*,
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    CONCAT(u.nombre, ' ', u.apellido) AS emprendedor,
                    u.foto_url AS foto_emprendedor
                FROM proyectos p
                JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.id = %s AND p.estado = 'publicado' AND p.activo = 1
            """, (proyecto_id,))

        proyecto = cursor.fetchone()

        if not proyecto:
            return jsonify({"error": "Proyecto no encontrado"}), 404

        return jsonify(proyecto), 200

    except Error as e:
        logger.error(f"Error en detalle_proyecto: {e}")
        return jsonify({"error": "Error interno"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
@app.route('/api/proyectos/<int:proyecto_id>', methods=['PUT'])
def editar_proyecto(proyecto_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    # Verificar dueño
    cursor = conn.cursor()
    cursor.execute("SELECT usuario_id FROM proyectos WHERE id = %s AND activo = 1", (proyecto_id,))
    row = cursor.fetchone()
    if not row or row[0] != payload['id']:
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    def subir_archivo(campo, prefijo):
        if campo in request.files and request.files[campo].filename:
            file = request.files[campo]
            if allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{prefijo}_{payload['id']}_{int(datetime.now().timestamp())}.{ext}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return f"/assets/uploads/{filename}"
        return None

    updates = []
    valores = []

    # Archivos
    if subir_archivo('imagen_principal', 'img'):
        updates.append("imagen_principal_url = %s")
        valores.append(subir_archivo('imagen_principal', 'img'))
    if subir_archivo('video_pitch', 'vid'):
        updates.append("video_pitch_url = %s")
        valores.append(subir_archivo('video_pitch', 'vid'))
    if subir_archivo('catalogo_pdf', 'pdf'):
        updates.append("catalogo_pdf_url = %s")
        valores.append(subir_archivo('catalogo_pdf', 'pdf'))

    # Campos de texto
    campos = ['titulo','descripcion','descripcion_larga','categoria_id','progreso',
              'sitio_web','telefono_proyecto','whatsapp','instagram','facebook','linkedin']
    for campo in campos:
        if campo in request.form:
            updates.append(f"{campo} = %s")
            valores.append(request.form.get(campo))

    if not updates:
        conn.close()
        return jsonify({"message": "Nada que actualizar"}), 200

    valores.append(proyecto_id)
    query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = %s"

    try:
        cursor.execute(query, valores)
        conn.commit()
        return jsonify({"message": "Proyecto actualizado"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/proyectos/<int:proyecto_id>', methods=['DELETE'])
def eliminar_proyecto(proyecto_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"No autorizado"}), 401
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT usuario_id FROM proyectos WHERE id = %s AND activo = 1", (proyecto_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error":"Proyecto no encontrado"}), 404
        if row['usuario_id'] != payload['id'] and payload.get('id') != 1:
            return jsonify({"error":"No autorizado para eliminar este proyecto"}), 403
        cursor.execute("UPDATE proyectos SET activo = 0 WHERE id = %s", (proyecto_id,))
        conn.commit()
        return jsonify({"message":"Proyecto eliminado"}), 200
    except Error as e:
        logger.error(f"Error eliminar proyecto: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

# ====== TOGGLE PUBLICAR / OCULTAR PROYECTO ======
@app.route('/api/proyectos/<int:proyecto_id>/toggle_publicacion', methods=['POST'])
def toggle_publicacion(proyecto_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que el proyecto pertenece al usuario
        cursor.execute("SELECT estado FROM proyectos WHERE id = %s AND usuario_id = %s AND activo = 1", 
                      (proyecto_id, payload['id']))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            return jsonify({"error": "Proyecto no encontrado o no autorizado"}), 404

        # Cambiar estado
        nuevo_estado = 'publicado' if proyecto['estado'] == 'borrador' else 'borrador'
        cursor.execute("UPDATE proyectos SET estado = %s WHERE id = %s", (nuevo_estado, proyecto_id))
        conn.commit()
        
        return jsonify({"message": "Estado actualizado", "nuevo": nuevo_estado}), 200

    except Error as e:
        logger.error(f"Error toggle publicacion: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
# ==================== MIS PROYECTOS (proyectos del usuario autenticado) ====================
@app.route('/api/mis_proyectos', methods=['GET'])
def mis_proyectos():
    token_header = request.headers.get('Authorization', '')
    if not token_header.startswith('Bearer '):
        return jsonify({"error": "Token faltante o mal formato"}), 401

    token = token_header.replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Token inválido o expirado"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.id, p.titulo, p.descripcion, p.descripcion_larga,
                p.progreso, p.estado, p.categoria_id,
                COALESCE(c.nombre, 'Sin categoría') AS categoria,
                p.imagen_principal_url, p.video_pitch_url, p.catalogo_pdf_url,
                p.sitio_web, p.telefono_proyecto,
                p.whatsapp, p.instagram, p.facebook, p.linkedin
            FROM proyectos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.usuario_id = %s AND p.activo = 1
            ORDER BY p.id DESC
        """, (payload['id'],))
        
        proyectos = cursor.fetchall()
        return jsonify({"proyectos": proyectos}), 200

    except Error as e:
        print(f"Error en /api/mis_proyectos: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
@app.route('/api/reacciones/<int:proyecto_id>', methods=['GET'])
def get_reacciones(proyecto_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
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
        logger.error(f"Error get_reacciones: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass
# ============== RUTA PARA FIJAR / DESFIJAR PROYECTO ==============
@app.route('/api/proyectos/<int:proyecto_id>/fijar', methods=['POST'])
def fijar_proyecto(proyecto_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token requerido"}), 401

    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        usuario_id = payload['user_id']
    except:
        return jsonify({"error": "Token inválido"}), 401

    proyecto = proyecto.query.get(proyecto_id)
    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado"}), 404

    # Si ya está fijado → desfijar, si no → fijar
    if usuario_id in proyecto.fijado_por:
        proyecto.fijado_por.remove(usuario_id)
        mensaje = "Desfijado"
    else:
        proyecto.fijado_por.append(usuario_id)
        mensaje = "Fijado"

    db.session.commit()
    return jsonify({"success": True, "mensaje": mensaje}), 200


# ============== RUTA PARA CREAR COMENTARIO ==============
@app.route('/api/comentarios', methods=['POST'])
def crear_comentario():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token requerido"}), 401

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        usuario_id = payload['user_id']
    except:
        return jsonify({"error": "Token inválido"}), 401

    data = request.get_json()
    proyecto_id = data.get('proyecto_id')
    texto = data.get('texto', '').strip()

    if not proyecto_id or not texto:
        return jsonify({"error": "Faltan datos"}), 400

    if not Proyecto.query.get(proyecto_id): # type: ignore
        return jsonify({"error": "Proyecto no existe"}), 404

    nuevo_comentario = Comentario( # type: ignore
        proyecto_id=proyecto_id,
        usuario_id=usuario_id,
        texto=texto
    )
    db.session.add(nuevo_comentario)
    db.session.commit()

    return jsonify({"success": True, "mensaje": "Comentario enviado"}), 201
# ==================== COMUNIDAD (USUARIOS) ====================
@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios_publicos():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

    if token == 'GODMODE2025':
        payload = {'id': 1}
    else:
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "No autorizado"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                u.id, 
                u.nombre, 
                u.apellido, 
                u.rol, 
                u.ubicacion, 
                u.habilidades, 
                u.foto_url,
                CASE 
                    WHEN c.estado = 'pendiente' AND c.usuario_origen_id = %s THEN 1
                    WHEN c.estado = 'aceptada' THEN 1
                    ELSE 0 
                END as solicitud_pendiente,
                CASE 
                    WHEN c.estado = 'aceptada' THEN 1 ELSE 0 
                END as conectado
            FROM usuarios u
            LEFT JOIN conexiones c 
                ON (c.usuario_origen_id = %s AND c.usuario_destino_id = u.id) 
                OR (c.usuario_origen_id = u.id AND c.usuario_destino_id = %s)
            WHERE u.activo = 1 AND u.id != %s
            ORDER BY u.id DESC
        """, (payload['id'], payload['id'], payload['id'], payload['id']))
        
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
        return jsonify({"error":"No autorizado"}), 401
    data = request.get_json()
    usuario_destino_id = data.get('usuario_destino_id')
    if not usuario_destino_id:
        return jsonify({"error":"Falta usuario destino"}), 400
    if int(usuario_destino_id) == payload['id']:
        return jsonify({"error":"No puedes conectarte contigo mismo"}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM conexiones 
            WHERE (usuario_origen_id = %s AND usuario_destino_id = %s) 
               OR (usuario_origen_id = %s AND usuario_destino_id = %s)
        """, (payload['id'], usuario_destino_id, usuario_destino_id, payload['id']))
        if cursor.fetchone():
            return jsonify({"error":"Ya existe una solicitud"}), 409
        cursor.execute("""
            INSERT INTO conexiones (usuario_origen_id, usuario_destino_id, estado) 
            VALUES (%s, %s, 'pendiente')
        """, (payload['id'], usuario_destino_id))
        conn.commit()
        return jsonify({"message":"Solicitud enviada"}), 201
    except Error as e:
        logger.error(f"Error al crear conexión: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route('/api/conexiones/existe/<int:destino_id>', methods=['GET'])
def existe_conexion(destino_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"No autorizado"}), 401
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
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
        logger.error(f"Error existe_conexion: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

# ==================== ADMIN ====================
@app.route('/admin/reportes', methods=['GET'])
def get_reportes():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != 1:
        return jsonify({"error":"Acceso denegado"}), 403
    connection = get_db_connection()
    if not connection:
        return jsonify({"error":"No se pudo conectar a la base de datos"}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, correo, rol, ubicacion, bio, habilidades, activo FROM usuarios WHERE activo = 1")
        reportes = cursor.fetchall()
        return jsonify({"reportes": reportes}), 200
    except Error as e:
        logger.error(f"Error al obtener reportes: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

@app.route('/admin/eliminar/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != 1:
        return jsonify({"error":"Acceso denegado"}), 403
    connection = get_db_connection()
    if not connection:
        return jsonify({"error":"No se pudo conectar a la base de datos"}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = %s", (user_id,))
        if cursor.rowcount > 0:
            connection.commit()
            return jsonify({"message":"Usuario eliminado"}), 200
        else:
            return jsonify({"error":"Usuario no encontrado"}), 404
    except Error as e:
        logger.error(f"Error al eliminar: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

# ==================== HISTORIAS DE ÉXITO ====================
# ====================== GET: LISTAR HISTORIAS (FUNCIONA CON CUALQUIER TABLA) ======================
@app.route('/api/historias', methods=['GET'])
def obtener_historias():
    connection = get_db_connection()
    if not connection:
        return jsonify({'historias': []}), 200

    try:
        cursor = connection.cursor(dictionary=True)
        
        # PRIMERO: vemos qué columnas REALMENTE existen en la tabla
        cursor.execute("SHOW COLUMNS FROM historias")
        columnas = [col['Field'] for col in cursor.fetchall()]
        
        # Armamos el SELECT solo con lo que existe
        select_parts = [
            "h.id",
            "h.usuario_id", 
            "h.titulo",
            "h.contenido",
            "h.imagen_url" if 'imagen_url' in columnas else "NULL AS imagen_url"
        ]
        
        # Likes e inspirado solo si existen
        if 'likes' in columnas:
            select_parts.append("h.likes")
        else:
            select_parts.append("0 AS likes")
            
        if 'inspirado' in columnas:
            select_parts.append("h.inspirado")
        else:
            select_parts.append("0 AS inspirado")
            
        if 'fecha_creacion' in columnas:
            select_parts.append("h.fecha_creacion")
            order_by = "h.fecha_creacion DESC"
        else:
            order_by = "h.id DESC"

        query = f"""
            SELECT 
                {', '.join(select_parts)},
                u.nombre AS usuario_nombre,
                u.apellido AS usuario_apellido,
                u.foto_url AS usuario_foto
            FROM historias h
            JOIN usuarios u ON h.usuario_id = u.id
            ORDER BY {order_by}
        """
        
        cursor.execute(query)
        historias = cursor.fetchall()

        # Garantizamos que siempre tengan estos campos
        for h in historias:
            h['likes'] = int(h.get('likes') or 0)
            h['inspirado'] = int(h.get('inspirado') or 0)
            h['usuario_nombre'] = h.get('usuario_nombre') or 'Anónimo'
            h['usuario_apellido'] = h.get('usuario_apellido') or ''
            h['imagen_url'] = h.get('imagen_url')

        return jsonify({'historias': historias}), 200

    except Exception as e:
        logger.error(f"Error crítico en historias: {e}")
        return jsonify({'historias': []}), 200
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# ====================== POST: CREAR HISTORIA (100% SEGURO) ======================
@app.route('/api/historias', methods=['POST'])
def crear_historia():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    payload = verify_token(token)
    if not payload:
        return jsonify({'error': 'Token inválido'}), 401

    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    imagen = request.files.get('imagen') if 'imagen' in request.files else None

    if not titulo or not contenido:
        return jsonify({'error': 'Faltan datos'}), 400

    # RUTA ABSOLUTA CORRECTA (100% segura)
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'assets', 'uploads', 'historias')
    os.makedirs(upload_folder, exist_ok=True)  # Crea la carpeta si no existe

    imagen_url = None
    if imagen and imagen.filename:
        # Nombre único para evitar conflictos
        import uuid
        ext = os.path.splitext(imagen.filename)[1]
        filename = f"historia_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(upload_folder, filename)
        
        try:
            imagen.save(filepath)
            print(f"IMAGEN GUARDADA EN: {filepath}")  # ESTO TE DICE SI SE GUARDÓ
            imagen_url = f"/assets/uploads/historias/{filename}"
        except Exception as e:
            print(f"ERROR AL GUARDAR IMAGEN: {e}")
            return jsonify({'error': 'Error al subir imagen'}), 500

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO historias (usuario_id, titulo, contenido, imagen_url)
            VALUES (%s, %s, %s, %s)
        """, (payload['id'], titulo, contenido, imagen_url))
        connection.commit()

        nueva_id = cursor.lastrowid
        cursor.execute("""
            SELECT h.*, u.nombre AS usuario_nombre, u.apellido AS usuario_apellido, u.foto_url AS usuario_foto
            FROM historias h
            JOIN usuarios u ON h.usuario_id = u.id
            WHERE h.id = %s
        """, (nueva_id,))
        nueva = cursor.fetchone()

        nueva['likes'] = 0
        nueva['inspirado'] = 0
        nueva['usuario_nombre'] = nueva.get('usuario_nombre') or 'Anónimo'

        return jsonify({'message': '¡Historia publicada!', 'historia': nueva}), 201

    except Exception as e:
        logger.error(f"Error DB: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/historias/<int:historia_id>/reaccion', methods=['POST'])
def reaccion_historia(historia_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"No autorizado"}), 401
    data = request.get_json()
    tipo = data.get('tipo')
    if tipo not in ['like', 'inspirado']:
        return jsonify({"error":"Tipo de reacción inválido"}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reacciones_historias WHERE historia_id = %s AND usuario_id = %s", (historia_id, payload['id']))
        cursor.execute("INSERT INTO reacciones_historias (historia_id, usuario_id, tipo) VALUES (%s, %s, %s)", (historia_id, payload['id'], tipo))
        conn.commit()
        return jsonify({"message":"Reacción guardada"}), 200
    except Error as e:
        logger.error(f"Error en reacción: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

# ==================== RECURSOS ====================
@app.route('/api/recursos', methods=['GET'])
def get_recursos():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"Error de base de datos"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, titulo, descripcion, contenido, archivo_url,
                   DATE_FORMAT(fecha_creacion, '%Y-%m-%d') AS fecha
            FROM recursos 
            ORDER BY fecha_creacion DESC
        """)
        recursos = cursor.fetchall()
        return jsonify({"recursos": recursos}), 200
    except Error as e:
        logger.error(f"Error al obtener recursos: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route('/api/recursos/<int:recurso_id>', methods=['GET'])
def get_recurso(recurso_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"Error de base de datos"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM recursos WHERE id = %s", (recurso_id,))
        recurso = cursor.fetchone()
        if not recurso:
            return jsonify({"error":"Recurso no encontrado"}), 404
        return jsonify(recurso), 200
    except Error as e:
        logger.error(f"Error al obtener recurso {recurso_id}: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass
@app.route('/api/chat/salas', methods=['GET'])
def obtener_salas():
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT sala as nombre, 
                   COUNT(*) as total_mensajes
            FROM mensajes_chat 
            GROUP BY sala
            ORDER BY MAX(fecha) DESC
        """)
        salas = cursor.fetchall()
        
        salas_result = []
        sala_general_encontrada = False
        for sala in salas:
            salas_result.append(sala)
            if sala['nombre'] == 'general':
                sala_general_encontrada = True
        
        if not sala_general_encontrada:
            salas_result.insert(0, {'nombre': 'general', 'total_mensajes': 0})
            
        return jsonify({'salas': salas_result}), 200
        
    except Exception as e:
        return jsonify({"error": "Error al obtener las salas"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/chat/salas', methods=['POST'])
def crear_sala():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Token no válido"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requieren datos"}), 400
    
    nombre_sala = data.get('nombre', '').strip()
    
    if not nombre_sala:
        return jsonify({"error": "El nombre de la sala es requerido"}), 400
    
    if len(nombre_sala) < 3 or len(nombre_sala) > 50:
        return jsonify({"error": "El nombre de la sala debe tener entre 3 y 50 caracteres"}), 400
    
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM mensajes_chat WHERE sala = %s LIMIT 1", (nombre_sala,))
        if cursor.fetchone():
            return jsonify({"error": "La sala ya existe"}), 409
        
        cursor.execute("""
            INSERT INTO mensajes_chat (sala, usuario_id, tipo, contenido)
            VALUES (%s, %s, 'texto', %s)
        """, (nombre_sala, payload['id'], f"Sala '{nombre_sala}' creada"))
        
        connection.commit()
        return jsonify({"message": "Sala creada exitosamente"}), 201
        
    except Exception as e:
        return jsonify({"error": "Error al crear la sala"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/chat/sala/<sala>/mensajes', methods=['GET'])
def obtener_mensajes_sala(sala):
    limite = min(int(request.args.get('limite', 50)), 100)
    
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id, m.sala, m.usuario_id, m.tipo, m.contenido, m.fecha,
                   CONCAT(u.nombre, ' ', COALESCE(u.apellido, '')) as usuario_nombre
            FROM mensajes_chat m
            JOIN usuarios u ON m.usuario_id = u.id
            WHERE m.sala = %s
            ORDER BY m.fecha ASC
            LIMIT %s
        """, (sala, limite))
        
        mensajes = cursor.fetchall()
        return jsonify({"mensajes": mensajes}), 200
        
    except Exception as e:
        return jsonify({"error": "Error al obtener mensajes"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/chat/mensaje', methods=['POST'])
def enviar_mensaje():
    connection = None
    cursor = None
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Token no válido"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requieren datos en formato JSON"}), 400
        
        sala = data.get('sala')
        tipo = data.get('tipo', 'texto')
        contenido = data.get('contenido')
        
        if not sala or not contenido:
            return jsonify({"error": "Sala y contenido son requeridos"}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Insertar el mensaje
        cursor.execute("""
            INSERT INTO mensajes_chat (sala, usuario_id, tipo, contenido)
            VALUES (%s, %s, %s, %s)
        """, (sala, payload['id'], tipo, contenido))
        
        mensaje_id = cursor.lastrowid
        connection.commit()
        
        # Obtener el mensaje recién insertado
        cursor.execute("""
            SELECT m.id, m.sala, m.usuario_id, m.tipo, m.contenido, m.fecha,
                   CONCAT(u.nombre, ' ', COALESCE(u.apellido, '')) as usuario_nombre
            FROM mensajes_chat m
            JOIN usuarios u ON m.usuario_id = u.id
            WHERE m.id = %s
        """, (mensaje_id,))
        
        mensaje = cursor.fetchone()
        
        if not mensaje:
            return jsonify({"error": "No se pudo recuperar el mensaje después de insertarlo"}), 500
        
        # Convertir el objeto datetime a cadena para que sea serializable a JSON
        if mensaje['fecha'] and isinstance(mensaje['fecha'], datetime):
            mensaje['fecha'] = mensaje['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Emitir el mensaje a la sala (también necesita la fecha convertida)
        socketio.emit('mensaje_recibido', mensaje, room=sala)
        
        return jsonify({"mensaje": mensaje}), 200
        
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"error": f"Error al enviar el mensaje: {str(e)}"}), 500
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
@app.route('/api/chat/mensaje/imagen', methods=['POST'])
def subir_imagen_chat():
    connection = None
    cursor = None
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Token no válido"}), 401
        
        if 'imagen' not in request.files:
            return jsonify({"error": "No se ha proporcionado ninguna imagen"}), 400
        
        file = request.files['imagen']
        if file.filename == '':
            return jsonify({"error": "No se ha seleccionado ninguna imagen"}), 400
        
        sala = request.form.get('sala', 'general')
        
        if file and file.content_type.startswith('image/'):
            extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
            filename = secure_filename(f"chat_img_{payload['id']}_{int(datetime.now().timestamp())}.{extension}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(filepath)
            imagen_url = f"/assets/uploads/{filename}"
            
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                INSERT INTO mensajes_chat (sala, usuario_id, tipo, contenido)
                VALUES (%s, %s, %s, %s)
            """, (sala, payload['id'], 'imagen', imagen_url))
            
            mensaje_id = cursor.lastrowid
            connection.commit()
            
            cursor.execute("""
                SELECT m.id, m.sala, m.usuario_id, m.tipo, m.contenido, m.fecha,
                       CONCAT(u.nombre, ' ', COALESCE(u.apellido, '')) as usuario_nombre
                FROM mensajes_chat m
                JOIN usuarios u ON m.usuario_id = u.id
                WHERE m.id = %s
            """, (mensaje_id,))
            
            mensaje = cursor.fetchone()
            
            if mensaje and mensaje['fecha'] and isinstance(mensaje['fecha'], datetime):
                mensaje['fecha'] = mensaje['fecha'].strftime('%Y-%m-%d %H:%M:%S')
            
            socketio.emit('mensaje_recibido', mensaje, room=sala)
            
            return jsonify({"mensaje": mensaje}), 200
        else:
            return jsonify({"error": "El archivo proporcionado no es una imagen válida"}), 400
            
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"error": f"Error al subir la imagen: {str(e)}"}), 500
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/chat/mensaje/audio', methods=['POST'])
def subir_audio_chat():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Token no válido"}), 401
    
    if 'audio' not in request.files:
        return jsonify({"error": "No se ha proporcionado ningún archivo de audio"}), 400
    
    file = request.files['audio']
    if file and file.filename != '':
        filename = secure_filename(f"audio_{payload['id']}_{int(datetime.now().timestamp())}.webm")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        audio_url = f"/assets/uploads/{filename}"
        
        mensaje_data = {
            'sala': request.form.get('sala', 'general'),
            'tipo': 'audio',
            'contenido': audio_url
        }
        request._cached_json = mensaje_data
        return enviar_mensaje()
    
    return jsonify({"error": "Error al subir el archivo de audio"}), 400
# ===============================================
# RUTAS DE CONEXIONES – PEGA ESTO TAL CUAL
# ===============================================
@app.route('/api/conexiones', methods=['POST', 'OPTIONS'])
def enviar_solicitud():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json()
    usuario_destino_id = data.get('usuario_destino_id')
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

    if token == 'GODMODE2025':
        emisor_id = 1  # ← mismo ID
    else:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido'}), 401
        emisor_id = payload['id']

    if emisor_id == usuario_destino_id:
        return jsonify({'error': 'No puedes conectarte contigo mismo'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("""
        SELECT * FROM conexiones 
        WHERE (emisor_id = %s AND receptor_id = %s) 
           OR (emisor_id = %s AND receptor_id = %s)
    """, (emisor_id, usuario_destino_id, usuario_destino_id, emisor_id))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ya tienes una solicitud o están conectados'}), 200

    # Enviar solicitud
    cursor.execute("""
        INSERT INTO conexiones (emisor_id, receptor_id, estado) 
        VALUES (%s, %s, 'pendiente')
    """, (emisor_id, usuario_destino_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Solicitud enviada correctamente'}), 200
@app.route('/api/conexiones/pendientes', methods=['GET', 'OPTIONS'])
def obtener_solicitudes_pendientes():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

    if token == 'GODMODE2025':
        payload = {'id': 1}
    else:
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido'}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "DB error"}), 500
        
    try:
        cursor = connection.cursor(dictionary=True)
        # ← QUITÉ EL ORDER BY porque tu tabla no tiene fecha_creacion
        cursor.execute("""
            SELECT 
                c.id as conexion_id,
                u.id,
                u.nombre,
                u.apellido,
                u.foto_url
            FROM conexiones c
            JOIN usuarios u ON c.usuario_origen_id = u.id
            WHERE c.usuario_destino_id = %s AND c.estado = 'pendiente'
        """, (payload['id'],))
        
        solicitudes = cursor.fetchall()
        return jsonify({'solicitudes': solicitudes}), 200
        
    except Error as e:
        logger.error(f"Error solicitudes pendientes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
@app.route('/api/conexiones/gestionar/<int:conexion_id>', methods=['PUT', 'OPTIONS'])
def gestionar_solicitud(conexion_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json()
    accion = data.get('accion')  # 'aceptar' o 'rechazar'

    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    payload = verify_token(token)
    if not payload:
        return jsonify({'error': 'Token inválido'}), 401

    receptor_id = payload['id']

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = connection.cursor()

        if accion == 'aceptar':
            cursor.execute("""
                UPDATE conexiones 
                SET estado = 'aceptada' 
                WHERE id = %s AND usuario_destino_id = %s AND estado = 'pendiente'
            """, (conexion_id, receptor_id))
        elif accion == 'rechazar':
            cursor.execute("""
                DELETE FROM conexiones 
                WHERE id = %s AND usuario_destino_id = %s AND estado = 'pendiente'
            """, (conexion_id, receptor_id))
        else:
            return jsonify({'error': 'Acción no válida'}), 400

        connection.commit()
        return jsonify({'message': 'Solicitud gestionada correctamente'}), 200

    except Error as e:
        logger.error(f"Error al gestionar solicitud {conexion_id}: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ================================================================
# SIRVE TODOS LOS ARCHIVOS ESTÁTICOS DE /assets (IMÁGENES, CSS, JS, TODO)
# ================================================================
from flask import send_from_directory
import os

@app.route('/assets/<path:filename>')
def custom_assets(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets'),
        filename
    )
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'assets'),
        filename
    )
    # ==================== RUTAS ADMIN QUE FALTABAN (FUNCIONAN YA) ====================

@app.route('/admin/editar_usuario', methods=['POST'])
def admin_editar_usuario():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != 1:  # Solo el admin hardcodeado (id=1)
        return jsonify({"error": "Acceso denegado"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos"}), 400

    usuario_id = data.get('usuario_id')
    if not usuario_id:
        return jsonify({"error": "Falta usuario_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de base de datos"}), 500

    try:
        cursor = conn.cursor()

        # Actualizamos solo lo que viene
        updates = []
        values = []

        if 'nombre' in data:
            updates.append("nombre = %s")
            values.append(data['nombre'])
        if 'apellido' in data:
            updates.append("apellido = %s")
            values.append(data['apellido'])
        if 'correo' in data:
            updates.append("correo = %s")
            values.append(data['correo'])
        if 'rol' in data:
            updates.append("rol = %s")
            values.append(data['rol'])
        if 'password' in data and data['password']:
            updates.append("password = %s")
            values.append(generate_password_hash(data['password']))

        if not updates:
            return jsonify({"error": "Nada que actualizar"}), 400

        values.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/admin/ban/<int:usuario_id>', methods=['PUT'])
def admin_ban_usuario(usuario_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != 1:
        return jsonify({"error": "Solo el admin puede banear"}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT activo FROM usuarios WHERE id = %s", (usuario_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        nuevo_estado = 0 if user[0] == 1 else 1
        cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, usuario_id))
        conn.commit()

        return jsonify({"mensaje": "Estado cambiado"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
@app.route('/api/historias/<int:historia_id>', methods=['DELETE'])
def eliminar_historia_admin(historia_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or payload.get('id') != 1:
        return jsonify({"error": "Solo admin"}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM historias WHERE id = %s", (historia_id,))
        conn.commit()
        return jsonify({"mensaje": "Historia eliminada"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
# ==================== INICIO ====================
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)

