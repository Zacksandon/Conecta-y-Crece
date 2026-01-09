// frontend/js/auth.js
function verificarSesion() {
    const token = localStorage.getItem('token');
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');

    if (!token || !usuario) {
        return null;
    }
    return { token, usuario };
}

// Mostrar usuario logueado en navbar (si existe el elemento en la página)
document.addEventListener('DOMContentLoaded', () => {
    const sesion = verificarSesion();
    const userStatus = document.getElementById('user-status');
    const navButtons = document.querySelector('.nav-buttons');
    const logout = document.getElementById('logout');

    if (sesion && userStatus) {
        userStatus.innerHTML = `
            <div class="user-info">
                <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" alt="Avatar" class="user-avatar" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">
                <span class="user-name">${sesion.usuario.nombre} ${sesion.usuario.apellido || ''}</span>
            </div>
        `;
        if (navButtons) navButtons.style.display = 'none';
        if (logout) logout.style.display = 'block';
    } else {
        if (navButtons) navButtons.style.display = 'flex';
        if (logout) logout.style.display = 'none';
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
