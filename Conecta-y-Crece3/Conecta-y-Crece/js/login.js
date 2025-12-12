// login.js – GUARDA TODO EL USUARIO + TOKEN
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const correo = document.getElementById('correo').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correo, password })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || 'Error al iniciar sesión');
            return;
        }

        // GUARDAR TODO EN LOCALSTORAGE
        localStorage.setItem('token', data.token);
        localStorage.setItem('usuario', JSON.stringify(data.usuario));

        // REDIRECCIÓN SEGÚN ROL
        const rol = data.usuario.rol.toLowerCase();
        if (rol === 'admin') {
            window.location.href = '../html/admin.html';
        } else {
            window.location.href = '../html/perfil.html';
        }

    } catch (error) {
        console.error(error);
        alert('Error de conexión');
    }
});