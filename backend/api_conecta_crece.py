from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import mysql.connector as mysql
from mysql.connector import Error
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt

# Añadir ruta al directorio padre para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar configuración de la base de datos desde config.py
from backend.config import DB_CONFIG

app = Flask(__name__)
CORS(app, resources={
    r"/login": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/registro": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/admin/reportes": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/admin/eliminar/*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/proyectos*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/reacciones*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500", "file://"], "allow_headers": ["Content-Type", "Authorization"]}
}, supports_credentials=True)

bcrypt = Bcrypt(app)

def get_db_connection():
    try:
        connection = mysql.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# Registro de usuario con hash de contraseña
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

        # Validar datos requeridos
        if not all([nombre, apellido, correo, password]):
            return jsonify({"error": "Faltan datos requeridos: nombre, apellido, correo o password"}), 400

        # Validar rol
        if rol not in ['emprendedor', 'mentor', 'inversor']:
            return jsonify({"error": "Rol no válido. Debe ser 'emprendedor', 'mentor' o 'inversor'"}), 400

        cursor = connection.cursor()
        hashed_password = generate_password_hash(password)
        consulta = "INSERT INTO usuarios (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        valores = (nombre, apellido, correo, hashed_password, rol, ubicacion, bio, habilidades)

        cursor.execute(consulta, valores)
        connection.commit()
        return jsonify({"message": "Usuario registrado exitosamente", "id": cursor.lastrowid}), 201

    except Error as e:
        if "Duplicate entry" in str(e):  # Manejar duplicado de correo
            return jsonify({"error": "El correo ya está registrado"}), 409
        return jsonify({"error": f"Error al registrar usuario: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

# Login de usuario
@app.route('/login', methods=['POST'])
def login_usuario():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        correo = data.get('correo')
        password = data.get('password')

        if not all([correo, password]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        cursor = connection.cursor(dictionary=True)
        consulta = "SELECT id, nombre, apellido, rol, password FROM usuarios WHERE correo = %s AND activo = 1"
        cursor.execute(consulta, (correo,))
        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario['password'], password):
            del usuario['password']  # No enviar la contraseña hasheada
            response = {"message": "Inicio de sesión exitoso", "usuario": usuario}
            if correo == 'admin@conecta-crece.com':
                response["redirect"] = "admin.html"
            return jsonify(response), 200
        else:
            return jsonify({"error": "Correo o contraseña incorrectos"}), 401

    except Error as e:
        return jsonify({"error": f"Error al iniciar sesión: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Listar proyectos
@app.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        consulta = """
            SELECT p.id, p.titulo, p.descripcion, c.nombre AS categoria, u.nombre AS emprendedor, p.fecha_inicio AS fecha, p.progreso
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            JOIN categorias c ON p.categoria_id = c.id
            WHERE p.estado = 'activo'
        """
        cursor.execute(consulta)
        proyectos = cursor.fetchall()
        return jsonify(proyectos), 200

    except Error as e:
        return jsonify({"error": f"Error al obtener proyectos: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Obtener detalles de un proyecto
@app.route('/api/proyectos/<int:id>', methods=['GET'])
def get_proyecto(id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        consulta = """
            SELECT p.id, p.titulo, p.descripcion, c.nombre AS categoria, u.nombre AS emprendedor, p.fecha_inicio AS fecha, p.progreso
            FROM proyectos p
            JOIN usuarios u ON p.usuario_id = u.id
            JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = %s AND p.estado = 'activo'
        """
        cursor.execute(consulta, (id,))
        proyecto = cursor.fetchone()
        if proyecto:
            return jsonify(proyecto), 200
        else:
            return jsonify({"error": "Proyecto no encontrado"}), 404
    except Error as e:
        return jsonify({"error": f"Error al obtener proyecto: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Crear un proyecto
@app.route('/api/proyectos', methods=['POST'])
def create_proyecto():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        usuario_id = data.get('usuario_id')
        titulo = data.get('titulo')
        descripcion = data.get('descripcion')
        categoria_id = data.get('categoria_id')
        fecha_inicio = data.get('fecha_inicio')
        progreso = data.get('progreso', 0)

        if not all([usuario_id, titulo, descripcion, categoria_id, fecha_inicio]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        # Validar progreso
        if not isinstance(progreso, int) or progreso < 0 or progreso > 100:
            return jsonify({"error": "El progreso debe ser un número entre 0 y 100"}), 400

        cursor = connection.cursor()
        consulta = """
            INSERT INTO proyectos (usuario_id, titulo, descripcion, categoria_id, fecha_inicio, progreso, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'activo')
        """
        valores = (usuario_id, titulo, descripcion, categoria_id, fecha_inicio, progreso)

        cursor.execute(consulta, valores)
        connection.commit()
        return jsonify({"message": "Proyecto creado exitosamente", "id": cursor.lastrowid}), 201

    except Error as e:
        return jsonify({"error": f"Error al crear proyecto: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Registrar una reacción
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
            return jsonify({"error": "Faltan datos requeridos"}), 400

        if tipo_reaccion not in ['me-gusta', 'me-encanta', 'me-interesa', 'apoyo']:
            return jsonify({"error": "Tipo de reacción no válido"}), 400

        cursor = connection.cursor()
        consulta = "INSERT INTO reacciones (proyecto_id, usuario_id, tipo_reaccion) VALUES (%s, %s, %s)"
        valores = (proyecto_id, usuario_id, tipo_reaccion)

        cursor.execute(consulta, valores)
        connection.commit()
        return jsonify({"message": "Reacción registrada"}), 201

    except Error as e:
        return jsonify({"error": f"Error al registrar reacción: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Obtener conteo de reacciones
@app.route('/api/reacciones/<int:proyecto_id>', methods=['GET'])
def get_reacciones(proyecto_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        consulta = """
            SELECT tipo_reaccion, COUNT(*) as count 
            FROM reacciones 
            WHERE proyecto_id = %s 
            GROUP BY tipo_reaccion
        """
        cursor.execute(consulta, (proyecto_id,))
        reacciones = cursor.fetchall()
        counts = {r['tipo_reaccion']: r['count'] for r in reacciones}
        return jsonify(counts), 200
    except Error as e:
        return jsonify({"error": f"Error al obtener reacciones: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Reportes de admin
@app.route('/admin/reportes', methods=['GET'])
def get_reportes():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != 'Bearer admin123':
        return jsonify({"error": "Acceso denegado"}), 403

    try:
        cursor = connection.cursor(dictionary=True)
        consulta = """
        SELECT id, nombre, apellido, correo, rol, ubicacion, bio, habilidades, activo
        FROM usuarios
        WHERE activo = 1
        ORDER BY id DESC;
        """
        cursor.execute(consulta)
        reportes = cursor.fetchall()

        if reportes:
            return jsonify({"reportes": reportes}), 200
        else:
            return jsonify({"message": "No hay usuarios registrados"}), 404

    except Error as e:
        return jsonify({"error": f"Error al obtener reportes: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Eliminar usuario (marcar como inactivo)
@app.route('/admin/eliminar/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != 'Bearer admin123':
        return jsonify({"error": "Acceso denegado"}), 403

    try:
        cursor = connection.cursor()
        consulta = "UPDATE usuarios SET activo = 0 WHERE id = %s"
        cursor.execute(consulta, (user_id,))
        if cursor.rowcount > 0:
            connection.commit()
            return jsonify({"message": "Usuario eliminado exitosamente"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404

    except Error as e:
        return jsonify({"error": f"Error al eliminar usuario: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

# Actualizar perfil de usuario
@app.route('/actualizar', methods=['PUT'])
def actualizar_usuario():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        user_id = data.get('id')
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        correo = data.get('correo')
        ubicacion = data.get('ubicacion')
        bio = data.get('bio')
        habilidades = data.get('habilidades')
        experiencia = data.get('experiencia')
        intereses = data.get('intereses')

        if not all([user_id, nombre, apellido, correo, ubicacion, bio, habilidades]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        cursor = connection.cursor()
        consulta = """
            UPDATE usuarios 
            SET nombre = %s, apellido = %s, correo = %s, ubicacion = %s, bio = %s, habilidades = %s, experiencia = %s, intereses = %s
            WHERE id = %s
        """
        valores = (nombre, apellido, correo, ubicacion, bio, habilidades, experiencia, intereses, user_id)

        cursor.execute(consulta, valores)
        connection.commit()
        return jsonify({"message": "Perfil actualizado exitosamente"}), 200

    except Error as e:
        return jsonify({"error": f"Error al actualizar perfil: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)