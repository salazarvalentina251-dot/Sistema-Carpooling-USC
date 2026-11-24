// Pestañas de "Mis reservas"
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

// Chat de "Mensajes" (solo visual; falta conectarlo al backend)
const form = document.getElementById('chat-form');
if (form) {
    const body = document.getElementById('chat-body');
    const input = document.getElementById('chat-input');
    body.scrollTop = body.scrollHeight;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        const div = document.createElement('div');
        div.className = 'bubble mine';
        div.textContent = text;
        body.appendChild(div);
        input.value = '';
        body.scrollTop = body.scrollHeight;
    });

    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            document.getElementById('chat-name').textContent = item.dataset.name;
        });
    });
}
