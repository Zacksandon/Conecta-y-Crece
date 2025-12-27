// Añade esto en tu ruta GET /api/historias
const historias = await db.query(`
    SELECT h.*, 
           CONCAT(u.nombre, ' ', u.apellido) AS autor,
           u.nombre AS usuario_nombre,
           u.apellido AS usuario_apellido
    FROM historias h
    JOIN usuarios u ON h.usuario_id = u.id
    WHERE h.aprobada = 1
    ORDER BY h.fecha DESC
`);