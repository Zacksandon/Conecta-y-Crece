# backend/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

# Inicializamos las extensiones (sin app aún)
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # ==================== CONFIGURACIÓN ====================
    app.config['SECRET_KEY'] = 'tu_clave_super_secreta_aqui_cambiala'  # CAMBIA ESTO
    app.config['JWT_SECRET_KEY'] = 'jwt_clave_muy_segura_cambiala_ya'   # CAMBIA ESTO
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conectaycrece.db'  # o tu DB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ==================== INICIAMOS EXTENSIONES ====================
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)  # permite que el frontend en localhost:3000 o 5000 hable con el backend

    # ==================== IMPORTAMOS MODELOS Y RUTAS ====================
    # Modelos
    from models import Usuario, Proyecto, Historia  # ajusta si tus archivos se llaman diferente

    # Rutas
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.proyectos import proyectos_bp
    from routes.historias import historias_bp
    # agrega aquí las demás rutas que tengas

    # Registramos los blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(proyectos_bp)
    app.register_blueprint(historias_bp)

    # ==================== CREAR TABLAS SI NO EXISTEN ====================
    with app.app_context():
        db.create_all()  # solo en desarrollo, quítalo en producción

    return app