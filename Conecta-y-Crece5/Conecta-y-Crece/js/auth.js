// frontend/js/auth.js
function verificarSesion() {
    const token = localStorage.getItem('token');
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
    
    if (!token || !usuario) {
        return null;
    }

    return { token, usuario };
}

// Mostrar usuario logueado en navbar
document.addEventListener('DOMContentLoaded', () => {
    const sesion = verificarSesion();
    const userStatus = document.getElementById('user-status');
    const navButtons = document.querySelector('.nav-buttons');
    const logout = document.getElementById('logout');

    if (sesion && userStatus) {
        userStatus.innerHTML = `
            <div class="user-info">
                <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" alt="Avatar" class="user-avatar">
                <span class="user-name">${sesion.usuario.nombre} ${sesion.usuario.apellido}</span>
            </div>
        `;
        navButtons.style.display = 'none';
        if (logout) logout.style.display = 'block';
    }

    // Logout
    if (logout) {
        logout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            localStorage.removeItem('usuario');
            window.location.href = '../html/login.html';
        });
    }
});