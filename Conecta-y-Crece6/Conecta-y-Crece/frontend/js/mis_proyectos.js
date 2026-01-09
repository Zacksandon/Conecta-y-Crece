// mis_proyectos.js
document.addEventListener('DOMContentLoaded', async () => {
    const sesion = verificarSesion();
    if (!sesion) {
        document.getElementById('mis-proyectos-container').innerHTML = '<p class="vacio">Debes iniciar sesión para ver y gestionar tus proyectos</p>';
        return;
    }
    setupUI(sesion);
    await cargarMisProyectos(sesion.token);
    setupFormHandlers(sesion);
});

function setupUI(sesion) {
    const userStatus = document.getElementById('user-status');
    if (userStatus) userStatus.innerHTML = `
        <div class="user-info">
            <img src="${sesion.usuario.foto_url || '../assets/default-avatar.png'}" class="user-avatar" />
            <span>${sesion.usuario.nombre}</span>
        </div>
    `;
    const btnNuevo = document.getElementById('btn-nuevo');
    btnNuevo.addEventListener('click', () => {
        abrirModalCrear();
    });
    // cerrar modales
    document.getElementById('cerrar-modal').addEventListener('click', () => cerrarModal('modal-form'));
    document.getElementById('cerrar-detalle').addEventListener('click', () => cerrarModal('modal-detalle'));
    document.getElementById('btn-cancel')?.addEventListener('click', () => cerrarModal('modal-form'));
}

async function cargarMisProyectos(token) {
    const container = document.getElementById('mis-proyectos-container');
    container.innerHTML = '<p class="vacio">Cargando tus proyectos...</p>';
    try {
        const res = await fetch('http://localhost:5000/api/mis_proyectos', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            const j = await res.json();
            throw new Error(j.error || 'Error al obtener proyectos');
        }
        const data = await res.json();
        if (!data.proyectos || data.proyectos.length === 0) {
            container.innerHTML = '<p class="vacio">No tienes proyectos aún</p>';
            return;
        }
        container.innerHTML = '';
        data.proyectos.forEach(p => {
            container.appendChild(crearCardProyecto(p));
        });
    } catch (e) {
        container.innerHTML = `<p class="vacio error">Error: ${e.message}</p>`;
        console.error(e);
    }
}

function crearCardProyecto(p) {
    const card = document.createElement('div');
    card.className = 'card-proyecto';
    card.dataset.id = p.id;
    const imgHtml = p.imagen_url ? `<div class="thumb" style="background-image:url('${p.imagen_url}')"></div>` : `<div class="thumb placeholder">Sin imagen</div>`;
    card.innerHTML = `
        ${imgHtml}
        <div class="info">
            <h3>${p.titulo}</h3>
            <p class="estado">Estado: <strong>${p.estado || 'borrador'}</strong></p>
            <p class="progreso">Progreso: ${p.progreso || 0}%</p>
            <div class="acciones">
                <button class="btn-ver">Ver</button>
                <button class="btn-editar">Editar</button>
                <button class="btn-eliminar">Eliminar</button>
                <button class="btn-duplicar">Duplicar</button>
                <button class="btn-toggle">${p.estado === 'publicado' ? 'Ocultar' : 'Publicar'}</button>
                <button class="btn-stats">Stats</button>
            </div>
        </div>
    `;
    // eventos
    card.querySelector('.btn-ver').addEventListener('click', () => verDetalle(p.id));
    card.querySelector('.btn-editar').addEventListener('click', () => abrirModalEditar(p));
    card.querySelector('.btn-eliminar').addEventListener('click', () => eliminarProyecto(p.id));
    card.querySelector('.btn-duplicar').addEventListener('click', () => duplicarProyecto(p.id));
    card.querySelector('.btn-toggle').addEventListener('click', (e) => togglePublicacion(p.id, e.target));
    card.querySelector('.btn-stats').addEventListener('click', () => mostrarStats(p.id));
    return card;
}

function abrirModalCrear() {
    const modal = document.getElementById('modal-form');
    document.getElementById('modal-title').textContent = 'Crear Proyecto';
    document.getElementById('form-proyecto').reset();
    document.getElementById('proyecto_id').value = '';
    modal.style.display = 'flex';
}

function abrirModalEditar(p) {
    const modal = document.getElementById('modal-form');
    document.getElementById('modal-title').textContent = 'Editar Proyecto';
    document.getElementById('proyecto_id').value = p.id;
    document.getElementById('titulo').value = p.titulo || '';
    document.getElementById('descripcion').value = p.descripcion || '';
    document.getElementById('categoria_id').value = p.categoria_id || '';
    document.getElementById('progreso').value = p.progreso || 0;
    document.getElementById('sitio_web').value = p.sitio_web || '';
    document.getElementById('contacto').value = p.contacto || '';
    document.getElementById('telefono_proyecto').value = p.telefono_proyecto || '';
    document.getElementById('redes').value = p.redes_sociales || '';
    modal.style.display = 'flex';
}

function cerrarModal(id) {
    document.getElementById(id).style.display = 'none';
}

function setupFormHandlers(sesion) {
    const form = document.getElementById('form-proyecto');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = verificarSesion().token;
        const id = document.getElementById('proyecto_id').value;
        const formData = new FormData(form);
        try {
            let url = 'http://localhost:5000/api/proyectos';
            let method = 'POST';
            if (id) {
                // editar: usamos PUT json patch (no archivos)
                // si hay archivos, podríamos usar multipart POST a otro endpoint; aquí simplificamos:
                method = 'PUT';
                url = `http://localhost:5000/api/proyectos/${id}`;
                // convert formData to json
                const obj = {};
                formData.forEach((v,k) => { if (k !== 'imagen_principal' && k !== 'video_pitch') obj[k] = v; });
                const res = await fetch(url, {
                    method: method,
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(obj)
                });
                if (!res.ok) {
                    const j = await res.json();
                    throw new Error(j.error || 'Error actualizando');
                }
            } else {
                // Crear con archivos -> multipart/form-data handler en API
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });
                if (!res.ok) {
                    const j = await res.json();
                    throw new Error(j.error || 'Error creando proyecto');
                }
            }
            alert('Operación realizada con éxito');
            cerrarModal('modal-form');
            await cargarMisProyectos(token);
        } catch (err) {
            alert('Error: ' + err.message);
            console.error(err);
        }
    });
}

async function eliminarProyecto(id) {
    if (!confirm('¿Eliminar proyecto?')) return;
    const token = verificarSesion().token;
    try {
        const res = await fetch(`http://localhost:5000/api/proyectos/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.error || 'Error eliminando');
        alert(j.message || 'Eliminado');
        await cargarMisProyectos(token);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function duplicarProyecto(id) {
    const token = verificarSesion().token;
    try {
        const res = await fetch(`http://localhost:5000/api/proyectos/${id}/duplicar`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.error || 'Error duplicando');
        alert('Proyecto duplicado');
        await cargarMisProyectos(token);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function togglePublicacion(id, btnEl) {
    const token = verificarSesion().token;
    try {
        const res = await fetch(`http://localhost:5000/api/proyectos/${id}/toggle_publicacion`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.error || 'Error cambiando estado');
        alert('Estado cambiado: ' + j.nuevo);
        btnEl.textContent = j.nuevo === 'publicado' ? 'Ocultar' : 'Publicar';
        await cargarMisProyectos(token);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function verDetalle(id) {
    try {
        const res = await fetch(`http://localhost:5000/api/proyectos/${id}`);
        if (!res.ok) {
            const j = await res.json();
            throw new Error(j.error || 'No encontrado');
        }
        const p = await res.json();
        const modal = document.getElementById('modal-detalle');
        document.getElementById('detalle-title').textContent = p.titulo;
        let html = `<p>${p.descripcion || ''}</p>`;
        if (p.imagen_url) html += `<img src="${p.imagen_url}" style="max-width:100%;border-radius:8px;margin-top:8px">`;
        if (p.video_url) html += `<div style="margin-top:8px"><video controls src="${p.video_url}" style="width:100%;max-height:300px"></video></div>`;
        html += `<p><strong>Contacto:</strong> ${p.contacto || '-'}</p>`;
        html += `<p><strong>Redes:</strong> ${p.redes_sociales || '-'}</p>`;
        html += `<p><strong>Detalles:</strong> ${p.detalles_ampliados || '-'}</p>`;
        document.getElementById('detalle-body').innerHTML = html;
        modal.style.display = 'flex';
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function mostrarStats(id) {
    try {
        const res = await fetch(`http://localhost:5000/api/proyectos/${id}/stats`);
        if (!res.ok) {
            const j = await res.json();
            throw new Error(j.error || 'Error stats');
        }
        const j = await res.json();
        alert(`Reacciones: ${j.reacciones}\nApoyos (sum): ${j.apoyos}`);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}
