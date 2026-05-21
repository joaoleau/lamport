const WEBSOCKET_URL = `ws://localhost:80`; 

let socket;
let listaMensagens = [];

const chatHistory = document.getElementById('chat-history');
const inputTexto = document.getElementById('texto-msg');
const inputNome = document.getElementById('nome-usuario');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

function conectar() {
    socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => {
        statusDot.className = 'status-dot connected';
        statusText.innerText = 'Conectado ao Cluster';
    };

    socket.onclose = () => {
        statusDot.className = 'status-dot disconnected';
        statusText.innerText = 'Desconectado (Tentando reconectar...)';
        setTimeout(conectar, 3000);
    };

    socket.onmessage = (event) => {
        const msgRecebida = JSON.parse(event.data);
        listaMensagens.push(msgRecebida);
        listaMensagens.sort((a, b) => a.lamport_clock - b.lamport_clock);

        renderizarChat();
    };
}

function enviarMensagem() {
    const texto = inputTexto.value.trim();
    const autor = inputNome.value.trim();

    if (texto === "" || autor === "") return;

    const pacote = {
        autor: autor,
        texto: texto
    };

    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(pacote));
        inputTexto.value = '';
        inputTexto.focus();
    } else {
        alert("Aguarde a conexão com o servidor.");
    }
}

function renderizarChat() {
    chatHistory.innerHTML = '';
    
    const meuNome = inputNome.value.trim();

    listaMensagens.forEach(msg => {
        const isMine = msg.autor === meuNome;
        const bubbleClass = isMine ? 'message-bubble mine' : 'message-bubble other';

        const bubbleHTML = `
            <div class="${bubbleClass}">
                ${!isMine ? `<div class="msg-author">${msg.autor}</div>` : ''}
                <div class="msg-text">${msg.texto}</div>
                <div class="msg-meta">⏳ Lamport: ${msg.lamport_clock}</div>
            </div>
        `;
        
        chatHistory.insertAdjacentHTML('beforeend', bubbleHTML);
    });

    chatHistory.scrollTop = chatHistory.scrollHeight;
}

inputTexto.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        enviarMensagem();
    }
});

const btnEnviar = document.getElementById('btn-enviar');

btnEnviar.addEventListener('click', () => {
    enviarMensagem();
});

conectar();