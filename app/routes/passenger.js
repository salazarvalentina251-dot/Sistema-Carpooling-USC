// ===== Pestañas de "Mis reservas" =====
const tabs = document.getElementById('tabs');
if (tabs) {
    const cards = document.querySelectorAll('.reserva');
    const empty = document.getElementById('empty');
    const filtrar = (grupo) => {
        let visibles = 0;
        cards.forEach(c => {
            const ok = c.dataset.group === grupo || (grupo === 'proximas' && c.dataset.group === 'pendientes');
            c.hidden = !ok;
            if (ok) visibles++;
        });
        empty.hidden = visibles > 0;
    };
    tabs.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        tabs.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        filtrar(tab.dataset.filter);
    });
    filtrar('proximas');
}

// ===== Código de abordaje (botones con clase .btn-codigo y data-id) =====
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-codigo');
    if (!btn) return;
    try {
        const res = await fetch(`/pasajero/reservas/${btn.dataset.id}/codigo`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'No se pudo obtener el código.');

        const dlg = document.createElement('dialog');
        dlg.style.cssText = 'background:var(--surface);color:var(--text);border:1px solid var(--border);' +
            'border-radius:16px;padding:28px;text-align:center;min-width:280px';
        dlg.innerHTML = '<small></small><p class="display gold" style="letter-spacing:.2em;margin:12px 0"></p>' +
            '<p class="muted small"></p><button class="btn-outline" style="margin-top:18px">Cerrar</button>';
        dlg.querySelector('small').textContent = 'CÓDIGO DE ABORDAJE';
        dlg.querySelector('.display').textContent = data.codigo;
        dlg.querySelector('.muted').textContent = `${data.ruta} · ${data.cuando}`;
        dlg.querySelector('button').addEventListener('click', () => dlg.close());
        dlg.addEventListener('close', () => dlg.remove());
        document.body.appendChild(dlg);
        dlg.showModal();
    } catch (err) {
        alert(err.message);
    }
});

// ===== Chat de "Mensajes" =====
const form = document.getElementById('chat-form');
if (form) {
    const body = document.getElementById('chat-body');
    const input = document.getElementById('chat-input');
    const nombre = document.getElementById('chat-name');
    let reservaId = Number(body.dataset.reserva) || null;
    let ultimoId = Number(body.dataset.ultimo) || 0;

    const burbuja = (m) => {
        const div = document.createElement('div');
        div.className = 'bubble ' + (m.mine ? 'mine' : 'theirs');
        div.textContent = m.text;
        body.appendChild(div);
        ultimoId = Math.max(ultimoId, m.id);
    };
    const bajar = () => { body.scrollTop = body.scrollHeight; };
    const url = () => `/pasajero/api/conversaciones/${reservaId}/mensajes`;
    bajar();

    const cargar = async (desde = 0) => {
        if (!reservaId) return;
        const res = await fetch(`${url()}?desde=${desde}`);
        if (!res.ok) return;
        const nuevos = await res.json();
        nuevos.forEach(burbuja);
        if (nuevos.length) bajar();
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text || !reservaId) return;
        input.value = '';
        const res = await fetch(url(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (res.ok) { burbuja(await res.json()); bajar(); }
        else { input.value = text; }
    });

    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', async () => {
            document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            nombre.textContent = item.dataset.name;
            reservaId = Number(item.dataset.id);
            body.innerHTML = '';
            ultimoId = 0;
            await cargar(0);
            bajar();
        });
    });

    // Actualización periódica de mensajes nuevos
    setInterval(() => { if (!document.hidden) cargar(ultimoId); }, 5000);
}
