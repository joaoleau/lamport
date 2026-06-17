const WEBSOCKET_URL = `ws://${location.hostname}:80`;

let socket;
let listaMensagens = [];
let logEventos = [];
let nodeId = "—";

const chatHistory = document.getElementById('chat-history');
const inputTexto = document.getElementById('texto-msg');
const inputNome = document.getElementById('nome-usuario');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const nodeName = document.getElementById('node-name');
const nodeClockValue = document.getElementById('node-clock-value');
const btnEnviar = document.getElementById('btn-enviar');
const btnLog = document.getElementById('btn-log');
const eventLog = document.getElementById('event-log');

// Escapa HTML para evitar injeção (XSS) ao renderizar autor/texto
function esc(s) {
    return String(s).replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

function setConexao(online) {
    statusDot.className = online ? 'status-dot connected' : 'status-dot disconnected';
    statusText.innerText = online ? 'Conectado ao cluster' : 'Desconectado (tentando reconectar...)';
    inputTexto.disabled = !online;
    btnEnviar.disabled = !online;
}

function conectar() {
    socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => setConexao(true);

    socket.onclose = () => {
        setConexao(false);
        setTimeout(conectar, 3000);
    };

    socket.onmessage = (event) => {
        const dado = JSON.parse(event.data);

        // Frame de boas-vindas: diz em qual nó o balanceador colocou este cliente
        if (dado.tipo === 'info') {
            nodeId = dado.node_id;
            nodeName.innerText = `nó ${dado.node_id}`;
            nodeClockValue.innerText = dado.node_clock;
            return;
        }

        // Atualiza o relógio lógico exibido para o nó que entregou a mensagem
        if (typeof dado.node_clock !== 'undefined') {
            nodeClockValue.innerText = dado.node_clock;
        }
        registrarLog(dado);

        listaMensagens.push(dado);
        // Ordem total de Lamport: ordena pelo relógio e desempata pelo nó de origem
        listaMensagens.sort((a, b) =>
            a.lamport_clock - b.lamport_clock ||
            String(a.origem).localeCompare(String(b.origem))
        );

        // Se a nova mensagem não ficou no fim da lista, ela foi reordenada
        const reordenada = listaMensagens[listaMensagens.length - 1] !== dado;
        renderizarChat(dado, reordenada);
    };
}

function enviarMensagem() {
    const texto = inputTexto.value.trim();
    const autor = inputNome.value.trim();

    if (texto === "" || autor === "") return;

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ autor, texto }));
        inputTexto.value = '';
        inputTexto.focus();
    } else {
        alert("Aguarde a conexão com o servidor.");
    }
}

// Eventos concorrentes: mesmo relógio lógico, mas nós de origem diferentes
function souConcorrente(msg) {
    return listaMensagens.some(m =>
        m !== msg &&
        m.lamport_clock === msg.lamport_clock &&
        m.origem !== msg.origem
    );
}

function metaMensagem(msg) {
    if (msg.evento === 'replica') {
        return {
            badge: `nó ${msg.origem} → nó ${msg.via}`,
            tipo: 'recebido',
            calc: `max(${msg.clock_antes}, ${msg.lamport_clock}) + 1 = ${msg.clock_depois}`
        };
    }
    return {
        badge: `nó ${msg.origem}`,
        tipo: 'local',
        calc: `relógio ${msg.clock_antes} → ${msg.clock_depois}`
    };
}

function renderizarChat(nova, reordenada) {
    chatHistory.innerHTML = '';

    const meuNome = inputNome.value.trim();

    listaMensagens.forEach(msg => {
        const isMine = msg.autor === meuNome;
        const meta = metaMensagem(msg);
        const concorrente = souConcorrente(msg);
        const destacar = msg === nova && reordenada;

        const classes = [
            'message-bubble',
            isMine ? 'mine' : 'other',
            destacar ? 'reordered' : ''
        ].join(' ').trim();

        const badgeClass = meta.tipo === 'recebido' ? 'badge-recv' : 'badge-local';

        const bubbleHTML = `
            <div class="${classes}">
                ${!isMine ? `<div class="msg-author">${esc(msg.autor)}</div>` : ''}
                <div class="msg-text">${esc(msg.texto)}</div>
                ${concorrente ? `<div class="msg-concurrent">⇄ concorrente</div>` : ''}
                <div class="msg-meta">
                    <span class="badge ${badgeClass}">${esc(meta.badge)} · ${meta.tipo}</span>
                    <span class="msg-calc">⏱ ${esc(meta.calc)}</span>
                </div>
            </div>
        `;

        chatHistory.insertAdjacentHTML('beforeend', bubbleHTML);
    });

    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function registrarLog(msg) {
    let linha;
    if (msg.evento === 'replica') {
        linha = `nó ${msg.via} recebeu de nó ${msg.origem} (ts=${msg.lamport_clock}) → relógio = max(${msg.clock_antes}, ${msg.lamport_clock}) + 1 = ${msg.clock_depois}`;
    } else {
        linha = `nó ${msg.origem} enviou "${msg.texto}" → evento local, relógio ${msg.clock_antes} → ${msg.clock_depois}`;
    }
    logEventos.push(linha);
    renderizarLog();
}

function renderizarLog() {
    eventLog.innerHTML = logEventos
        .map((l, i) => `<div class="log-line"><span class="log-n">${i + 1}</span>${esc(l)}</div>`)
        .join('');
    eventLog.scrollTop = eventLog.scrollHeight;
}

inputTexto.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        enviarMensagem();
    }
});

btnEnviar.addEventListener('click', enviarMensagem);

// Trocar o nome reavalia quais bolhas são "minhas"
inputNome.addEventListener('input', () => renderizarChat());

btnLog.addEventListener('click', () => {
    if (eventLog.hasAttribute('hidden')) {
        eventLog.removeAttribute('hidden');
        btnLog.innerText = 'Ocultar log de eventos';
    } else {
        eventLog.setAttribute('hidden', '');
        btnLog.innerText = 'Mostrar log de eventos';
    }
});

setConexao(false);
conectar();
