import pytest
import requests
import json

# Configuración global
API_URL = "http://localhost:5000"
NEW_USER = {"nombre": "Prueba", "apellido": "Usuario", "correo": "pruebausuario@example.com", "password": "Prueba1234", "rol": "emprendedor", "ubicacion": "Cali", "bio": "Usuario para pruebas", "habilidades": "pruebas,creatividad"}
EXISTING_USER = {"correo": "admin@conecta-crece.com", "password": "admin123"}  # Ajusta según tu usuario existente

def test_backend_connectivity():
    response = requests.get(f"{API_URL}/api/proyectos")
    assert response.status_code == 200, f"Conectividad falló: {response.text}"
    assert len(response.json()) >= 0, "No se devolvieron datos de proyectos"

def test_registration():
    response = requests.post(f"{API_URL}/registro", json=NEW_USER)
    assert response.status_code == 201, f"Registro falló: {response.text}"
    assert "Usuario registrado exitosamente" in response.json().get("message", "")

def test_login():
    response = requests.post(f"{API_URL}/login", json=EXISTING_USER)
    assert response.status_code == 200, f"Login falló: {response.text}"
    assert "Inicio de sesión exitoso" in response.json().get("message", "")

# Nota: Limpieza opcional para evitar duplicados (descomentar si necesario)
# def test_cleanup():
#     response = requests.delete(f"{API_URL}/admin/eliminar/1", headers={"Authorization": "Bearer admin123"})  # Ajusta user_id
#     assert response.status_code == 200, f"Limpieza falló: {response.text}"