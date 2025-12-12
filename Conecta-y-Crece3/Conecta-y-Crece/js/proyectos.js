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

    // Filtrado dinámico
    const busquedaInput = document.querySelector('.busqueda');
    const categoriasSelect = document.querySelector('.categorias');
    const btnBuscar = document.querySelector('.btn-buscar');
    const proyectos = document.querySelectorAll('.proyecto-card');

    const filtrarProyectos = () => {
        const termino = busquedaInput.value.toLowerCase();
        const categoria = categoriasSelect.value;
        proyectos.forEach(card => {
            const titulo = card.querySelector('h3').textContent.toLowerCase();
            const emprendedor = card.querySelector('.emprendedor').textContent.toLowerCase();
            const cat = card.querySelector('.categoria').textContent.toLowerCase();
            const coincideBusqueda = titulo.includes(termino) || emprendedor.includes(termino);
            const coincideCategoria = !categoria || cat === categoria;
            card.style.display = coincideBusqueda && coincideCategoria ? 'block' : 'none';
        });
    };

    busquedaInput.addEventListener('input', filtrarProyectos);
    categoriasSelect.addEventListener('change', filtrarProyectos);
    btnBuscar.addEventListener('click', filtrarProyectos);

    // Modal de detalles
    const modal = document.getElementById('modal-detalles');
    const modalContenido = document.querySelector('.modal-contenido');
    const cerrarModal = document.querySelector('.cerrar-modal');

    document.querySelectorAll('.btn-detalles').forEach(button => {
        button.addEventListener('click', () => {
            const card = button.closest('.proyecto-card');
            const titulo = card.querySelector('h3').textContent;
            const descripcion = card.querySelector('.descripcion').textContent;
            const emprendedor = card.querySelector('.emprendedor').textContent;
            const fecha = card.querySelector('.fecha').textContent;
            const progreso = card.querySelector('.progreso').textContent;
            const reacciones = card.querySelector('.reacciones').innerHTML;

            document.querySelector('.titulo-modal').textContent = titulo;
            document.querySelector('.descripcion-modal').textContent = descripcion;
            document.querySelector('.emprendedor-modal').textContent = `Emprendedor: ${emprendedor}`;
            document.querySelector('.fecha-modal').textContent = `Fecha: ${fecha}`;
            document.querySelector('.progreso-modal').textContent = progreso;
            document.querySelector('.reacciones-modal').innerHTML = reacciones;

            gsap.from(modalContenido, { scale: 0, opacity: 0, duration: 0.5, ease: "back.out(1.7)" });
            modal.style.display = 'block';
        });
    });

    cerrarModal.addEventListener('click', () => {
        gsap.to(modalContenido, { scale: 0, opacity: 0, duration: 0.5, onComplete: () => modal.style.display = 'none' });
    });
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            gsap.to(modalContenido, { scale: 0, opacity: 0, duration: 0.5, onComplete: () => modal.style.display = 'none' });
        }
    });

    // Reacciones con persistencia
    document.querySelectorAll('.btn-reaccion').forEach(button => {
        button.addEventListener('click', () => {
            const span = button.querySelector('span');
            const projectId = button.closest('.proyecto-card').querySelector('h3').textContent;
            let reactions = JSON.parse(localStorage.getItem('reactions') || '{}');
            reactions[projectId] = reactions[projectId] || {};
            const reactionType = button.getAttribute('data-reaction');
            reactions[projectId][reactionType] = (reactions[projectId][reactionType] || 0) + 1;
            localStorage.setItem('reactions', JSON.stringify(reactions));
            span.textContent = reactions[projectId][reactionType];
            button.style.background = '#00BFFF';
            setTimeout(() => button.style.background = '', 500);
        });
    });

    // Animación de hover en tarjetas
    const cards = document.querySelectorAll('.proyecto-card');
    cards.forEach(card => {
        card.addEventListener('mouseover', () => {
            gsap.to(card, { scale: 1.05, boxShadow: '0 0 25px #00BFFF, 0 0 35px #FF3B9E', duration: 0.3 });
        });
        card.addEventListener('mouseout', () => {
            gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.3 });
        });
    });

    // Botón crear proyecto (simulado)
    const btnCrearProyecto = document.querySelector('.btn-crear-proyecto');
    btnCrearProyecto.addEventListener('click', () => {
        if (user.nombre === 'Invitado') {
            alert('Debes iniciar sesión para crear un proyecto.');
        } else {
            alert(`¡Bienvenido, ${user.nombre}! Redirigiendo al formulario de creación de proyectos... (Función en desarrollo)`);
            // Aquí podrías redirigir a un formulario o página de creación
        }
    });
});