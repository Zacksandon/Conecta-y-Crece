// frontend/js/auth.js
(function () {
    function verificarSesion() {
        const token = localStorage.getItem('token');
        const usuario = localStorage.getItem('usuario');
        if (!token || !usuario) return null;
        try {
            return { token, user: JSON.parse(usuario) };
        } catch {
            localStorage.clear();
            return null;
        }
    }

    function mostrarUsuarioEnNavbar() {
        const userStatus = document.getElementById('user-status');
        const navButtons = document.querySelector('.nav-buttons');
        const logoutItem = document.querySelector('#logout');

        if (!userStatus) return;

        const sesion = verificarSesion();

        if (sesion) {
            const { user } = sesion;
            const foto = user.foto_url || '../assets/default-avatar.png';

            userStatus.innerHTML = `
                <div class="user-info">
                    <img src="${foto}" alt="Foto" class="user-avatar" onerror="this.src='../assets/default-avatar.png'">
                    <span class="user-name">${user.nombre} ${user.apellido}</span>
                </div>
            `;

            if (navButtons) navButtons.style.display = 'none';
            if (logoutItem) {
                logoutItem.style.display = 'block';
                logoutItem.onclick = (e) => {
                    e.preventDefault();
                    localStorage.clear();
                    window.location.href = '../html/login.html';
                };
            }
        } else {
            userStatus.innerHTML = '';
            if (navButtons) navButtons.style.display = 'flex';
            if (logoutItem) logoutItem.style.display = 'none';
        }
    }

    // Ejecutar al cargar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mostrarUsuarioEnNavbar);
    } else {
        mostrarUsuarioEnNavbar();
    }
})();