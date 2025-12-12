// frontend/js/auth.js → VERSIÓN FINAL CON DETECCIÓN DE TOKEN EXPIRADO
function verificarSesion() {
    const token = localStorage.getItem('token');
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');

    if (!token || !usuario) {
        return null;
    }

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp * 1000 < Date.now()) {
            console.warn("Token expirado");
            localStorage.clear();
            return null;
        }
    } catch (e) {
        console.warn("Token inválido");
        localStorage.clear();
        return null;
    }

    return { token, usuario };
}

document.addEventListener('DOMContentLoaded', () => {
    const sesion = verificarSesion();
    const userStatus = document.getElementById('user-status');
    const navButtons = document.querySelector('.nav-buttons');
    const logout = document.getElementById('logout');

    if (sesion && userStatus) {
        userStatus.innerHTML = `
            <div class="user-info">
                <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" alt="Avatar" class="user-avatar">
                <span class="user-name">${sesion.usuario.nombre} ${sesion.usuario.apellido || ''}</span>
            </div>
        `;
        if (navButtons) navButtons.style.display = 'none';
    } else {
        if (navButtons) navButtons.style.display = 'flex';
    }

    if (logout) {
        logout.style.display = sesion ? 'block' : 'none';
        logout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = 'login.html';
        });
    }
});