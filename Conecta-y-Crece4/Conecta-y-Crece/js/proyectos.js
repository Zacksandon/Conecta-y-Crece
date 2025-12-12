// frontend/js/proyectos.js
const orbToggle = document.querySelector('.orb-menu-toggle');
const orbMenu = document.querySelector('.orb-menu');
const orbItems = document.querySelectorAll('.orb-items li');
const userStatus = document.getElementById('user-status');
const logout = document.getElementById('logout');
let isOpen = false;

// === MENÚ ORBES ANIMADO ===
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

// === AUTENTICACIÓN ===
document.addEventListener('DOMContentLoaded', async () => {
    const sesion = verificarSesion();
    if (!sesion) {
        document.querySelector('.nav-buttons').style.display = 'flex';
        document.getElementById('logout').style.display = 'none';
    } else {
        document.querySelector('.nav-buttons').style.display = 'none';
        document.getElementById('logout').style.display = 'block';
        userStatus.innerHTML = `
            <div class="user-info">
                <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" class="user-avatar">
                <span class="user-name">${sesion.usuario.nombre}</span>
            </div>
        `;
    }

    logout.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('sesion');
        window.location.href = '../html/index.html';
    });

    await cargarProyectos(sesion?.token);
    setupFiltros();
    setupModalCrear();
    setupModalDetalles();
});

// === CARGAR PROYECTOS DESDE API ===
async function cargarProyectos(token) {
    try {
        const response = await fetch('http://localhost:5000/api/proyectos', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const proyectos = await response.json();
        const contenedor = document.getElementById('proyectos-listado');
        contenedor.innerHTML = '';

        proyectos.forEach(p => {
            const card = document.createElement('div');
            card.className = 'proyecto-card';
            card.dataset.id = p.id;
            card.innerHTML = `
                <div class="imagen-proyecto" style="background: linear-gradient(135deg, #${Math.floor(Math.random()*16777215).toString(16)}, #${Math.floor(Math.random()*16777215).toString(16)});"></div>
                <h3>${p.titulo}</h3>
                <p class="categoria">${p.categoria}</p>
                <p class="descripcion">${p.descripcion}</p>
                <p class="emprendedor">${p.emprendedor}</p>
                <p class="fecha">${new Date(p.fecha).toLocaleDateString('es-CO')}</p>
                <p class="progreso">Progreso: ${p.progreso}%</p>
                <button class="btn-detalles">Ver Detalles</button>
                <div class="reacciones" data-id="${p.id}"></div>
            `;
            contenedor.appendChild(card);
        });

        await cargarReacciones(proyectos.map(p => p.id), token);
        setupReacciones(token);
        setupHoverCards();
    } catch (error) {
        console.error('Error:', error);
    }
}

// === REACCIONES EN BD ===
async function cargarReacciones(proyectoIds, token) {
    for (const id of proyectoIds) {
        try {
            const res = await fetch(`http://localhost:5000/api/reacciones/${id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const counts = await res.json();
            const reaccionesDiv = document.querySelector(`.reacciones[data-id="${id}"]`);
            reaccionesDiv.innerHTML = `
                <button class="btn-reaccion" data-reaction="me-gusta">Like <span>${counts['me-gusta'] || 0}</span></button>
                <button class="btn-reaccion" data-reaction="me-encanta">Love <span>${counts['me-encanta'] || 0}</span></button>
                <button class="btn-reaccion" data-reaction="me-interesa">Idea <span>${counts['me-interesa'] || 0}</span></button>
                <button class="btn-reaccion" data-reaction="apoyo">Support <span>${counts['apoyo'] || 0}</span></button>
            `;
        } catch (e) {}
    }
}

function setupReacciones(token) {
    document.querySelectorAll('.btn-reaccion').forEach(btn => {
        btn.addEventListener('click', async () => {
            const proyectoId = btn.closest('.reacciones').dataset.id;
            const tipo = btn.dataset.reaction;
            const span = btn.querySelector('span');
            const sesion = verificarSesion();
            if (!sesion) return alert('Debes iniciar sesión');

            try {
                await fetch('http://localhost:5000/api/reacciones', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${sesion.token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        proyecto_id: proyectoId,
                        usuario_id: sesion.usuario.id,
                        tipo_reaccion: tipo
                    })
                });
                span.textContent = parseInt(span.textContent) + 1;
                btn.style.background = '#00BFFF';
                setTimeout(() => btn.style.background = '', 500);
            } catch (e) {
                alert('Error al reaccionar');
            }
        });
    });
}

// === FILTROS ===
function setupFiltros() {
    const busqueda = document.querySelector('.busqueda');
    const categoria = document.querySelector('.categorias');
    const btnBuscar = document.querySelector('.btn-buscar');

    const filtrar = () => {
        const termino = busqueda.value.toLowerCase();
        const cat = categoria.value;
        document.querySelectorAll('.proyecto-card').forEach(card => {
            const titulo = card.querySelector('h3').textContent.toLowerCase();
            const emprendedor = card.querySelector('.emprendedor').textContent.toLowerCase();
            const categoriaCard = card.querySelector('.categoria').textContent.toLowerCase();
            const visible = (titulo.includes(termino) || emprendedor.includes(termino)) && (!cat || categoriaCard === cat);
            card.style.display = visible ? 'block' : 'none';
        });
    };

    busqueda.addEventListener('input', filtrar);
    categoria.addEventListener('change', filtrar);
    btnBuscar.addEventListener('click', filtrar);
}

// === MODAL CREAR PROYECTO ===
function setupModalCrear() {
    const btnCrear = document.querySelector('.btn-crear-proyecto');
    const modal = document.getElementById('modal-crear');
    const cerrar = modal.querySelector('.cerrar-modal');
    const form = document.getElementById('form-crear-proyecto');

    btnCrear.addEventListener('click', () => {
        const sesion = verificarSesion();
        if (!sesion) return alert('Debes iniciar sesión');
        modal.style.display = 'block';
        gsap.from(modal.querySelector('.modal-contenido'), { scale: 0, duration: 0.5, ease: "back.out(1.7)" });
    });

    cerrar.addEventListener('click', () => {
        gsap.to(modal.querySelector('.modal-contenido'), { scale: 0, duration: 0.5, onComplete: () => modal.style.display = 'none' });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const sesion = verificarSesion();
        const formData = new FormData(form);
        const data = {
            titulo: formData.getAll('input')[0].value,
            descripcion: formData.getAll('textarea')[0].value,
            categoria_id: ['tecnologia','salud','educacion','medioambiente','emprendimiento'].indexOf(formData.getAll('select')[0].value) + 1,
            fecha_inicio: formData.getAll('input')[1].value,
            progreso: 0,
            usuario_id: sesion.usuario.id
        };

        try {
            const res = await fetch('http://localhost:5000/api/proyectos', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sesion.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                alert('Proyecto creado!');
                modal.style.display = 'none';
                cargarProyectos(sesion.token);
            }
        } catch (e) {
            alert('Error al crear proyecto');
        }
    });
}

// === MODAL DETALLES ===
function setupModalDetalles() {
    const modal = document.getElementById('modal-detalles');
    const cerrar = modal.querySelector('.cerrar-modal');

    document.querySelectorAll('.btn-detalles').forEach(btn => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.proyecto-card');
            document.querySelector('.titulo-modal').textContent = card.querySelector('h3').textContent;
            document.querySelector('.descripcion-modal').textContent = card.querySelector('.descripcion').textContent;
            document.querySelector('.emprendedor-modal').textContent = `Emprendedor: ${card.querySelector('.emprendedor').textContent}`;
            document.querySelector('.fecha-modal').textContent = card.querySelector('.fecha').textContent;
            document.querySelector('.progreso-modal').textContent = card.querySelector('.progreso').textContent;
            document.querySelector('.reacciones-modal').innerHTML = card.querySelector('.reacciones').innerHTML;

            gsap.from(modal.querySelector('.modal-contenido'), { scale: 0, opacity: 0, duration: 0.5 });
            modal.style.display = 'block';
        });
    });

    cerrar.addEventListener('click', () => {
        gsap.to(modal.querySelector('.modal-contenido'), { scale: 0, opacity: 0, duration: 0.5, onComplete: () => modal.style.display = 'none' });
    });
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            gsap.to(modal.querySelector('.modal-contenido'), { scale: 0, opacity: 0, duration: 0.5, onComplete: () => modal.style.display = 'none' });
        }
    });
}

// === HOVER CARDS ===
function setupHoverCards() {
    document.querySelectorAll('.proyecto-card').forEach(card => {
        card.addEventListener('mouseover', () => {
            gsap.to(card, { scale: 1.05, boxShadow: '0 0 35px #00BFFF, 0 0 25px #FF3B9E', duration: 0.3 });
        });
        card.addEventListener('mouseout', () => {
            gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.3 });
        });
    });
}