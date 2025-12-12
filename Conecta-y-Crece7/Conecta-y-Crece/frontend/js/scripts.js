// frontend/js/scripts.js
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const message = document.getElementById('message');

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            fetch('http://localhost:5000/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ correo: email, password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message === 'Inicio de sesión exitoso') {
                    message.textContent = data.message;
                    message.style.color = '#00BFFF';
                    // Redirige a dashboard (simulado)
                    // window.location.href = '../html/dashboard.html';
                } else {
                    message.textContent = data.error || 'Error en el inicio de sesión';
                    message.style.color = '#FF3B9E';
                }
            })
            .catch(error => {
                message.textContent = 'Error de conexión con el servidor';
                message.style.color = '#FF3B9E';
                console.error('Error:', error);
            });
        });
    }

    const registroLink = document.getElementById('registro-link');
    if (registroLink) {
        registroLink.addEventListener('click', function(e) {
            e.preventDefault();
            const registroData = prompt('Ingresa datos (JSON): {"nombre":"Nuevo","apellido":"Usuario","correo":"nuevo@ejemplo.com","password":"pass123"}');
            if (registroData) {
                fetch('http://localhost:5000/registro', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: registroData
                })
                .then(response => response.json())
                .then(data => alert(data.message || data.error))
                .catch(error => console.error('Error:', error));
            }
        });
    }
});