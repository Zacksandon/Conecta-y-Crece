const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const userStatus = document.getElementById('user-status');
const logout = document.getElementById('logout');
const navButtons = document.querySelector('.nav-buttons');
let isOpen = false;

if (orbToggle && orbMenu) {
    orbToggle.addEventListener('click', () => {
        isOpen = !isOpen;
        orbItems.forEach((item, index) => {
            const totalItems = orbItems.length;
            const angle = (index * (360 / totalItems)) * Math.PI / 180;
            const radius = 180; // Aumentado para un efecto más amplio
            gsap.to(item, {
                x: isOpen ? Math.cos(angle) * radius : 0,
                y: isOpen ? Math.sin(angle) * radius + 160 : 0,
                opacity: isOpen ? 1 : 0,
                scale: isOpen ? 1.2 : 1,
                rotation: isOpen ? '+=45' : 0,
                duration: 0.6,
                delay: index * 0.08,
                ease: "elastic.out(1, 0.3)"
            });
        });
        gsap.to(orbToggle, {
            scale: isOpen ? 1.1 : 1,
            boxShadow: isOpen ? '0 0 40px #FF3B9E, 0 0 20px #00BFFF' : '0 0 20px #00BFFF',
            color: isOpen ? '#FF3B9E' : '#00BFFF',
            duration: 0.5
        });
    });
}

logout.addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('user');
    window.location.href = '../html/index.html';
});

window.addEventListener('load', () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        userStatus.textContent = `Logueado como: ${user.nombre} (${user.rol})`;
    } else {
        userStatus.style.display = 'none';
        navButtons.style.display = 'flex';
    }
});