-- =====================================================
-- BASE DE DATOS CONECTA & CRECE - VERSIÓN FINAL DEFINITIVA
-- 100% COMPATIBLE CON TU API FLASK (2025)
-- Copia y pega TODO esto de una sola vez
-- =====================================================

DROP DATABASE IF EXISTS conecta_crece;
CREATE DATABASE conecta_crece CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE conecta_crece;

-- 1. USUARIOS (exactamente como los usa tu API)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    rol ENUM('emprendedor','administrador','mentor','inversor') NOT NULL DEFAULT 'emprendedor',
    ubicacion VARCHAR(150),
    bio TEXT,
    habilidades TEXT,
    experiencia_años INT DEFAULT 0,
    sitio_web VARCHAR(200),
    linkedin VARCHAR(200),
    twitter VARCHAR(200),
    instagram VARCHAR(200),
    foto_url VARCHAR(300),
    verificado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actividad DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    preferencias_notificaciones JSON,
    pais VARCHAR(100),
    industria_preferida VARCHAR(100),
    INDEX idx_correo (correo),
    INDEX idx_rol (rol),
    INDEX idx_activo (activo)
);

-- 2. CATEGORÍAS
CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo ENUM('proyecto','recurso','evento','curso') NOT NULL,
    UNIQUE KEY uniq_nombre_tipo (nombre, tipo)
);

-- 3. PROYECTOS (100% compatible con tu crear/editar proyecto)
CREATE TABLE proyectos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    descripcion_larga TEXT,
    categoria_id INT,
    monto_objetivo DECIMAL(15,2),
    monto_recaudado DECIMAL(15,2) DEFAULT 0.00,
    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_fin DATETIME,
    estado ENUM('borrador','publicado','finalizado') DEFAULT 'borrador',
    progreso INT DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    imagen_principal_url VARCHAR(300),
    video_pitch_url VARCHAR(300),
    catalogo_pdf_url VARCHAR(300),
    sitio_web VARCHAR(300),
    telefono_proyecto VARCHAR(50),
    whatsapp VARCHAR(50),
    instagram VARCHAR(300),
    facebook VARCHAR(300),
    twitter VARCHAR(300),
    linkedin VARCHAR(300),
    redes JSON,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
);

-- 4. ALIANZAS / INVERSIONES
CREATE TABLE proyecto_alianzas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NOT NULL,
    participante_id INT NOT NULL,
    rol_alianza ENUM('inversor','mentor','colaborador') NOT NULL,
    monto_invertido DECIMAL(15,2) DEFAULT 0.00,
    fecha_alianza DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente','aprobada','rechazada') DEFAULT 'pendiente',
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (participante_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_alianza (proyecto_id, participante_id, rol_alianza)
);

-- 5. COMENTARIOS Y REACCIONES
CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NOT NULL,
    usuario_id INT NOT NULL,
    texto TEXT NOT NULL,
    padre_id INT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (padre_id) REFERENCES comentarios(id) ON DELETE CASCADE
);

CREATE TABLE reacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NULL,
    comentario_id INT NULL,
    usuario_id INT NOT NULL,
    tipo ENUM('me_gusta','me_encanta','me_interesa','apoyo') NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (comentario_id) REFERENCES comentarios(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT chk_solo_uno CHECK ((proyecto_id IS NOT NULL AND comentario_id IS NULL) OR (proyecto_id IS NULL AND comentario_id IS NOT NULL))
);

-- 6. CONEXIONES (tipo LinkedIn - exactamente como tu API)
CREATE TABLE conexiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_origen_id INT NOT NULL,
    usuario_destino_id INT NOT NULL,
    estado ENUM('pendiente','aceptada','rechazada') DEFAULT 'pendiente',
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_origen_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_destino_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_conexion (usuario_origen_id, usuario_destino_id)
);

-- 7. HISTORIAS (Stories + Reacciones)
CREATE TABLE historias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200),
    contenido TEXT,
    imagen_url VARCHAR(300),
    video_url VARCHAR(300),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiracion DATETIME DEFAULT (DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 24 HOUR)),
    aprobada TINYINT DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE reacciones_historias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    historia_id INT NOT NULL,
    usuario_id INT NOT NULL,
    tipo ENUM('like','inspirado') NOT NULL,
    FOREIGN KEY (historia_id) REFERENCES historias(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 8. CHAT EN TIEMPO REAL (100% compatible con tu SocketIO)
CREATE TABLE mensajes_chat (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sala VARCHAR(100) NOT NULL,
    usuario_id INT NOT NULL,
    tipo ENUM('texto','imagen','audio','documento') NOT NULL DEFAULT 'texto',
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_sala_fecha (sala, fecha DESC)
);

-- 9. NOTIFICACIONES
CREATE TABLE notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo ENUM('alianza','comentario','evento','curso','mensaje','conexion','historia') NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    mensaje TEXT NOT NULL,
    url VARCHAR(300),
    leida BOOLEAN DEFAULT FALSE,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 10. RECURSOS, CURSOS, EVENTOS, etc. (todos los que ya tenías)
CREATE TABLE recursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_id INT,
    url VARCHAR(300) NOT NULL,
    tipo ENUM('guia','plantilla','herramienta','otro') NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
);

-- =========================================
-- TODOS TUS DATOS DE PRUEBA (EXACTOS)
-- =========================================

INSERT INTO usuarios (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades, experiencia_años, pais, industria_preferida, telefono, foto_url, verificado) VALUES
('Juan', 'Pérez', 'juan@example.com', '$2y$10$examplehash123', 'emprendedor', 'Bogotá', 'Emprendedor apasionado.', 'Desarrollo web', 3, 'Colombia', 'Tecnología', '3001234567', '/assets/uploads/juan.jpg', 1),
('Ana', 'García', 'ana@example.com', '$2y$10$examplehash456', 'inversor', 'Medellín', 'Inversora experimentada.', 'Finanzas', 5, 'Colombia', 'Finanzas', '3109876543', '/assets/uploads/ana.jpg', 1),
('Luis', 'Martínez', 'luis@example.com', '$2y$10$examplehash789', 'emprendedor', 'Cali', 'Desarrollador de apps.', 'Móvil', 2, 'Colombia', 'Tecnología', NULL, NULL, 0),
('María', 'López', 'maria@example.com', '$2y$10$examplehash012', 'inversor', 'Barranquilla', 'Inversora en innovación.', 'Inversiones', 4, 'Colombia', 'Innovación', NULL, NULL, 1),
('Carlos', 'Rodríguez', 'carlos@example.com', '$2y$10$examplehash345', 'mentor', 'Bogotá', 'Mentor de startups.', 'Mentoría', 7, 'Colombia', 'Tecnología', NULL, NULL, 1),
('Sofía', 'Hernández', 'sofia@example.com', '$2y$10$examplehash678', 'emprendedor', 'Medellín', 'Emprendedora social.', 'Social', 1, 'Colombia', 'Educación', NULL, NULL, 0),
('Admin', 'Sistema', 'admin@conecta-crece.com', '$2y$10$adminhash2025', 'administrador', 'Bogotá', 'Administrador del sistema', 'Todo', 20, 'Colombia', 'Educación', NULL, '/assets/uploads/admin.jpg', 1);

INSERT INTO categorias (nombre, descripcion, tipo) VALUES
('Tecnología', 'Proyectos de software y hardware', 'proyecto'),
('Finanzas', 'Proyectos financieros y fintech', 'proyecto'),
('Educación', 'Proyectos educativos y e-learning', 'proyecto'),
('Salud', 'Proyectos de salud y bienestar', 'proyecto'),
('Guía de Marketing', 'Guías para marketing digital', 'recurso'),
('Curso React', 'Cursos de desarrollo web', 'curso'),
('Evento Startup', 'Eventos de startups', 'evento');

INSERT INTO proyectos (usuario_id, titulo, descripcion, descripcion_larga, categoria_id, monto_objetivo, monto_recaudado, fecha_fin, estado, progreso, imagen_principal_url, video_pitch_url, catalogo_pdf_url, telefono_proyecto, whatsapp, instagram, facebook, twitter, linkedin, sitio_web, redes) VALUES
(1, 'Tienda de Ropa Zack Style', 'Ropa urbana premium', 'Catálogo completo 2025 con más de 100 diseños...', 1, 50000000.00, 42000000.00, '2025-12-31', 'publicado', 85, '/assets/uploads/ropa.jpg', '/assets/uploads/pitch.mp4', '/assets/uploads/catalogo.pdf', '3001234567', '573001234567', 'https://instagram.com/zackstyle', 'https://facebook.com/zackstyle', 'https://twitter.com/zackstyle', 'https://linkedin.com/zackstyle', 'https://zackstyle.com', '{"tiktok":"zackstyle"}');

select * from usuarios;

CREATE TABLE IF NOT EXISTS eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATETIME NOT NULL,
    modalidad ENUM('online','presencial','hibrido') DEFAULT 'online',
    ubicacion VARCHAR(255),
    tipo VARCHAR(100),
    cupos_totales INT DEFAULT 0,
    enlace_externo VARCHAR(255),
    creador_id INT NOT NULL,
    activo TINYINT(1) DEFAULT 1,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS eventos_registros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id INT NOT NULL,
    usuario_id INT NOT NULL,
    estado ENUM('confirmado','cancelado') DEFAULT 'confirmado',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_evento_usuario (evento_id, usuario_id),
    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proyectos_fijados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_usuario_proyecto (usuario_id, proyecto_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
);