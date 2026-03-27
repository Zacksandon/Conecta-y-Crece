// frontend/js/comunidad.js
document.addEventListener('DOMContentLoaded', async () => {
    await cargarUsuarios();
});

async function cargarUsuarios() {
    const container = document.getElementById('users-container');
    const loading = document.getElementById('loading');
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            container.innerHTML = '<p style="color: #FF3B9E;">Debes iniciar sesión para ver la comunidad</p>';
            loading.style.display = 'none';
            return;
        }

        const response = await fetch('http://localhost:5000/admin/reportes', {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer admin123',  // Usa el token de admin para ver todos
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('Error al cargar usuarios');

        const result = await response.json();
        if (!result.reportes || result.reportes.length === 0) {
            container.innerHTML = '<p style="color: #00BFFF;">No hay usuarios registrados aún</p>';
            loading.style.display = 'none';
            return;
        }

        container.innerHTML = '';
        result.reportes.forEach(user => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta-usuario';
            tarjeta.innerHTML = `
                <div class="foto-perfil" style="background-image: url('${user.foto_url || '../assets/default-avatar.png'}')"></div>
                <h3>${user.nombre} ${user.apellido}</h3>
                <p><strong>Rol:</strong> ${user.rol}</p>
                <p><strong>Ubicación:</strong> ${user.ubicacion || 'No especificada'}</p>
                <p><strong>Habilidades:</strong> ${user.habilidades || 'Sin habilidades'}</p>
                <button class="btn-conectar" onclick="verPerfil(${user.id})">Ver Perfil</button>
            `;
            container.appendChild(tarjeta);
        });

        loading.style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = '<p style="color: #FF3B9E;">Error al cargar la comunidad</p>';
        loading.style.display = 'none';
    }
}

function verPerfil(userId) {
    alert(`Ver perfil del usuario ID: ${userId}`);
    // Puedes redirigir a perfil.html?id=5
}