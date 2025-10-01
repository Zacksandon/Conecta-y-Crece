const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const userStatus = document.getElementById('user-status');
const logout = document.getElementById('logout');
const userInfoDisplay = document.getElementById('user-info-display');
const rolContent = document.getElementById('rol-content');
const profileForm = document.getElementById('profile-form');
const updateForm = document.getElementById('updateForm');
const updateMessage = document.getElementById('update-message');
const navButtons = document.querySelector('.nav-buttons');
const canvas = document.querySelector('.particle-canvas');
const ctx = canvas.getContext('2d');
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

updateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        updateMessage.textContent = 'Error: No estás logueado.';
        updateMessage.style.color = '#FF3B9E';
        return;
    }

    const updatedData = {
        id: user.id,
        nombre: document.getElementById('nombre').value,
        apellido: document.getElementById('apellido').value,
        correo: document.getElementById('correo').value,
        ubicacion: document.getElementById('ubicacion').value,
        bio: document.getElementById('bio').value,
        habilidades: document.getElementById('habilidades').value,
        experiencia: document.getElementById('experiencia').value,
        intereses: document.getElementById('intereses').value
    };

    try {
        const response = await fetch('http://localhost:5000/actualizar', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${user.id}` },
            body: JSON.stringify(updatedData)
        });

        if (!response.ok) throw new Error('Error al actualizar en la base de datos');
        const result = await response.json();
        updateMessage.textContent = result.message || 'Perfil actualizado con éxito';
        updateMessage.style.color = '#00BFFF';
        localStorage.setItem('user', JSON.stringify({ ...user, ...updatedData }));
    } catch (error) {
        updateMessage.textContent = 'Error: ' + error.message;
        updateMessage.style.color = '#FF3B9E';
    }
});

// Partículas
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const particlesArray = [];
const numberOfParticles = 75;

class Particle {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 6 + 2;
        this.speedX = Math.random() * 4 - 2;
        this.speedY = Math.random() * 4 - 2;
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

window.addEventListener('load', () => {
    const user = JSON.parse(localStorage.getItem('user')) || { nombre: 'Invitado', rol: 'Sin rol' };
    if (user && user.nombre !== 'Invitado') {
        userStatus.textContent = `Logueado como: ${user.nombre} (${user.rol})`;
        userInfoDisplay.textContent = `Bienvenido, ${user.nombre} ${user.apellido} (${user.rol})`;
        let content = '';
        switch (user.rol.toLowerCase()) {
            case 'emprendedor':
                content = `
                    <h2>Tus Oportunidades</h2>
                    <p>Explora proyectos, conecta con mentores y encuentra inversores para hacer crecer tu idea.</p>
                    <a href="proyectos.html" class="btn-registro">Ver Proyectos</a>
                `;
                break;
            case 'mentor':
                content = `
                    <h2>Tus Mentorías</h2>
                    <p>Guía a emprendedores con tu experiencia y gestiona tus sesiones.</p>
                    <a href="comunidad.html" class="btn-registro">Ver Solicitudes</a>
                `;
                break;
            case 'inversor':
                content = `
                    <h2>Tus Inversiones</h2>
                    <p>Descubre startups prometedoras y evalúa oportunidades de inversión.</p>
                    <a href="proyectos.html" class="btn-registro">Explorar Inversiones</a>
                `;
                break;
            case 'administrador':
                content = `
                    <h2>Panel de Administración</h2>
                    <p>Gestiona usuarios y genera reportes con herramientas avanzadas.</p>
                    <a href="admin.html" class="btn-registro">Ir a Admin</a>
                `;
                break;
            default:
                content = `<p>Rol no reconocido. Contacta al soporte.</p>`;
        }
        rolContent.innerHTML = content;
        profileForm.style.display = 'block';
        document.getElementById('nombre').value = user.nombre || '';
        document.getElementById('apellido').value = user.apellido || '';
        document.getElementById('correo').value = user.correo || '';
        document.getElementById('ubicacion').value = user.ubicacion || '';
        document.getElementById('bio').value = user.bio || '';
        document.getElementById('habilidades').value = user.habilidades || '';
        document.getElementById('experiencia').value = user.experiencia || 0;
        document.getElementById('intereses').value = user.intereses || '';
    } else {
        userStatus.style.display = 'none';
        navButtons.style.display = 'flex';
        userInfoDisplay.textContent = 'Por favor, inicia sesión para ver tu perfil.';
        rolContent.innerHTML = '<p>Inicia sesión para desbloquear contenido.</p>';
        profileForm.style.display = 'none';
    }
});