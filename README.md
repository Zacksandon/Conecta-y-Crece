# Conecta y Crece

**Red social para emprendedores** que conecta ideas, proyectos, mentores e inversores en un solo lugar.  
**"Tu idea crece cuando se conecta."**

## Descripción del Proyecto

**Conecta y Crece** es una plataforma colaborativa para:
- Publicar y descubrir proyectos emprendedores  
- Conectar con mentores e inversores  
- Reaccionar, comentar y hacer seguimiento  
- Generar reportes de impacto (inversión, crecimiento, red)

---

## Tecnologías Utilizadas (Stack)

| Capa | Tecnología |
|------|------------|
| **Backend** | Python 3.13, Flask, Flask-CORS |
| **Base de Datos** | MySQL 8.0 (relacional) + MongoDB (NoSQL) |
| **Autenticación** | Bcrypt, JWT |
| **Frontend** | React.js, Tailwind CSS |
| **Control de Versiones** | Git + GitHub |
| **Calidad de Código** | `black`, `flake8`, `pre-commit` |
| **Documentación** | Docstrings, Swagger API, README |
| **Entorno** | Docker (opcional), VS Code |

---

## Requisitos de Instalación

```bash
# Python
Python 3.14 o superior

# Base de datos
MySQL 8.0


# Herramientas
Git


## Instalación y Configuración

# 1. Clonar el repositorio
git clone https://github.com/zack-sandon/conecta-y-crece.git
cd conecta-y-crece

# 2. Backend: Instalar dependencias
pip install -r backend/requirements.txt

# 3. Frontend: Instalar dependencias
cd frontend
npm install
cd ..

# 4. Configurar variables de entorno
cp backend/.env.example backend/.env
# Edita .env con:
# DB_HOST=localhost
# DB_USER=root
# DB_PASS=tu_password
# SECRET_KEY=tu_clave_secreta

## Ejecución del Proyecto
 cd backend
python api_conecta_crece.py
  
## Frontend: Se ejecuta con live server que es una extension en Visual Code 