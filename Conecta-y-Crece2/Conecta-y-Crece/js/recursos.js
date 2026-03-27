const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const userStatus = document.getElementById('user-status');
const logout = document.getElementById('logout');
const navButtons = document.querySelector('.nav-buttons');
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
        navButtons.style.display = 'flex';
    }

    // Interactividad para descargar recursos
    document.querySelectorAll('.btn-descargar').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            alert(`Descarga de ${button.parentElement.querySelector('h3').textContent} iniciada. (Simulación)`);
        });
    });

    // Animación de hover en tarjetas
    const cards = document.querySelectorAll('.recurso-card');
    cards.forEach(card => {
        card.addEventListener('mouseover', () => {
            gsap.to(card, { scale: 1.05, boxShadow: '0 0 25px #00BFFF, 0 0 35px #FF3B9E', duration: 0.3 });
        });
        card.addEventListener('mouseout', () => {
            gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.3 });
        });
    });
});