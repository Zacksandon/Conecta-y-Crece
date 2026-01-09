// frontend/js/proyectos.js
document.addEventListener('DOMContentLoaded', async () => {
  const sesion = verificarSesion();
  if (!sesion) {
    const navButtons = document.querySelector('.nav-buttons');
    if (navButtons) navButtons.style.display = 'flex';
    const logout = document.getElementById('logout');
    if (logout) logout.style.display = 'none';
  } else {
    const navButtons = document.querySelector('.nav-buttons');
    if (navButtons) navButtons.style.display = 'none';
    const logout = document.getElementById('logout');
    if (logout) logout.style.display = 'block';
    const userStatus = document.getElementById('user-status');
    if (userStatus) userStatus.innerHTML = `
      <div class="user-info">
        <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" class="user-avatar" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">
        <span class="user-name">${sesion.usuario.nombre}</span>
      </div>`;
  }

  const logoutBtn = document.getElementById('logout');
  if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
          e.preventDefault();
          localStorage.removeItem('token');
          localStorage.removeItem('usuario');
          window.location.href = '../html/index.html';
      });
  }

  setupOrb(); // activa menú orb
  await cargarProyectos();
  setupFiltros();
  setupModalCrear();
  setupModalEditar();
  setupModalDetalles();
});

function setupOrb() {
    const orbToggle = document.querySelector('.orb-menu-toggle');
    const orbItems = document.querySelectorAll('.orb-items li');
    let isOpen = false;
    if (!orbToggle) return;
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
                delay: index * 0.05,
                ease: "back.out(1.7)",
                rotation: isOpen ? 360 : 0
            });
        });
        orbToggle.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
    });
}

// === CARGAR PROYECTOS ===
async function cargarProyectos() {
  try {
    const sesion = verificarSesion();
    const token = sesion ? sesion.token : null;
    const res = await fetch('http://localhost:5000/api/proyectos', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (!res.ok) {
      console.error('Error cargando proyectos', res.status);
      return;
    }
    const proyectos = await res.json();
    const contenedor = document.getElementById('proyectos-listado');
    contenedor.innerHTML = '';

    proyectos.forEach((p) => renderProyecto(p, contenedor, sesion));
    setupHoverCards();
    setupReaccionesUI();
  } catch (e) {
    console.error(e);
  }
}

function renderProyecto(p, contenedor, sesion) {
  const card = document.createElement('div');
  card.className = 'proyecto-card';
  card.dataset.id = p.id;

  const sesionNombre = sesion ? `${sesion.usuario.nombre} ${sesion.usuario.apellido}` : '';
  const esPropio = sesion && p.emprendedor && p.emprendedor.includes(sesion.usuario.nombre);

  const imagenStyle = p.imagen_principal_url ? `background-image: url('${p.imagen_principal_url}')` :
    `background: linear-gradient(135deg, #${Math.floor(Math.random()*16777215).toString(16)}, #${Math.floor(Math.random()*16777215).toString(16)})`;

  card.innerHTML = `
    <div class="imagen-proyecto" style="${imagenStyle}"></div>
    <h3>${p.titulo}</h3>
    <p class="categoria">${p.categoria}</p>
    <p class="descripcion">${p.descripcion}</p>
    <p class="emprendedor">${p.emprendedor}</p>
    <p class="fecha">${new Date(p.fecha).toLocaleDateString('es-CO')}</p>
    <p class="progreso">Progreso: ${p.progreso}%</p>
    <div class="acciones-card">
      <button class="btn-detalles">Ver Detalles</button>
      ${esPropio ? '<button class="btn-editar">Editar</button>' : ''}
    </div>
    <div class="reacciones" data-id="${p.id}"></div>
  `;
  contenedor.prepend(card);

  // eventos
  const btnDet = card.querySelector('.btn-detalles');
  if (btnDet) btnDet.addEventListener('click', () => abrirDetallesById(p.id));

  const btnEdit = card.querySelector('.btn-editar');
  if (btnEdit) btnEdit.addEventListener('click', () => abrirEditarById(p.id));
}

// === REACCIONES (carga de contador visual)
async function setupReaccionesUI() {
  const reaccionesDivs = document.querySelectorAll('.reacciones[data-id]');
  const sesion = verificarSesion();
  for (const div of reaccionesDivs) {
    const id = div.dataset.id;
    try {
      const res = await fetch(`http://localhost:5000/api/reacciones/${id}`);
      if (!res.ok) continue;
      const counts = await res.json();
      div.innerHTML = `
        <button class="btn-reaccion" data-reaction="me_gusta">Like <span>${counts['me_gusta']||0}</span></button>
        <button class="btn-reaccion" data-reaction="me_encanta">Love <span>${counts['me_encanta']||0}</span></button>
        <button class="btn-reaccion" data-reaction="me_interesa">Idea <span>${counts['me_interesa']||0}</span></button>
        <button class="btn-reaccion" data-reaction="apoyo">Support <span>${counts['apoyo']||0}</span></button>
      `;
      // listeners
      div.querySelectorAll('.btn-reaccion').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (!sesion) return alert('Debes iniciar sesión');
          const tipo = btn.dataset.reaction;
          try {
            const resp = await fetch('http://localhost:5000/api/reacciones', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${sesion.token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ proyecto_id: id, tipo_reaccion: tipo })
            });
            if (!resp.ok) {
              const er = await resp.json();
              throw new Error(er.error || 'Error reaccionando');
            }
            const span = btn.querySelector('span');
            span.textContent = parseInt(span.textContent || '0') + 1;
          } catch (e) {
            alert('Error: ' + e.message);
          }
        });
      });
    } catch (e) {
      // ignore per-project errors
    }
  }
}

// === FILTROS ===
function setupFiltros() {
  const busqueda = document.querySelector('.busqueda');
  const categoria = document.querySelector('.categorias');
  const btnBuscar = document.querySelector('.btn-buscar');

  const filtrar = () => {
    const termino = (busqueda && busqueda.value.toLowerCase()) || '';
    const catText = (categoria && categoria.options[categoria.selectedIndex].text.toLowerCase()) || '';
    document.querySelectorAll('.proyecto-card').forEach((card) => {
      const titulo = card.querySelector('h3').textContent.toLowerCase();
      const emprendedor = card.querySelector('.emprendedor').textContent.toLowerCase();
      const categoriaCard = (card.querySelector('.categoria') && card.querySelector('.categoria').textContent.toLowerCase()) || '';
      const visible =
        (titulo.includes(termino) || emprendedor.includes(termino)) &&
        (catText === 'todas las categorías' || catText === '' || categoriaCard === catText);
      card.style.display = visible ? 'block' : 'none';
    });
  };

  if (busqueda) busqueda.addEventListener('input', filtrar);
  if (categoria) categoria.addEventListener('change', filtrar);
  if (btnBuscar) btnBuscar.addEventListener('click', filtrar);
}

// === MODAL CREAR ===
function setupModalCrear() {
  const btnCrear = document.querySelector('.btn-crear-proyecto');
  const modal = document.getElementById('modal-crear');
  const cerrar = modal ? modal.querySelector('#cerrar-modal-crear') : null;
  const form = document.getElementById('form-crear-proyecto');

  if (!btnCrear || !modal || !form) return;

  btnCrear.addEventListener('click', () => {
    const sesion = verificarSesion();
    if (!sesion) return alert('Debes iniciar sesión');
    modal.style.display = 'flex';
  });

  if (cerrar) cerrar.addEventListener('click', () => (modal.style.display = 'none'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const sesion = verificarSesion();
    if (!sesion) return alert('Debes iniciar sesión');
    const fd = new FormData(form);
    try {
      const res = await fetch('http://localhost:5000/api/proyectos', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sesion.token}` },
        body: fd
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Error creando proyecto');
      }
      const nuevo = await res.json();
      // recargar lista
      modal.style.display = 'none';
      form.reset();
      await cargarProyectos();
      alert('Proyecto creado exitosamente 🎉');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
}

// === EDITAR ===
function setupModalEditar() {
  const modal = document.getElementById('modal-editar');
  const cerrar = modal ? modal.querySelector('#cerrar-modal-editar') : null;
  const form = document.getElementById('form-editar-proyecto');
  if (!modal || !form) return;

  if (cerrar) cerrar.addEventListener('click', () => (modal.style.display = 'none'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const sesion = verificarSesion();
    if (!sesion) return alert('Debes iniciar sesión');
    const id = form['edit-id'].value;
    const fd = new FormData();
    // si quieres aceptar archivos aquí debes adaptar form con inputs file
    fd.append('titulo', form['edit-titulo'].value);
    fd.append('descripcion', form['edit-descripcion'].value);
    fd.append('categoria_id', form['edit-categoria_id'].value);
    fd.append('progreso', form['edit-progreso'].value);

    try {
      const res = await fetch(`http://localhost:5000/api/proyectos/${id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${sesion.token}` },
        body: fd
      });
      if (!res.ok) {
        const er = await res.json();
        throw new Error(er.error || 'Error actualizando proyecto');
      }
      alert('Proyecto actualizado ✅');
      modal.style.display = 'none';
      await cargarProyectos();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  });
}

async function abrirEditarById(id) {
  try {
    const sesion = verificarSesion();
    if (!sesion) return alert('Debes iniciar sesión');
    const res = await fetch(`http://localhost:5000/api/proyectos/${id}`, {
      headers: { 'Authorization': `Bearer ${sesion.token}` }
    });
    if (!res.ok) throw new Error('No se pudo obtener proyecto');
    const p = await res.json();
    document.getElementById('edit-id').value = p.id;
    document.getElementById('edit-titulo').value = p.titulo;
    document.getElementById('edit-descripcion').value = p.descripcion;
    document.getElementById('edit-categoria_id').value = p.categoria_id || 1;
    document.getElementById('edit-progreso').value = p.progreso || 0;
    document.getElementById('modal-editar').style.display = 'flex';
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// === DETALLES ===
function setupModalDetalles() {
  const modal = document.getElementById('modal-detalles');
  const cerrar = modal ? modal.querySelector('#cerrar-modal-detalles') : null;
  if (!modal) return;
  if (cerrar) cerrar.addEventListener('click', () => (modal.style.display = 'none'));
}

async function abrirDetallesById(id) {
  try {
    const sesion = verificarSesion();
    const token = sesion ? sesion.token : null;
    const res = await fetch(`http://localhost:5000/api/proyectos/${id}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (!res.ok) throw new Error('No se pudo obtener proyecto');
    const p = await res.json();
    abrirDetalles(p);
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

function abrirDetalles(p) {
  const modal = document.getElementById('modal-detalles');
  modal.querySelector('.titulo-modal').textContent = p.titulo;
  modal.querySelector('.descripcion-modal').textContent = p.descripcion;
  modal.querySelector('.emprendedor-modal').textContent = `Emprendedor: ${p.emprendedor}`;
  modal.querySelector('.fecha-modal').textContent = `Publicado: ${new Date(p.fecha).toLocaleDateString('es-CO')}`;
  modal.querySelector('.progreso-modal').textContent = `Progreso: ${p.progreso}%`;
  modal.style.display = 'flex';
}

// === HOVER CARDS ===
function setupHoverCards() {
  document.querySelectorAll('.proyecto-card').forEach(card => {
    card.addEventListener('mouseover', () => {
      gsap.to(card, { scale: 1.03, boxShadow: '0 0 35px #00BFFF, 0 0 25px #FF3B9E', duration: 0.25 });
    });
    card.addEventListener('mouseout', () => {
      gsap.to(card, { scale: 1, boxShadow: '0 0 15px #00BFFF', duration: 0.25 });
    });
  });
}
