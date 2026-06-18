import asyncio
import websockets
import json
import time

# Configurações do Teste
WS_URL = "ws://localhost:80"
NUM_CLIENTES = 10       # Quantidade de abas simuladas
MSGS_POR_CLIENTE = 20   # Quantas mensagens cada cliente vai mandar
ATRASO_DISPARO = 0.05   # Atraso minúsculo para simular digitação ultrarrápida

async def cliente_bot(client_id, resultados):
    """Simula um cliente conectando e enviando várias mensagens em rajada"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Aguarda a mensagem de boas vindas ('info') do balanceador
            info_msg = await websocket.recv()
            info = json.loads(info_msg)
            node_id = info.get("node_id", "Desconhecido")
            print(f"[Bot {client_id}] Conectado ao {node_id}")

            # Dispara as mensagens
            for i in range(MSGS_POR_CLIENTE):
                msg = {"autor": f"Bot-{client_id}", "texto": f"Msg {i+1}"}
                await websocket.send(json.dumps(msg))
                await asyncio.sleep(ATRASO_DISPARO)

            # Fica ouvindo os retornos por 3 segundos para capturar tudo do cluster
            start_time = time.time()
            while time.time() - start_time < 3:
                try:
                    resposta = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    dados = json.loads(resposta)
                    if dados.get("tipo") != "info":
                        resultados.append(dados)
                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        print(f"[Bot {client_id}] Erro: {e}")

async def main():
    print(f"Iniciando teste com {NUM_CLIENTES} clientes enviando {MSGS_POR_CLIENTE} msgs cada...")
    print(f"Total esperado de mensagens globais: {NUM_CLIENTES * MSGS_POR_CLIENTE}")
    
    resultados_globais = []
    
    # Cria as tarefas para rodarem simultaneamente
    tarefas = [cliente_bot(i, resultados_globais) for i in range(NUM_CLIENTES)]
    
    # Executa todos os bots ao mesmo tempo (Teste de concorrência real)
    await asyncio.gather(*tarefas)

    print("\n--- ANÁLISE DOS RESULTADOS ---")
    
    # Filtra as mensagens únicas (usando autor + texto como chave)
    mensagens_unicas = {}
    for msg in resultados_globais:
        chave = f"{msg['autor']}::{msg['texto']}"
        mensagens_unicas[chave] = msg

    print(f"Mensagens únicas processadas com sucesso: {len(mensagens_unicas)}")
    
    if len(mensagens_unicas) == NUM_CLIENTES * MSGS_POR_CLIENTE:
        print("✅ SUCESSO: O cluster não perdeu nenhuma mensagem sob estresse!")
    else:
        print("❌ FALHA: Houve perda de pacotes ou desconexões prematuras.")

    # Verifica se houve alucinação no Relógio de Lamport (Race Condition no Lock)
    # Regra: Em um mesmo nó de origem, os relógios lógicos devem ser estritamente crescentes.
    # Não podem existir duas mensagens originadas do mesmo nó com o mesmo lamport_clock
    conflitos = 0
    relogios_por_no = {}
    
    for msg in mensagens_unicas.values():
        origem = msg["origem"]
        clock = msg["lamport_clock"]
        
        if origem not in relogios_por_no:
            relogios_por_no[origem] = []
            
        if clock in relogios_por_no[origem]:
            conflitos += 1
            print(f"⚠️ ALUCINAÇÃO DETECTADA: O nó '{origem}' gerou duas mensagens com o relógio {clock}")
        
        relogios_por_no[origem].append(clock)

    if conflitos == 0:
        print("✅ SUCESSO: Nenhuma 'Race Condition' detectada. O relógio lógico suportou a concorrência sem alucinar timestamps locais duplicados!")
    else:
        print(f"❌ FALHA: Ocorreram {conflitos} conflitos de relógio lógico.")

if __name__ == "__main__":
    asyncio.run(main())