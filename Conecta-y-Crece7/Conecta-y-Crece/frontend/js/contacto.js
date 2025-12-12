const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const userStatus = document.getElementById('user-status');
const logout = document.getElementById('logout');
let isOpen = false;

// Menú orb animado
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
                ease: "back.out(1.7)",
                rotation: isOpen ? 360 : 0
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

window.addEventListener('load', () => {
    const user = JSON.parse(localStorage.getItem('user')) || { nombre: 'Invitado', rol: 'Sin rol' };
    if (user && user.nombre !== 'Invitado') {
        userStatus.style.display = 'block';
        userStatus.textContent = `Logueado como: ${user.nombre} (${user.rol})`;
    } else {
        userStatus.style.display = 'none';
        const navButtons = document.querySelector('.nav-buttons');
        if (navButtons) navButtons.style.display = 'flex';
    }

    const contactForm = document.getElementById('contact-form');
    const contactMessage = document.getElementById('contact-message');

    if (contactForm && contactMessage) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                nombre: document.getElementById('nombre').value,
                correo: document.getElementById('correo').value,
                mensaje: document.getElementById('mensaje').value
            };

            try {
                const response = await fetch('http://localhost:5000/contacto', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!response.ok) throw new Error('Error al enviar el mensaje');
                contactMessage.textContent = 'Mensaje enviado con éxito';
                contactMessage.style.color = '#00BFFF';
                contactForm.reset();
            } catch (error) {
                contactMessage.textContent = 'Error: ' + error.message;
                contactMessage.style.color = '#FF3B9E';
            }
        });
    }
});