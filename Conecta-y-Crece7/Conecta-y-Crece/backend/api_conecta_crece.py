# api_conecta_crece.py
# ==================== API CONECTA Y CRECE - VERSIÓN FINAL (ACTUALIZADA) ====================
# Autor: Zack Sandon (adaptada)
# Fecha: 10 de noviembre de 2025 (actualizado)
# NOTA: Este archivo mantiene tu estructura original; se agregaron y corrigieron endpoints.

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
from datetime import datetime, timedelta

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

app = Flask(__name__)

# ==================== CORS ====================
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ==================== CONFIG JWT Y FOTOS ====================
SECRET_KEY = os.environ.get('SECRET_KEY', "conecta_y_crece_2025_sena")
app.config['SECRET_KEY'] = SECRET_KEY

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'assets', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_token(user_id):
    payload = {
        'id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    if jwt and hasattr(jwt, 'encode'):
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # PyJWT >=2 returns str, <=1 returns bytes
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token
    else:
        # Si no hay PyJWT instalado o encode no disponible, avisar en logs y lanzar excepción clara
        logger.error("PyJWT no está disponible o no tiene 'encode'. Instala 'PyJWT' (pip install PyJWT).")
        raise RuntimeError("JWT encode not available. Install PyJWT (pip install PyJWT).")

def verify_token(token):
    if not token:
        return None
    if jwt and hasattr(jwt, 'decode'):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except Exception as e:
            logger.warning(f"Token inválido: {e}")
            return None
    else:
        logger.error("PyJWT no está disponible o no tiene 'decode'.")
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
@app.route('/assets/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

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
                   COALESCE(p.progreso, 0) AS progreso,
                   p.usuario_id,
                   p.imagen_principal_url, p.video_pitch_url,
                   p.sitio_web, p.contacto, p.telefono_proyecto, redes_sociales
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
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

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
         sitio_web, telefono_proyecto, whatsapp, instagram, facebook, linkedin, fecha_creacion)
        VALUES (%s,%s,%s,%s,%s,%s,'borrador',1, %s,%s,%s, %s,%s,%s,%s,%s,%s, NOW())
    """, (payload['id'], titulo, descripcion, descripcion_larga, categoria_id, progreso,
          imagen_url, video_url, pdf_url, sitio_web, telefono_proyecto,
          whatsapp, instagram, facebook, linkedin))
    conn.commit()
    conn.close()
    return jsonify({"message": "Proyecto creado", "id": cursor.lastrowid}), 201

@app.route('/api/proyectos/<int:proyecto_id>', methods=['GET'])
def detalle_proyecto(proyecto_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"DB error"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.titulo, p.descripcion, p.usuario_id, p.categoria_id,
                   COALESCE(c.nombre, 'Sin categoría') AS categoria,
                   CONCAT(u.nombre, ' ', u.apellido) AS emprendedor,
                   p.fecha_inicio AS fecha, COALESCE(p.progreso,0) AS progreso,
                   p.imagen_principal_url, p.video_pitch_url, p.sitio_web, p.contacto,
                   p.telefono_proyecto, redes_sociales
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = %s AND p.activo = 1
        """, (proyecto_id,))
        proyecto = cursor.fetchone()
        if not proyecto:
            return jsonify({"error":"Proyecto no encontrado"}), 404
        return jsonify(proyecto), 200
    except Error as e:
        logger.error(f"Error detalle proyecto: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass
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

# ==================== COMUNIDAD (USUARIOS) ====================
@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios_publicos():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"No autorizado"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error":"No se pudo conectar a la base de datos"}), 500
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
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except:
            pass

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
@app.route('/api/historias', methods=['GET'])
def get_historias():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"Error de base de datos"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT h.id, h.titulo, h.contenido, h.imagen_url,
                   CONCAT(u.nombre, ' ', u.apellido) AS autor,
                   u.nombre AS usuario_nombre,
                   u.apellido AS usuario_apellido,
                   SUBSTRING(h.contenido, 1, 100) AS resumen,
                   COALESCE(SUM(CASE WHEN rh.tipo='like' THEN 1 ELSE 0 END), 0) AS likes,
                   COALESCE(SUM(CASE WHEN rh.tipo='inspirado' THEN 1 ELSE 0 END), 0) AS inspirado
            FROM historias h
            JOIN usuarios u ON h.usuario_id = u.id
            LEFT JOIN reacciones_historias rh ON h.id = rh.historia_id
            WHERE h.aprobada = 1
            GROUP BY h.id
            ORDER BY h.fecha DESC
        """)
        historias = cursor.fetchall()
        return jsonify({"historias": historias}), 200
    except Error as e:
        logger.error(f"Error al obtener historias: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route('/api/historias', methods=['POST'])
def crear_historia():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"No autorizado"}), 401
    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    if not titulo or not contenido:
        return jsonify({"error":"Faltan título o contenido"}), 400
    imagen_url = None
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"hist_{payload['id']}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            imagen_url = f"/assets/uploads/{filename}"
    conn = get_db_connection()
    if not conn:
        return jsonify({"error":"Error de base de datos"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historias (usuario_id, titulo, contenido, imagen_url, aprobada, fecha)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (payload['id'], titulo, contenido, imagen_url, 0))
        conn.commit()
        historia_id = cursor.lastrowid
        logger.info(f"Historia enviada para aprobación: {historia_id}")
        return jsonify({
            "message":"Historia enviada para aprobación",
            "id": historia_id,
            "autor": f"{payload.get('nombre','')} {payload.get('apellido','')}".strip()
        }), 201
    except Error as e:
        logger.error(f"Error al crear historia: {e}")
        return jsonify({"error":str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

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

# ==================== INICIO ====================
if __name__ == '__main__':
    logger.info("API Conecta y Crece iniciada - ¡Listo para exponer!")
    app.run(debug=True, host='0.0.0.0', port=5000)
