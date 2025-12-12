-- Eliminar base de datos si existe y crearla
DROP DATABASE IF EXISTS conecta_crece;
CREATE DATABASE conecta_crece CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE conecta_crece;

-- Tabla usuarios (base principal para todos los roles)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL, -- Almacena contraseñas hasheadas
    telefono VARCHAR(20),
    rol ENUM('emprendedor', 'administrador', 'mentor', 'inversor') NOT NULL DEFAULT 'emprendedor',
    ubicacion VARCHAR(150),
    bio TEXT,
    habilidades TEXT,
    experiencia_años INT DEFAULT 0 CHECK (experiencia_años >= 0),
    sitio_web VARCHAR(200),
    linkedin VARCHAR(200),
    twitter VARCHAR(200),
    foto_perfil VARCHAR(300), -- Ruta a la foto de perfil
    verificado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actividad DATETIME DEFAULT CURRENT_TIMESTAMP,
    preferencias_notificaciones JSON, -- Preferencias (ej. {"email": true, "push": false})
    pais VARCHAR(100),
    industria_preferida VARCHAR(100),
    INDEX idx_correo (correo),
    INDEX idx_rol (rol),
    INDEX idx_ubicacion (ubicacion),
    INDEX idx_fecha_registro (fecha_registro),
    INDEX idx_industria_preferida (industria_preferida)
);

-- Tabla categorias (para proyectos, recursos, eventos, etc.)
CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo ENUM('proyecto', 'recurso', 'evento', 'curso') NOT NULL, -- Tipo para categorizar usos
    INDEX idx_nombre (nombre),
    INDEX idx_tipo (tipo)
);

-- Tabla proyectos (publicación de proyectos por emprendedores)
CREATE TABLE proyectos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_id INT,
    monto_objetivo DECIMAL(15,2),
    monto_recaudado DECIMAL(15,2) DEFAULT 0.00,
    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_fin DATETIME,
    estado ENUM('borrador', 'publicado', 'finalizado') NOT NULL DEFAULT 'borrador',
    activo BOOLEAN DEFAULT TRUE,
    progreso INT DEFAULT 0,
    descripcion_larga TEXT,
    imagen_principal_url VARCHAR(255) NULL,
    video_pitch_url VARCHAR(255) NULL,
    catalogo_pdf_url VARCHAR(255) NULL,
    sitio_web VARCHAR(255) NULL,
    contacto VARCHAR(255) NULL,
    telefono_proyecto VARCHAR(50) NULL,
    whatsapp VARCHAR(50) NULL,
    instagram VARCHAR(255) NULL,
    facebook VARCHAR(255) NULL,
    twitter VARCHAR(255) NULL,
    linkedin VARCHAR(255) NULL,
    redes JSON NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_categoria_id (categoria_id),
    INDEX idx_estado (estado),
    INDEX idx_fecha_inicio (fecha_inicio)
);

-- Tabla proyecto_alianzas (alianzas, inversiones, mentorías)
CREATE TABLE proyecto_alianzas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NOT NULL,
    participante_id INT NOT NULL,
    rol_alianza ENUM('inversor', 'mentor', 'colaborador') NOT NULL,
    monto_invertido DECIMAL(15,2) DEFAULT 0.00,
    fecha_alianza DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente', 'aprobada', 'rechazada') NOT NULL DEFAULT 'pendiente',
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (participante_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_proyecto_id (proyecto_id),
    INDEX idx_participante_id (participante_id),
    INDEX idx_rol_alianza (rol_alianza),
    INDEX idx_estado (estado)
);

-- Tabla comentarios (comentarios y reacciones en proyectos)
CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NOT NULL,
    usuario_id INT NOT NULL,
    texto TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    padre_id INT, -- Para comentarios anidados
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (padre_id) REFERENCES comentarios(id) ON DELETE CASCADE,
    INDEX idx_proyecto_id (proyecto_id),
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_padre_id (padre_id),
    INDEX idx_fecha (fecha)
);

-- Tabla reacciones (reacciones en proyectos y comentarios)
CREATE TABLE reacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT,
    comentario_id INT,
    usuario_id INT NOT NULL,
    tipo ENUM('me_gusta', 'me_encanta', 'me_interesa', 'apoyo') NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
    FOREIGN KEY (comentario_id) REFERENCES comentarios(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_proyecto_id (proyecto_id),
    INDEX idx_comentario_id (comentario_id),
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_tipo (tipo)
);

-- Tabla eventos (gestión de eventos)
CREATE TABLE eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha DATETIME NOT NULL,
    ubicacion VARCHAR(150),
    categoria_id INT,
    capacidad INT DEFAULT 100 CHECK (capacidad > 0),
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_fecha (fecha),
    INDEX idx_categoria_id (categoria_id)
);

-- Tabla inscripciones_eventos (inscripciones a eventos)
CREATE TABLE inscripciones_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inscripcion (evento_id, usuario_id),
    INDEX idx_evento_id (evento_id),
    INDEX idx_usuario_id (usuario_id)
);

-- Tabla recursos (biblioteca de recursos, guías, plantillas)
CREATE TABLE recursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_id INT,
    url VARCHAR(300) NOT NULL, -- Enlace para descargar o ver
    tipo ENUM('guia', 'plantilla', 'herramienta', 'otro') NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_categoria_id (categoria_id),
    INDEX idx_tipo (tipo),
    INDEX idx_fecha_subida (fecha_subida)
);

-- Tabla cursos (acceso a cursos online)
CREATE TABLE cursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_id INT,
    url VARCHAR(300) NOT NULL, -- Enlace al curso
    duracion INT, -- En horas
    nivel ENUM('basico', 'intermedio', 'avanzado') NOT NULL DEFAULT 'basico',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_categoria_id (categoria_id),
    INDEX idx_nivel (nivel)
);

-- Tabla inscripciones_cursos (inscripciones a cursos)
CREATE TABLE inscripciones_cursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    curso_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    progreso DECIMAL(5,2) DEFAULT 0.00 CHECK (progreso BETWEEN 0 AND 100),
    completado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inscripcion (curso_id, usuario_id),
    INDEX idx_curso_id (curso_id),
    INDEX idx_usuario_id (usuario_id)
);

-- Tabla notificaciones (sistema de notificaciones)
CREATE TABLE notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo ENUM('alianza', 'comentario', 'evento', 'curso', 'mensaje') NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_tipo (tipo),
    INDEX idx_fecha (fecha)
);

-- Tabla comunidades (grupos o comunidades)
CREATE TABLE comunidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    creador_id INT NOT NULL,
    categoria_id INT,
    privado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creador_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    INDEX idx_creador_id (creador_id),
    INDEX idx_categoria_id (categoria_id)
);

-- Tabla comunidad_miembros (miembros de comunidades)
CREATE TABLE comunidad_miembros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comunidad_id INT NOT NULL,
    usuario_id INT NOT NULL,
    rol ENUM('miembro', 'moderador', 'admin') NOT NULL DEFAULT 'miembro',
    fecha_union DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comunidad_id) REFERENCES comunidades(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_miembro (comunidad_id, usuario_id),
    INDEX idx_comunidad_id (comunidad_id),
    INDEX idx_usuario_id (usuario_id)
);

-- Tabla historias_exito (historias de éxito)
CREATE TABLE historias_exito (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    usuario_id INT NOT NULL,
    video_url VARCHAR(300),
    fecha_publicacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_fecha_publicacion (fecha_publicacion)
);

-- Tabla testimonios (reseñas o testimonios)
CREATE TABLE testimonios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    texto TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_fecha (fecha)
);

-- Tabla admin_logs (registros de administrador, opcional para auditoría)
CREATE TABLE admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    accion TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_admin_id (admin_id),
    INDEX idx_fecha (fecha)
);

-- Datos de prueba para usuarios
INSERT INTO usuarios (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades, experiencia_años, pais, industria_preferida) VALUES
('Juan', 'Pérez', 'juan@example.com', 'hashedpass1', 'emprendedor', 'Bogotá', 'Emprendedor apasionado.', 'Desarrollo web', 3, 'Colombia', 'Tecnología'),
('Ana', 'García', 'ana@example.com', 'hashedpass2', 'inversor', 'Medellín', 'Inversora experimentada.', 'Finanzas', 5, 'Colombia', 'Finanzas'),
('Luis', 'Martínez', 'luis@example.com', 'hashedpass3', 'emprendedor', 'Cali', 'Desarrollador de apps.', 'Móvil', 2, 'Colombia', 'Tecnología'),
('María', 'López', 'maria@example.com', 'hashedpass4', 'inversor', 'Barranquilla', 'Inversora en innovación.', 'Inversiones', 4, 'Colombia', 'Innovación'),
('Carlos', 'Rodríguez', 'carlos@example.com', 'hashedpass5', 'mentor', 'Bogotá', 'Mentor de startups.', 'Mentoría', 7, 'Colombia', 'Tecnología'),
('Sofía', 'Hernández', 'sofia@example.com', 'hashedpass6', 'emprendedor', 'Medellín', 'Emprendedora social.', 'Social', 1, 'Colombia', 'Educación'),
('Admin', 'SENA', 'admin@sena.com', 'hashedadmin', 'administrador', 'Bogotá', 'Administrador de la plataforma.', 'Gestión', 10, 'Colombia', 'Educación');

-- Datos de prueba para categorias
INSERT INTO categorias (nombre, descripcion, tipo) VALUES
('Tecnología', 'Proyectos de software y hardware', 'proyecto'),
('Finanzas', 'Proyectos financieros y fintech', 'proyecto'),
('Educación', 'Proyectos educativos y e-learning', 'proyecto'),
('Salud', 'Proyectos de salud y bienestar', 'proyecto'),
('Guía de Marketing', 'Guías para marketing digital', 'recurso'),
('Curso React', 'Cursos de desarrollo web', 'curso'),
('Evento Startup', 'Eventos de startups', 'evento');

-- Datos de prueba para proyectos
INSERT INTO proyectos (usuario_id, titulo, descripcion, categoria_id, monto_objetivo, monto_recaudado, fecha_fin) VALUES
(1, 'App de Salud', 'Aplicación para monitoreo de salud.', 4, 10000.00, 6000.00, '2025-12-31'),
(1, 'Plataforma Educativa', 'Plataforma de aprendizaje online.', 3, 15000.00, 8000.00, '2025-11-30'),
(3, 'Startup Fintech', 'Solución financiera moderna.', 2, 20000.00, 10000.00, '2025-10-31'),
(6, 'Proyecto Social', 'Iniciativa para comunidades.', 3, 5000.00, 3000.00, '2025-09-30');

-- Datos de prueba para proyecto_alianzas
INSERT INTO proyecto_alianzas (proyecto_id, participante_id, rol_alianza, monto_invertido, estado) VALUES
(1, 2, 'inversor', 5000.00, 'aprobada'),
(1, 4, 'inversor', 3000.00, 'aprobada'),
(2, 2, 'inversor', 2000.00, 'aprobada'),
(3, 4, 'inversor', 4000.00, 'aprobada'),
(1, 5, 'mentor', 0.00, 'aprobada'),
(4, 5, 'mentor', 0.00, 'aprobada'),
(1, 6, 'colaborador', 0.00, 'pendiente');

-- Datos de prueba para comentarios
INSERT INTO comentarios (proyecto_id, usuario_id, texto, padre_id) VALUES
(1, 2, 'Interesante proyecto, me interesa invertir.', NULL),
(1, 3, '¡Gran idea! ¿Cómo puedo colaborar?', 1);

-- Datos de prueba para reacciones
INSERT INTO reacciones (proyecto_id, comentario_id, usuario_id, tipo) VALUES
(1, NULL, 3, 'me_gusta'),
(1, 1, 4, 'me_encanta'),
(1, NULL, 5, 'me_interesa'),
(2, NULL, 6, 'apoyo');

-- Datos de prueba para eventos
INSERT INTO eventos (titulo, descripcion, fecha, ubicacion, categoria_id, capacidad) VALUES
('Startup Weekend', 'Evento para startups.', '2025-09-15', 'Bogotá', 7, 100),
('Taller de Innovación', 'Taller práctico.', '2025-10-10', 'Medellín', 7, 50);

-- Datos de prueba para inscripciones_eventos
INSERT INTO inscripciones_eventos (evento_id, usuario_id) VALUES
(1, 1),
(1, 3),
(2, 6);

-- Datos de prueba para recursos
INSERT INTO recursos (titulo, descripcion, categoria_id, url, tipo) VALUES
('Guía de Marketing Digital', 'Guía completa de marketing.', 5, 'url/guia-marketing.pdf', 'guia'),
('Plantilla Pitch Deck', 'Plantilla para pitches.', 5, 'url/pitch-deck.docx', 'plantilla');

-- Datos de prueba para cursos
INSERT INTO cursos (titulo, descripcion, categoria_id, url, duracion, nivel) VALUES
('Curso React Básico', 'Aprende React desde cero.', 6, 'url/curso-react', 20, 'basico'),
('Curso Avanzado de IA', 'IA aplicada a negocios.', 6, 'url/curso-ia', 40, 'avanzado');

-- Datos de prueba para inscripciones_cursos
INSERT INTO inscripciones_cursos (curso_id, usuario_id, progreso, completado) VALUES
(1, 1, 50.00, FALSE),
(2, 3, 0.00, FALSE);

-- Datos de prueba para notificaciones
INSERT INTO notificaciones (usuario_id, tipo, mensaje, leida) VALUES
(1, 'alianza', 'Tienes una nueva propuesta de alianza.', FALSE),
(3, 'comentario', 'Nuevo comentario en tu proyecto.', FALSE);

-- Datos de prueba para comunidades
INSERT INTO comunidades (nombre, descripcion, creador_id, categoria_id, privado) VALUES
('Emprendedores Tech', 'Comunidad para emprendedores en tecnología.', 1, 1, FALSE),
('Inversores Colombia', 'Grupo para inversores locales.', 2, 2, TRUE);

-- Datos de prueba para comunidad_miembros
INSERT INTO comunidad_miembros (comunidad_id, usuario_id, rol) VALUES
(1, 1, 'admin'),
(1, 3, 'miembro'),
(2, 2, 'admin'),
(1, 5, 'moderador');

-- Datos de prueba para historias_exito
INSERT INTO historias_exito (titulo, descripcion, usuario_id, video_url) VALUES
('El viaje de Juan', 'Cómo Juan creció su startup.', 1, 'video/juan.mp4'),
('Ana la inversora', 'Historia de inversión exitosa.', 2, 'video/ana.mp4');

-- Datos de prueba para testimonios
INSERT INTO testimonios (usuario_id, texto) VALUES
(1, 'Gran plataforma para emprendedores.'),
(3, 'Me ayudó a conectar con inversores.');

-- Datos de prueba para admin_logs
INSERT INTO admin_logs (admin_id, accion) VALUES
(7, 'Aprobó alianza ID 1'),
(7, 'Eliminó usuario inactivo');

-- Consulta principal corregida y completada
SELECT 
    datos_emprendedores.id AS emprendedor_id,
    datos_emprendedores.nombre_completo,
    datos_emprendedores.correo_electronico,
    datos_emprendedores.ciudad,
    datos_emprendedores.descripcion_personal,
    datos_emprendedores.habilidades_tecnicas,
    datos_emprendedores.años_experiencia,
    datos_emprendedores.cuenta_verificada,
    datos_emprendedores.total_inversores,
    datos_emprendedores.total_inversion,
    datos_emprendedores.lista_proyectos,
    datos_emprendedores.lista_categorias,
    datos_emprendedores.nombres_inversores
FROM (
    SELECT 
        u.id,
        CONCAT(u.nombre, ' ', u.apellido) AS nombre_completo,
        u.correo AS correo_electronico,
        u.ubicacion AS ciudad,
        u.bio AS descripcion_personal,
        u.habilidades AS habilidades_tecnicas,
        u.experiencia_años AS años_experiencia,
        u.verificado AS cuenta_verificada,
        COUNT(DISTINCT pa.participante_id) AS total_inversores,
        SUM(pa.monto_invertido) AS total_inversion,
        GROUP_CONCAT(DISTINCT p.titulo ORDER BY pa.id SEPARATOR ', ') AS lista_proyectos,
        GROUP_CONCAT(DISTINCT c.nombre ORDER BY pa.id SEPARATOR ', ') AS lista_categorias,
        GROUP_CONCAT(DISTINCT CONCAT(u2.nombre, ' ', u2.apellido) ORDER BY pa.id SEPARATOR ', ') AS nombres_inversores
    FROM usuarios u
    LEFT JOIN proyectos p ON u.id = p.usuario_id
    LEFT JOIN proyecto_alianzas pa ON p.id = pa.proyecto_id AND pa.rol_alianza = 'inversor'
    LEFT JOIN categorias c ON p.categoria_id = c.id
    LEFT JOIN usuarios u2 ON pa.participante_id = u2.id
    WHERE u.rol = 'emprendedor' AND u.activo = 1
    GROUP BY u.id, u.nombre, u.apellido, u.correo, u.ubicacion, u.bio, u.habilidades, u.experiencia_años, u.verificado
) AS datos_emprendedores
WHERE datos_emprendedores.total_inversores > 0
ORDER BY datos_emprendedores.total_inversores DESC
LIMIT 6;

INSERT INTO usuarios (nombre, apellido, correo, password, rol, ubicacion, bio, habilidades, activo)
VALUES ('Admin', 'Conecta', 'admin@conecta-crece.com', 'adminpass123', 'emprendedor', 'Bogotá', 'Administrador del sistema', 'gestión,reportes', 1);


ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS ubicacion VARCHAR(100),
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS habilidades TEXT,
ADD COLUMN IF NOT EXISTS experiencia INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS intereses TEXT;

-- Verifica que existan
DESCRIBE usuarios;


select * from usuarios;

ALTER TABLE usuarios
ADD COLUMN foto_url VARCHAR(255) NULL DEFAULT NULL AFTER password;

DESCRIBE usuarios;

USE conecta_crece;

CREATE TABLE conexiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_origen_id INT NOT NULL,
    usuario_destino_id INT NOT NULL,
    estado ENUM('pendiente', 'aceptada', 'rechazada') DEFAULT 'pendiente',
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_origen_id) REFERENCES usuarios(id),
    FOREIGN KEY (usuario_destino_id) REFERENCES usuarios(id),
    UNIQUE KEY unique_conexion (usuario_origen_id, usuario_destino_id)
);



select * from usuarios;


CREATE TABLE historias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    titulo VARCHAR(200),
    contenido TEXT,
    imagen_url VARCHAR(255),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    aprobada TINYINT DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE reacciones_historias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    historia_id INT,
    usuario_id INT,
    tipo ENUM('like', 'inspirado'),
    FOREIGN KEY (historia_id) REFERENCES historias(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);


INSERT INTO recursos (titulo, descripcion, contenido) VALUES
('Guía de Fundraising 2025', 'Pasos para conseguir inversión', 'Contenido completo del PDF...'),
('Pitch Perfecto', 'Cómo impresionar a inversores', 'Estructura ideal de pitch...');



select * from usuarios;

ALTER TABLE proyectos
ADD COLUMN imagen_url VARCHAR(255),
ADD COLUMN video_url VARCHAR(255),
ADD COLUMN contacto VARCHAR(100),
ADD COLUMN redes_sociales TEXT;


select * from usuarios;

ALTER TABLE proyectos 
ADD COLUMN imagen_principal_url VARCHAR(255) NULL,
ADD COLUMN video_pitch_url VARCHAR(255) NULL,
ADD COLUMN sitio_web VARCHAR(255) NULL,
ADD COLUMN contacto VARCHAR(255) NULL,
ADD COLUMN telefono_proyecto VARCHAR(50) NULL,
ADD COLUMN redes JSON NULL;

SHOW COLUMNS FROM proyectos;


ALTER TABLE proyectos 
ADD COLUMN imagen_principal_url VARCHAR(255) NULL,
ADD COLUMN video_pitch_url VARCHAR(255) NULL,
ADD COLUMN sitio_web VARCHAR(255) NULL,
ADD COLUMN telefono_proyecto VARCHAR(50) NULL;


ALTER TABLE proyectos
ADD COLUMN redes TEXT NULL;

INSERT INTO proyectos (usuario_id, titulo, descripcion, descripcion_larga, categoria_id, progreso, estado,
    imagen_principal_url, video_pitch_url, catalogo_pdf_url, telefono_proyecto, whatsapp, instagram, facebook, twitter, linkedin, sitio_web, redes)
VALUES (1, 'Tienda de Ropa Zack Style', 'Ropa urbana premium', 'Catálogo completo 2025 con más de 100 diseños...', 1, 85, 'publicado',
    '/assets/uploads/ropa.jpg', '/assets/uploads/pitch.mp4', '/assets/uploads/catalogo.pdf',
    '3001234567', '573001234567', 'https://instagram.com/zackstyle', 'https://facebook.com/zackstyle',
    'https://twitter.com/zackstyle', 'https://linkedin.com/zackstyle', 'https://zackstyle.com',
    '{"tiktok":"zackstyle"}');

-- Tabla para mensajes del chat
CREATE TABLE mensajes_chat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sala VARCHAR(100) NOT NULL,
    usuario_id INT NOT NULL,
    tipo ENUM('texto', 'imagen', 'audio') NOT NULL,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_sala_fecha (sala, fecha),
    INDEX idx_usuario_id (usuario_id)
);

-- Tabla para rastrear usuarios activos en salas (opcional, para mostrar cuántos usuarios hay en cada sala)
CREATE TABLE usuarios_salas_activos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    sala VARCHAR(100) NOT NULL,
    fecha_ultima_actividad DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_usuario_sala (usuario_id, sala),
    INDEX idx_sala (sala),
    INDEX idx_activo (activo)
);

CREATE TABLE IF NOT EXISTS mensajes_chat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sala VARCHAR(100) NOT NULL,
    usuario_id INT NOT NULL,
    tipo ENUM('texto', 'imagen', 'audio') NOT NULL,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_sala_fecha (sala, fecha)
);

select * from usuarios

