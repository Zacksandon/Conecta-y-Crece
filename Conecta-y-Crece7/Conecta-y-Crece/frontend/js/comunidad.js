// frontend/js/comunidad.js
let isOpen = false;
const orbToggle = document.querySelector('.orb-menu-toggle');
const orbItems = document.querySelectorAll('.orb-items li');

document.addEventListener('DOMContentLoaded', async () => {
    // === MENÚ ORBES ===
    if (orbToggle) {
        orbToggle.addEventListener('click', () => {
            isOpen = !isOpen;
            orbItems.forEach((item, i) => {
                const angle = (i * 360 / orbItems.length) * Math.PI / 180;
                const radius = 100;
                gsap.to(item, {
                    x: isOpen ? Math.cos(angle) * radius : 0,
                    y: isOpen ? Math.sin(angle) * radius : 0,
                    opacity: isOpen ? 1 : 0,
                    duration: 0.45,
                    delay: i * 0.05,
                    ease: "back.out(1.4)"
                });
            });
            orbToggle.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
        });
    }

    // === CARGAR USUARIOS ===
    await cargarUsuarios();
});

async function cargarUsuarios() {
    const container = document.getElementById('users-container');
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'block';

    const sesion = verificarSesion();
    if (!sesion) {
        if (container) container.innerHTML = '<p style="color: #FF3B9E;">Debes iniciar sesión para ver la comunidad</p>';
        if (loading) loading.style.display = 'none';
        return;
    }

    const token = sesion.token;

    try {
        const response = await fetch('http://localhost:5000/api/usuarios', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            let errorMsg = response.statusText || 'Error en la API';
            try {
                const errJson = await response.json();
                errorMsg = errJson.error || errorMsg;
            } catch (e) {}
            throw new Error(errorMsg);
        }

        const result = await response.json();
        if (!result.usuarios || result.usuarios.length === 0) {
            if (container) container.innerHTML = '<p style="color: #00BFFF;">No hay usuarios registrados aún</p>';
            if (loading) loading.style.display = 'none';
            return;
        }

        container.innerHTML = '';
        result.usuarios.forEach(user => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta-usuario';
            tarjeta.innerHTML = `
                <div class="foto-perfil" style="background-image: url('${user.foto_url || '../assets/default-avatar.png'}')"></div>
                <h3>${user.nombre} ${user.apellido}</h3>
                <p><strong>Rol:</strong> ${user.rol}</p>
                <p><strong>Ubicación:</strong> ${user.ubicacion || 'No especificada'}</p>
                <p><strong>Habilidades:</strong> ${user.habilidades || 'Sin habilidades'}</p>
                <div class="acciones">
                    <button class="btn-conectar" data-id="${user.id}">Conectar</button>
                    <button class="btn-ver-perfil" data-id="${user.id}">Ver Perfil</button>
                </div>
            `;
            container.appendChild(tarjeta);
        });

        // Delegación de eventos para botones creados dinámicamente
        container.querySelectorAll('.btn-ver-perfil').forEach(b => {
            b.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                verPerfil(id);
            });
        });
        container.querySelectorAll('.btn-conectar').forEach(b => {
            b.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                await enviarConexion(id);
            });
        });

        if (loading) loading.style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        if (container) container.innerHTML = `<p style="color: #FF3B9E;">Error: ${error.message}</p>`;
        if (loading) loading.style.display = 'none';
    }
}

function verPerfil(userId) {
    window.location.href = `../html/perfil-publico.html?id=${userId}`;
}

async function enviarConexion(userId) {
    const sesion = verificarSesion();
    if (!sesion) return alert('Debes iniciar sesión');
    try {
        const res = await fetch('http://localhost:5000/api/conexiones', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${sesion.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ usuario_destino_id: userId })
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.error || 'Error al enviar solicitud');
        alert(j.message || 'Solicitud enviada');
    } catch (e) {
        alert('Error: ' + e.message);
    }
}
