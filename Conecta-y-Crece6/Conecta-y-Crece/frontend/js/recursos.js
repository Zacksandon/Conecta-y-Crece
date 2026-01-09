const sesion = verificarSesion();
let isOrbOpen = false;

document.addEventListener('DOMContentLoaded', () => {
    setupOrbMenu();
    actualizarInterfazUsuario();
    cargarRecursos();
    initParticles();
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

    if (sesion && sesion.usuario) {
        userStatus.textContent = `${sesion.usuario.nombre} ${sesion.usuario.apellido}`;
        navButtons.style.display = 'none';
        logout.style.display = 'block';
    } else {
        userStatus.textContent = 'Invitado';
        navButtons.style.display = 'flex';
        logout.style.display = 'none';
    }

    logout.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.clear();
        window.location.href = '../html/login.html';
    });
}

async function cargarRecursos() {
    const container = document.getElementById('recursos-container');
    try {
        const res = await fetch('http://localhost:5000/api/recursos');
        const data = await res.json();

        if (!data.recursos || data.recursos.length === 0) {
            container.innerHTML = '<p class="vacio">No hay recursos disponibles.</p>';
            return;
        }

        container.innerHTML = '';
        data.recursos.forEach(r => {
            const card = document.createElement('div');
            card.className = 'recurso-card';
            card.innerHTML = `
                <h3>${r.titulo}</h3>
                <p class="descripcion">${r.descripcion}</p>
                <button class="btn-descargar" data-id="${r.id}">
                    <i class="fas fa-download"></i> Descargar PDF
                </button>
            `;
            container.appendChild(card);

            // Hover animado
            card.addEventListener('mouseover', () => {
                gsap.to(card, { scale: 1.05, boxShadow: '0 0 30px #00BFFF, 0 0 40px #FF3B9E', duration: 0.3 });
            });
            card.addEventListener('mouseout', () => {
                gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.3 });
            });
        });

        setupDescargas();
    } catch (err) {
        container.innerHTML = '<p class="error">Error al cargar recursos</p>';
    }
}

function setupDescargas() {
    document.querySelectorAll('.btn-descargar').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            try {
                const res = await fetch(`http://localhost:5000/api/recursos/${id}`);
                const recurso = await res.json();

                generarPDF(recurso);
                alert(`¡PDF "${recurso.titulo}" generado!`);
            } catch (err) {
                alert('Error al generar PDF');
            }
        });
    });
}

function generarPDF(recurso) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    doc.setFontSize(22);
    doc.setTextColor(155, 38, 255);
    doc.text(recurso.titulo, 20, 30);

    doc.setFontSize(12);
    doc.setTextColor(0, 191, 255);
    doc.text('Conecta & Crece - Recursos para Emprendedores', 20, 45);

    doc.setFontSize(11);
    doc.setTextColor(255, 255, 255);
    const lines = doc.splitTextToSize(recurso.contenido || recurso.descripcion, 170);
    doc.text(lines, 20, 60);

    doc.setFontSize(10);
    doc.setTextColor(150, 150, 150);
    doc.text(`Generado el: ${new Date().toLocaleDateString('es-CO')}`, 20, 280);

    doc.save(`${recurso.titulo.replace(/[^a-z0-9]/gi, '_')}.pdf`);
}

function initParticles() {
    const canvas = document.querySelector('.particle-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    for (let i = 0; i < 70; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 3 + 1,
            speedX: Math.random() * 1.5 - 0.75,
            speedY: Math.random() * 1.5 - 0.75,
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