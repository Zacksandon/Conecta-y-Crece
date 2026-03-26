// frontend/js/perfil-publico.js
let usuarioId = null;
let usuarioData = null;
let solicitudEnviada = false;

document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    usuarioId = params.get('id');
    
    if (!usuarioId) {
        alert('No se especificó el usuario');
        window.location.href = '../html/comunidad.html';
        return;
    }

    const sesion = verificarSesion();
    if (!sesion) {
        alert('Debes iniciar sesión');
        window.location.href = '../html/login.html';
        return;
    }

    const userStatus = document.getElementById('user-status');
    const foto = sesion.usuario.foto_url || '../assets/default-avatar.png';
    userStatus.innerHTML = `
        <div class="user-info">
            <img src="${foto}" alt="Avatar" class="user-avatar">
            <span class="user-name">${sesion.usuario.nombre} ${sesion.usuario.apellido}</span>
        </div>
    `;

    await cargarPerfil(sesion.token);
    verificarConexionExistente(sesion.token);
});

async function cargarPerfil(token) {
    try {
        const response = await fetch(`http://localhost:5000/api/perfil-publico/${usuarioId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al cargar perfil');
        }

        usuarioData = await response.json();

        document.getElementById('foto-perfil').style.backgroundImage = 
            `url('${usuarioData.foto_url || '../assets/default-avatar.png'}')`;
        
        document.getElementById('nombre-completo').textContent = 
            `${usuarioData.nombre} ${usuarioData.apellido}`;
        
        document.getElementById('rol').textContent = usuarioData.rol || 'No especificado';
        document.getElementById('ubicacion').textContent = usuarioData.ubicacion || 'No especificada';
        document.getElementById('habilidades').textContent = usuarioData.habilidades || 'Sin habilidades';
        document.getElementById('bio').textContent = usuarioData.bio || 'Sin biografía';
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar el perfil: ' + error.message);
    }
}

async function verificarConexionExistente(token) {
    try {
        const response = await fetch(`http://localhost:5000/api/conexiones/existe/${usuarioId}`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.existe) {
                document.querySelector('.btn-conectar').textContent = 'Solicitud Enviada';
                document.querySelector('.btn-conectar').disabled = true;
                solicitudEnviada = true;
            }
        }
    } catch (e) { /* Ignorar si no existe la ruta aún */ }
}

async function conectar() {
    if (!usuarioData || solicitudEnviada) return;

    const sesion = verificarSesion();
    if (!sesion) return;

    try {
        const response = await fetch('http://localhost:5000/api/conexiones', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${sesion.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usuario_destino_id: usuarioId
            })
        });

        if (response.ok) {
            alert(`¡Solicitud enviada a ${usuarioData.nombre}!`);
            document.querySelector('.btn-conectar').textContent = 'Solicitud Enviada';
            document.querySelector('.btn-conectar').disabled = true;
            solicitudEnviada = true;
        } else {
            const err = await response.json();
            alert(err.error || 'Error al enviar solicitud');
        }
    } catch (error) {
        alert('Error de conexión');
    }
}