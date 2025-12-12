// perfil.js – CARGA PERFIL CON DATOS DE localStorage + API
const fotoInput = document.getElementById('foto-input');
const fotoPreview = document.getElementById('foto-preview');
const updateForm = document.getElementById('updateForm');
const updateMessage = document.getElementById('update-message');
const rolContent = document.getElementById('rol-content');
const orbToggle = document.querySelector('.orb-menu-toggle');
const orbItems = document.querySelectorAll('.orb-items li');
const logout = document.getElementById('logout');
let fotoFile = null;
let isOpen = false;

// VERIFICAR SI HAY USUARIO
function verificarUsuario() {
    const token = localStorage.getItem('token');
    const usuario = localStorage.getItem('usuario');

    if (!token || !usuario) {
        alert('Debes iniciar sesión');
        window.location.href = '../html/login.html';
        return null;
    }

    try {
        return JSON.parse(usuario);
    } catch {
        localStorage.clear();
        window.location.href = '../html/login.html';
        return null;
    }
}

// CARGAR PERFIL
async function cargarPerfil() {
    const user = verificarUsuario();
    if (!user) return;

    try {
        const res = await fetch(`http://localhost:5000/api/perfil/${user.id}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (!res.ok) throw new Error('Error al cargar perfil');

        const data = await res.json();

        // ACTUALIZAR localStorage con datos completos
        const fullUser = { ...user, ...data };
        localStorage.setItem('usuario', JSON.stringify(fullUser));

        // RELLENAR FORMULARIO
        document.getElementById('nombre').value = fullUser.nombre || '';
        document.getElementById('apellido').value = fullUser.apellido || '';
        document.getElementById('correo').value = fullUser.correo || '';
        document.getElementById('ubicacion').value = fullUser.ubicacion || '';
        document.getElementById('bio').value = fullUser.bio || '';
        document.getElementById('habilidades').value = fullUser.habilidades || '';
        document.getElementById('experiencia').value = fullUser.experiencia || 0;
        document.getElementById('intereses').value = fullUser.intereses || '';

        // FOTO
        if (fullUser.foto_url) {
            fotoPreview.src = fullUser.foto_url;
        }

        // CONTENIDO POR ROL
        let html = '';
        switch (fullUser.rol.toLowerCase()) {
            case 'emprendedor':
                html = `<h2>Tus Oportunidades</h2><p>Explora proyectos...</p><a href="proyectos.html" class="btn-registro">Ver Proyectos</a>`;
                break;
            case 'mentor':
                html = `<h2>Tus Mentorías</h2><p>Guía a emprendedores...</p><a href="comunidad.html" class="btn-registro">Ver Solicitudes</a>`;
                break;
            case 'inversor':
                html = `<h2>Tus Inversiones</h2><p>Descubre startups...</p><a href="proyectos.html" class="btn-registro">Ver Inversiones</a>`;
                break;
            case 'admin':
                html = `<h2>Panel Admin</h2><p>Gestiona usuarios...</p><a href="admin.html" class="btn-registro">Ir a Admin</a>`;
                break;
        }
        rolContent.innerHTML = html;

    } catch (error) {
        console.error(error);
        alert('Error al cargar perfil: ' + error.message);
    }
}

// SUBIR FOTO
fotoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => fotoPreview.src = e.target.result;
        reader.readAsDataURL(file);
        fotoFile = file;
    }
});

// GUARDAR CAMBIOS
updateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = verificarUsuario();
    if (!user) return;

    const formData = new FormData();
    formData.append('nombre', document.getElementById('nombre').value);
    formData.append('apellido', document.getElementById('apellido').value);
    formData.append('ubicacion', document.getElementById('ubicacion').value);
    formData.append('bio', document.getElementById('bio').value);
    formData.append('habilidades', document.getElementById('habilidades').value);
    formData.append('experiencia', document.getElementById('experiencia').value);
    formData.append('intereses', document.getElementById('intereses').value);
    if (fotoFile) formData.append('foto', fotoFile);

    try {
        const res = await fetch(`http://localhost:5000/api/perfil/${user.id}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: formData
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.error);

        updateMessage.textContent = result.message;
        updateMessage.style.color = '#00BFFF';

        if (result.foto_url) {
            const updatedUser = { ...user, foto_url: result.foto_url };
            localStorage.setItem('usuario', JSON.stringify(updatedUser));
        }

        setTimeout(cargarPerfil, 1000);

    } catch (error) {
        updateMessage.textContent = 'Error: ' + error.message;
        updateMessage.style.color = '#FF3B9E';
    }
});

// LOGOUT
logout.addEventListener('click', () => {
    localStorage.clear();
    window.location.href = '../html/login.html';
});

// ORB MENU
orbToggle.addEventListener('click', () => {
    isOpen = !isOpen;
    orbItems.forEach((item, i) => {
        const angle = (i * 360 / orbItems.length) * Math.PI / 180;
        const radius = 100;
        gsap.to(item, {
            x: isOpen ? Math.cos(angle) * radius : 0,
            y: isOpen ? Math.sin(angle) * radius : 0,
            opacity: isOpen ? 1 : 0,
            duration: 0.5,
            delay: i * 0.1,
            ease: "back.out(1.7)"
        });
    });
    orbToggle.style.transform = isOpen ? 'translate(-50%, -50%) rotate(90deg)' : 'translate(-50%, -50%) rotate(0deg)';
});

// PARTÍCULAS
const canvas = document.querySelector('.particle-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const particles = Array.from({ length: 80 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    size: Math.random() * 5 + 2,
    speedX: Math.random() * 3 - 1.5,
    speedY: Math.random() * 3 - 1.5,
    color: `hsl(${Math.random() * 360}, 70%, 60%)`
}));

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.speedX; p.y += p.speedY;
        if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
        if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
    });
    requestAnimationFrame(animate);
}
animate();

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

// INICIAR
window.addEventListener('load', cargarPerfil);