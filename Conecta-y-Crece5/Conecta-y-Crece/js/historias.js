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

    const cards = document.querySelectorAll('.historia-card');
    const canvas = document.querySelector('.particle-canvas');
    const ctx = canvas.getContext('2d');

    cards.forEach(card => {
        card.addEventListener('mouseover', () => {
            gsap.to(card, { scale: 1.05, boxShadow: '0 0 25px #00BFFF, 0 0 35px #FF3B9E', duration: 0.3 });
        });
        card.addEventListener('mouseout', () => {
            gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.3 });
        });

        const readMore = card.querySelector('.btn-ver-mas');
        readMore.addEventListener('click', (e) => {
            e.preventDefault();
            alert(`Detalles de ${card.querySelector('h3').textContent}: Esta es una vista previa. ¡Más contenido próximamente!`);
        });
    });

    // Partículas
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const particlesArray = [];
    const numberOfParticles = 50;

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 5 + 1;
            this.speedX = Math.random() * 3 - 1.5;
            this.speedY = Math.random() * 3 - 1.5;
            this.color = `hsl(${Math.random() * 360}, 70%, 50%)`;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX = -this.speedX;
            if (this.y < 0 || this.y > canvas.height) this.speedY = -this.speedY;
        }
        draw() {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function init() {
        for (let i = 0; i < numberOfParticles; i++) particlesArray.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particlesArray.length; i++) {
            particlesArray[i].update();
            particlesArray[i].draw();
        }
        requestAnimationFrame(animate);
    }

    init();
    animate();

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
});