const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const navButtons = document.querySelector('.nav-buttons');
const logout = document.getElementById('logout');
const userStatus = document.getElementById('user-status');
let isOpen = false;

// Menú orb en el centro
if (orbToggle && orbMenu) {
    orbToggle.addEventListener('click', () => {
        isOpen = !isOpen;
        orbItems.forEach((item, index) => {
            const totalItems = orbItems.length;
            const angle = (index * (360 / totalItems)) * Math.PI / 180;
            const radius = 120;
            gsap.to(item, {
                x: isOpen ? Math.cos(angle) * radius : 0,
                y: isOpen ? Math.sin(angle) * radius : 0,
                opacity: isOpen ? 1 : 0,
                duration: 0.5,
                delay: index * 0.1,
                ease: "back.out(1.7)"
            });
        });
        orbToggle.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
    });
}

logout.addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('user');
    window.location.href = '../html/index.html';
});

window.addEventListener('load', async () => {
    const usersContainer = document.getElementById('users-container');
    const loading = document.getElementById('loading');
    const user = JSON.parse(localStorage.getItem('user')) || { nombre: 'Invitado', rol: 'Sin rol' };
    if (user && user.nombre !== 'Invitado') {
        userStatus.style.display = 'block';
        userStatus.textContent = `Logueado como: ${user.nombre} (${user.rol})`;
    } else {
        userStatus.style.display = 'none';
        navButtons.style.display = 'flex';
    }

    try {
        const response = await fetch('http://localhost:5000/admin/reportes', {
            headers: { 'Authorization': 'Bearer admin123' }
        });
        if (!response.ok) throw new Error('Error al cargar usuarios');
        const data = await response.json();
        loading.style.display = 'none';
        if (data.reportes && data.reportes.length > 0) {
            const filteredUsers = data.reportes.filter(u => ['emprendedor', 'mentor', 'inversor'].includes(u.rol.toLowerCase()) && u.activo === 1);
            usersContainer.innerHTML = ''; // Limpiar antes de agregar
            filteredUsers.forEach(user => {
                const card = document.createElement('div');
                card.className = 'tarjeta-usuario';
                card.innerHTML = `
                    <div class="foto-perfil" style="background: linear-gradient(135deg, #${(Math.random()*0xFFFFFF<<0).toString(16)}, #${(Math.random()*0xFFFFFF<<0).toString(16)});"></div>
                    <h3>${user.nombre} ${user.apellido}</h3>
                    <p class="rol">${user.rol}</p>
                    <p class="ubicacion">${user.ubicacion || 'Sin ubicación'}</p>
                    <p class="habilidades">${user.habilidades || 'Sin habilidades'}</p>
                    <button class="btn-conectar" data-id="${user.id}">Conectar</button>
                `;
                usersContainer.appendChild(card);
            });

            // Evento para abrir ventana emergente al hacer clic en "Conectar"
            document.querySelectorAll('.btn-conectar').forEach(button => {
                button.addEventListener('click', () => {
                    const userId = button.getAttribute('data-id');
                    const selectedUser = filteredUsers.find(u => u.id === userId);
                    if (selectedUser) {
                        const modal = document.createElement('div');
                        modal.className = 'modal';
                        modal.innerHTML = `
                            <div class="modal-content">
                                <div class="foto-perfil-large" style="background: linear-gradient(135deg, #${(Math.random()*0xFFFFFF<<0).toString(16)}, #${(Math.random()*0xFFFFFF<<0).toString(16)});"></div>
                                <h2>${selectedUser.nombre} ${selectedUser.apellido}</h2>
                                <p><strong>Rol:</strong> ${selectedUser.rol}</p>
                                <p><strong>Ubicación:</strong> ${selectedUser.ubicacion || 'Sin ubicación'}</p>
                                <p><strong>Biografía:</strong> ${selectedUser.bio || 'Sin biografía'}</p>
                                <p><strong>Habilidades:</strong> ${selectedUser.habilidades || 'Sin habilidades'}</p>
                                <p><strong>Experiencia:</strong> ${selectedUser.experiencia || '0'} años</p>
                                <p><strong>Intereses:</strong> ${selectedUser.intereses || 'Sin intereses'}</p>
                                <button class="btn-back">Volver</button>
                            </div>
                        `;
                        document.body.appendChild(modal);

                        // Ampliar foto al hacer clic
                        const fotoPerfil = modal.querySelector('.foto-perfil-large');
                        fotoPerfil.addEventListener('click', () => {
                            fotoPerfil.style.width = fotoPerfil.style.width === '200px' ? '120px' : '200px';
                            fotoPerfil.style.height = fotoPerfil.style.height === '200px' ? '120px' : '200px';
                            fotoPerfil.style.transition = 'all 0.3s ease';
                        });

                        // Cerrar modal
                        modal.querySelector('.btn-back').addEventListener('click', () => {
                            document.body.removeChild(modal);
                        });
                    }
                });
            });
        } else {
            usersContainer.innerHTML = '<p style="color: #FFFFFF;">No hay usuarios registrados.</p>';
        }
    } catch (error) {
        usersContainer.innerHTML = `<p style="color: #FF3B9E;">Error: ${error.message}</p>`;
    }

    const postsContainer = document.getElementById('posts-container');
    const postsLoading = document.getElementById('posts-loading');
    postsLoading.style.display = 'none';
    if (user && user.nombre !== 'Invitado') {
        postsContainer.innerHTML = `
            <div class="publicacion">
                <p class="usuario">${user.nombre} ${user.apellido} - <span class="fecha">14 Sep 2025</span></p>
                <p class="texto">¡Hola! Estoy buscando colaboración para mi nuevo proyecto.</p>
                <div class="reacciones">
                    <button class="btn-reaccion">💡 Me interesa</button>
                    <button class="btn-reaccion">❤️ Me encanta</button>
                    <button class="btn-reaccion">👍 Apoyo</button>
                </div>
            </div>
        `;
    } else {
        postsContainer.innerHTML = '<p style="color: #FFFFFF;">Inicia sesión para ver publicaciones.</p>';
    }
});