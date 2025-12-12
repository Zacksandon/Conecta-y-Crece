// login.js – GUARDA TODO EN 'sesion' COMO ESPERA proyectos.js
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

        // GUARDAR TODO EN 'sesion' (EXACTAMENTE COMO LO LEE proyectos.js)
        localStorage.setItem('sesion', JSON.stringify({
            token: data.token,
            usuario: data.usuario
        }));

        // REDIRECCIÓN SEGÚN ROL
        const rol = data.usuario.rol.toLowerCase();
        if (rol === 'administrador') {
            window.location.href = '../html/admin.html';
        } else {
            window.location.href = '../html/proyectos.html'; // AQUÍ VA A PROYECTOS
        }

    } catch (error) {
        console.error(error);
        alert('Error de conexión');
    }
});