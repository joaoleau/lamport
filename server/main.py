import socket
import threading
import json
import hashlib
import base64
import os

# ==========================================
# ESTADO DO SERVIDOR E CONTROLE DE CONCORRÊNCIA
# ==========================================
lamport_clock = 0
mensagens = []
clientes_locais = []

# Como estamos usando Threads puras, PRECISAMOS de um Lock (Mutex) 
# para evitar "Race Conditions" ao alterar o relógio lógico
estado_lock = threading.Lock()

# IDs das réplicas (ex: "node-b", "node-c")
REPLICAS = os.getenv("REPLICAS", "").split(",")
PORT_SYNC = int(os.getenv("PORT_SYNC", 5001))
PORT_WS = int(os.getenv("PORT_WS", 5000))

# ==========================================
# FUNÇÕES DE WEBSOCKET (Feitas na unha)
# ==========================================
def fazer_handshake_ws(conn, request):
    """Responde ao navegador com as chaves corretas para converter HTTP em WebSocket"""
    lines = request.split('\r\n')
    key = ""
    for line in lines:
        if "Sec-WebSocket-Key:" in line:
            key = line.split(": ")[1]
            break
            
    magic = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept_key = base64.b64encode(hashlib.sha1(key.encode() + magic).digest()).decode()
    
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
    )
    conn.send(response.encode())

def enviar_ws(conn, mensagem_dict):
    """Empacota um JSON no formato de frames do WebSocket (Mensagens < 126 bytes)"""
    payload = json.dumps(mensagem_dict).encode('utf-8')
    header = bytearray([129, len(payload)]) # 129 = Texto
    try:
        conn.send(header + payload)
    except:
        pass

def decodificar_ws(data):
    """Remove a máscara de segurança que o navegador coloca na mensagem"""
    if len(data) < 6: return ""
    payload_len = data[1] & 127
    masks = data[2:6]
    payload = data[6:6+payload_len]
    decoded = bytearray([payload[i] ^ masks[i % 4] for i in range(len(payload))])
    return decoded.decode('utf-8')

# ==========================================
# LÓGICA DE NEGÓCIO E SINCRONIZAÇÃO
# ==========================================
def tratar_cliente_ws(conn, addr):
    """Thread dedicada para cada usuário conectado no navegador"""
    request = conn.recv(1024).decode()
    fazer_handshake_ws(conn, request)
    clientes_locais.append(conn)
    print(f"[+] Cliente Web conectado: {addr}")
    
    global lamport_clock
    
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
            
            texto_recebido = decodificar_ws(data)
            if not texto_recebido: continue
            pacote = json.loads(texto_recebido)
            
            # --- PROTEGENDO A SEÇÃO CRÍTICA ---
            with estado_lock:
                lamport_clock += 1  # Regra 1: Evento Local
                
                nova_msg = {
                    "autor": pacote.get("autor", "User"),
                    "texto": pacote.get("texto", ""),
                    "lamport_clock": lamport_clock
                }
                mensagens.append(nova_msg)
            
            # Envia para quem está na própria máquina
            for cli in clientes_locais:
                enviar_ws(cli, nova_msg)
                
            # Dispara Thread para enviar aos outros servidores via TCP
            threading.Thread(target=enviar_para_replicas, args=(nova_msg,)).start()
            
    except Exception as e:
        print(f"[-] Cliente desconectado.")
    finally:
        if conn in clientes_locais: clientes_locais.remove(conn)
        conn.close()

def tratar_sincronizacao_replicas(conn, addr):
    """Thread dedicada para receber pacotes de outros Servidores"""
    global lamport_clock
    
    try:
        data = conn.recv(1024).decode()
        if data:
            msg_recebida = json.loads(data)
            
            with estado_lock:
                # Regra 2: Atualiza pro maior relógio + 1
                lamport_clock = max(lamport_clock, msg_recebida["lamport_clock"]) + 1
                mensagens.append(msg_recebida)
            
            # Repassa a mensagem do outro servidor para os clientes HTML deste servidor
            for cli in clientes_locais:
                enviar_ws(cli, msg_recebida)
    except:
        pass
    finally:
        conn.close()

def enviar_para_replicas(msg_dict):
    """Abre um Socket TCP comum, manda o JSON para outro servidor e fecha"""
    payload = json.dumps(msg_dict).encode()
    for host in REPLICAS:
        if not host: continue
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, PORT_SYNC)) # Conecta na porta de Sync da réplica
            s.send(payload)
            s.close()
        except:
            print(f"[!] Falha ao sincronizar com {host}")

# ==========================================
# INICIALIZAÇÃO DOS SERVIDORES (Ouvintes)
# ==========================================
def iniciar_servidor_web():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', PORT_WS))
    s.listen(5)
    print("Servidor WebSocket rodando na porta 5000...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=tratar_cliente_ws, args=(conn, addr)).start()

def iniciar_servidor_sync():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', PORT_SYNC))
    s.listen(5)
    print("Servidor de Replicação (TCP) rodando na porta 5001...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=tratar_sincronizacao_replicas, args=(conn, addr)).start()

if __name__ == "__main__":
    # Roda as duas portas ao mesmo tempo usando Threads
    threading.Thread(target=iniciar_servidor_web).start()
    threading.Thread(target=iniciar_servidor_sync).start()