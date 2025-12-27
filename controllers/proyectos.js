// controllers/proyectos.js
const db = require('../database');

const obtenerProyectos = async () => {
    const query = `
        SELECT p.*, u.nombre as nombre_usuario 
        FROM proyectos p 
        LEFT JOIN usuarios u ON p.usuario_id = u.id 
        WHERE p.estado = 'publicado' OR p.estado IS NULL
        ORDER BY p.fecha_creacion DESC
    `;
    const [rows] = await db.query(query);
    return rows;
};

module.exports = { obtenerProyectos };