// frontend/js/login.js
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const correo = document.getElementById('correo').value.trim();
    const password = document.getElementById('password').value;

    if (!correo || !password) {
        alert('Completa todos los campos');
        return;
    }

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

        // GUARDAR EXACTAMENTE COMO LO LEE auth.js
        localStorage.setItem('token', data.token);
        localStorage.setItem('usuario', JSON.stringify(data.usuario));

        // REDIRIGIR SEGÚN ROL
        const rol = data.usuario.rol.toLowerCase();
        if (rol === 'admin' || rol === 'administrador') {
            window.location.href = '../html/admin.html';
        } else {
            window.location.href = '../html/proyectos.html';
        }

    } catch (error) {
        console.error('Error de conexión:', error);
        alert('No se pudo conectar al servidor');
    }
});