// frontend/js/comunidad.js
let isOpen = false;
const orbToggle = document.querySelector('.orb-menu-toggle');
const orbItems = document.querySelectorAll('.orb-items li');

document.addEventListener('DOMContentLoaded', async () => {
    // === MENÚ ORBES ===
    orbToggle.addEventListener('click', () => {
        isOpen = !isOpen;
        orbItems.forEach((item, i) => {
            const angle = (i * 360 / orbItems.length) * Math.PI / 180;
            const radius = 100;
            gsap.to(item, {
                x: isOpen ? Math.cos(angle) * radius : 0,
                y: isOpen ? Math.sin(angle) * radius : 0,
                opacity: isOpen ? 1 : 0,
                duration: 0.5,
                delay: i * 0.1,
                ease: "back.out(1.7)"
            });
        });
        orbToggle.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
    });

    // === CARGAR USUARIOS ===
    await cargarUsuarios();
});

async function cargarUsuarios() {
    const container = document.getElementById('users-container');
    const loading = document.getElementById('loading');
    
    const sesion = verificarSesion();
    if (!sesion) {
        container.innerHTML = '<p style="color: #FF3B9E;">Debes iniciar sesión para ver la comunidad</p>';
        loading.style.display = 'none';
        return;
    }

    const token = sesion.token;

    try {
        const response = await fetch('http://localhost:5000/api/usuarios', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error en la API');
        }

        const result = await response.json();
        if (!result.usuarios || result.usuarios.length === 0) {
            container.innerHTML = '<p style="color: #00BFFF;">No hay usuarios registrados aún</p>';
            loading.style.display = 'none';
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
                    <button class="btn-conectar" onclick="conectar(${user.id})">Conectar</button>
                    <button class="btn-ver-perfil" onclick="verPerfil(${user.id})">Ver Perfil</button>
                </div>
            `;
            container.appendChild(tarjeta);
        });

        loading.style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `<p style="color: #FF3B9E;">Error: ${error.message}</p>`;
        loading.style.display = 'none';
    }
}

function verPerfil(userId) {
    window.location.href = `../html/perfil-publico.html?id=${userId}`;
}

function conectar(userId) {
    alert(`Solicitud de conexión enviada al usuario ID: ${userId}`);
}