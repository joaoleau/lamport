# 🌐 Sistema de Chat Distribuído com Sincronização de Mensagens

Este repositório contém o código-fonte de um **Sistema de Chat Distribuído**, desenvolvido como requisito de avaliação para a disciplina de Computação Paralela e Distribuída do Instituto Federal de São Paulo (IFSP).

O projeto propõe uma topologia descentralizada e replicada, garantindo alta disponibilidade, tolerância a falhas e a consistência temporal das informações trafegadas através da implementação de **Relógios Lógicos de Lamport**.

## 🚀 Funcionalidades

- **Comunicação Bidirecional Ativa**: Utilização de WebSockets puros para comunicação *full-duplex* em tempo real entre cliente e cluster.
- **Balanceamento de Carga Transparente**: Uso do **Nginx** como *Reverse Proxy* e *Load Balancer* (via `least_conn`), distribuindo de forma uniforme as conexões entre instâncias do backend.
- **Sincronização Distribuída**: Replicação de estado assíncrona entre os servidores do cluster utilizando Sockets TCP.
- **Ordenação Causal (Relógio de Lamport)**: Implementação do algoritmo de Lamport em Python nativo e no frontend para garantir a cronologia exata e global da conversa, mitigando problemas de *clock drift* e atrasos de rede.
- **Isolamento de Ambiente**: Infraestrutura totalmente conteinerizada com Docker e orquestrada pelo Docker Compose.

## 📂 Estrutura Organizacional do Projeto

```text
lamport/
├── backend/             # Lógica do servidor de mensageria (Python)
│   ├── main.py          # Inicialização do servidor e gerenciamento de conexões assíncronas
│   └── requirements.txt # Dependências e bibliotecas do ecossistema Python
├── frontend/            # Interface gráfica do usuário (Web nativa)
│   ├── index.html       # Estrutura visual da aplicação de chat
│   ├── style.css        # Camada de estilização e layout responsivo
│   └── app.js           # Lógica de conexão WebSocket e gerência do Relógio de Lamport
├── infra/               # Configurações de ambiente e redes do cluster
│   └── nginx.conf       # Diretivas do Nginx para balanceamento de carga distribuída
├── docker-compose.yml   # Orquestração de múltiplos nós do backend e do balanceador
└── README.md            # Documento de instrução para build e execução do sistema
```

## 🛠️ Tecnologias Utilizadas

* **Backend**: Python 3.14 (Sockets TCP, Threads, JSON)
* **Frontend**: HTML5, CSS3, JavaScript Vanilla (WebSocket API)
* **Infraestrutura**: Docker, Docker Compose, Nginx (Alpine)

## ⚙️ Como Executar o Projeto

### Pré-requisitos

Certifique-se de ter o **Docker** e o **Docker Compose** instalados na sua máquina. Opcionalmente, o utilitário `make` pode ser usado para facilitar os comandos.

### Passo a Passo

1. **Clone o repositório**
```bash
git clone [https://github.com/joaoleau/lamport.git](https://github.com/joaoleau/lamport.git)
cd lamport

```


2. **Construa a imagem do servidor backend**
Se estiver a usar o comando `make`:
```bash
make build

```


Ou via Docker puro:
```bash
docker build -t lamport-server .

```


3. **Suba o cluster distribuído**
Via `make`:
```bash
make run

```


Ou via Docker Compose:
```bash
docker compose up --build

```


> 💡 *Neste momento, a orquestração inicializará 3 servidores backend a comunicarem entre si, 1 balanceador de carga Nginx central (porta 80) e 3 clientes simulados providenciando o frontend.*


4. **Inicie à aplicação**

Abra o seu navegador e abra as instâncias dos clientes, simulando usuários diferentes:
* 👤 **Cliente 1:** [http://localhost:8081](https://www.google.com/search?q=http://localhost:8081)
* 👤 **Cliente 2:** [http://localhost:8082](https://www.google.com/search?q=http://localhost:8082)
* 👤 **Cliente 3:** [http://localhost:8083](https://www.google.com/search?q=http://localhost:8083)


5. **Acompanhamento de Logs (Opcional)**
Para ver a sincronização acontecer em tempo real entre os servidores:
```bash
make logs

```


6. **Para encerrar a execução**
```bash
make down
# ou
docker compose down

```



## 👥 Equipe Desenvolvedora

* Pedro Barros Zich
* Gustavo Silva Novais
* Sthefany Cristovam da Silva
* João Vitor Leal de Castro
* Guilherme Henrique Araújo Pereira
* Kauê Dias da Silva

---

*Instituto Federal de Educação, Ciência e Tecnologia de São Paulo (IFSP) - Câmpus São Paulo, 2026*
