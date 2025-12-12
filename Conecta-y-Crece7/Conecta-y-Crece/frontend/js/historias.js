const sesion = verificarSesion();
let historias = [];
let currentIndex = 0;
let isOrbOpen = false;

document.addEventListener('DOMContentLoaded', async () => {
    setupOrbMenu(); // MENÚ ORB ANTES DE TODO
    await cargarHistorias();
    initCarousel();
    initParticles();
    setupCrearHistoria();
    setupLogout();
    actualizarInterfazUsuario(); // AUTH + NOMBRE
});

function setupOrbMenu() {
    const toggle = document.querySelector('.orb-menu-toggle');
    const menu = document.getElementById('orb-menu');
    const items = document.querySelectorAll('#orb-items li');

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        isOrbOpen = !isOrbOpen;
        menu.style.display = isOrbOpen ? 'block' : 'none';

        items.forEach((item, i) => {
            if (isOrbOpen) {
                setTimeout(() => {
                    item.style.opacity = '1';
                    const angle = i * 40;
                    const radius = 100;
                    const x = Math.cos(angle * Math.PI / 180) * radius;
                    const y = Math.sin(angle * Math.PI / 180) * radius;
                    item.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px)`;
                }, i * 80);
            } else {
                item.style.opacity = '0';
                item.style.transform = 'translate(-50%, -50%)';
            }
        });
    });

    document.addEventListener('click', (e) => {
        if (isOrbOpen && !toggle.contains(e.target) && !menu.contains(e.target)) {
            toggle.click();
        }
    });
}

function actualizarInterfazUsuario() {
    const userStatus = document.getElementById('user-status');
    const navButtons = document.getElementById('nav-buttons');
    const logout = document.getElementById('logout');
    const crearContainer = document.getElementById('crear-container');

    if (sesion && sesion.usuario) {
        userStatus.textContent = `${sesion.usuario.nombre} ${sesion.usuario.apellido}`;
        navButtons.style.display = 'none';
        logout.style.display = 'block';
        if (sesion.usuario.rol !== 'admin') {
            crearContainer.style.display = 'block';
        }
    } else {
        userStatus.textContent = 'Invitado';
        navButtons.style.display = 'flex';
        logout.style.display = 'none';
        crearContainer.style.display = 'none';
        document.getElementById('carousel-inner').innerHTML = 
            `<p class="vacio">Inicia sesión para ver las historias</p>`;
    }
}

async function cargarHistorias() {
    try {
        const headers = sesion ? { 'Authorization': `Bearer ${sesion.token}` } : {};
        const res = await fetch('http://localhost:5000/api/historias', { headers });
        const data = await res.json();
        historias = data.historias || [];
        renderizarCarousel();
    } catch (err) {
        document.getElementById('carousel-inner').innerHTML = `<p class="error">Error cargando historias</p>`;
    }
}

function renderizarCarousel() {
    const container = document.getElementById('carousel-inner');
    container.innerHTML = '';

    if (historias.length === 0) {
        container.innerHTML = `<p class="vacio">Aún no hay historias. ¡Sé el primero!</p>`;
        return;
    }

    historias.forEach((h, i) => {
        const card = document.createElement('div');
        card.className = 'historia-3d-card';
        card.dataset.index = i;
        card.innerHTML = `
            <div class="card-inner">
                <div class="card-front">
                    <img src="${h.imagen_url || '../assets/historia-default.jpg'}" alt="Historia">
                    <div class="overlay">
                        <h3>${h.titulo}</h3>
                        <p>${h.autor}</p>
                    </div>
                </div>
                <div class="card-back">
                    <h3>${h.titulo}</h3>
                    <p class="autor">Por: ${h.autor}</p>
                    <p class="contenido">${h.contenido}</p>
                    <div class="reacciones">
                        <button data-tipo="like" data-id="${h.id}"><i class="fas fa-heart"></i> <span>${h.likes || 0}</span></button>
                        <button data-tipo="inspirado" data-id="${h.id}"><i class="fas fa-lightbulb"></i> <span>${h.inspirado || 0}</span></button>
                        <button data-tipo="compartir" data-id="${h.id}"><i class="fas fa-share"></i> Compartir</button>
                        <button class="btn-pdf" data-id="${h.id}"><i class="fas fa-file-pdf"></i> PDF</button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    setupReacciones();
    setupPDF();
    updateCarousel();
}

function updateCarousel() {
    const cards = document.querySelectorAll('.historia-3d-card');
    cards.forEach((card, i) => {
        const offset = i - currentIndex;
        const scale = offset === 0 ? 1 : 0.8;
        const z = offset === 0 ? 0 : -200;
        const opacity = offset === 0 ? 1 : 0.6;
        gsap.to(card, { scale, z, opacity, x: offset * 320, duration: 0.6, ease: "power2.out" });
    });
}

document.querySelector('.next-btn').addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % historias.length;
    updateCarousel();
});

document.querySelector('.prev-btn').addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + historias.length) % historias.length;
    updateCarousel();
});

function setupReacciones() {
    document.querySelectorAll('[data-tipo]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if (!sesion) return alert('Inicia sesión para reaccionar');
            const tipo = btn.dataset.tipo;
            const id = btn.dataset.id;
            if (tipo === 'compartir') {
                navigator.clipboard.writeText(window.location.href);
                alert('Enlace copiado!');
                return;
            }
            await fetch(`http://localhost:5000/api/historias/${id}/reaccion`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sesion.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tipo })
            });
            await cargarHistorias(); // RECARGA INMEDIATA
        });
    });
}

function setupPDF() {
    document.querySelectorAll('.btn-pdf').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const historia = historias.find(h => h.id == id);
            generarPDF(historia);
        });
    });
}

function generarPDF(historia) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.setFontSize(20);
    doc.text(historia.titulo, 20, 30);
    doc.setFontSize(12);
    doc.text(`Por: ${historia.autor}`, 20, 45);
    doc.setFontSize(10);
    const lines = doc.splitTextToSize(historia.contenido, 170);
    doc.text(lines, 20, 60);
    doc.save(`${historia.titulo.replace(/ /g, '_')}.pdf`);
}

function setupCrearHistoria() {
    const btn = document.getElementById('btn-crear-historia');
    const modal = document.getElementById('form-historia');
    const close = document.querySelector('.close-form');
    const form = document.getElementById('nueva-historia-form');

    if (!btn) return;

    btn.addEventListener('click', () => modal.style.display = 'block');
    close.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!sesion) return alert('Debes iniciar sesión');

        const formData = new FormData();
        formData.append('titulo', document.getElementById('titulo').value);
        formData.append('contenido', document.getElementById('contenido').value);
        const file = document.getElementById('imagen').files[0];
        if (file) formData.append('imagen', file);

        try {
            const res = await fetch('http://localhost:5000/api/historias', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sesion.token}` },
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                alert('¡Historia publicada al instante!');
                modal.style.display = 'none';
                form.reset();
                await cargarHistorias(); // APARECE SIN RECARGAR
            } else {
                alert(data.error || 'Error al publicar');
            }
        } catch (err) {
            alert('Error de red');
        }
    });
}

function initCarousel() {
    gsap.set('.historia-3d-card', { transformPerspective: 1000, transformStyle: "preserve-3d" });
}

function initParticles() {
    const canvas = document.querySelector('.particle-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    for (let i = 0; i < 80; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 4 + 1,
            speedX: Math.random() * 2 - 1,
            speedY: Math.random() * 2 - 1,
            color: `hsl(${Math.random() * 60 + 200}, 70%, 60%)`
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;
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
}

function setupLogout() {
    const logout = document.getElementById('logout');
    if (logout) {
        logout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = '../html/login.html';
        });
    }
}