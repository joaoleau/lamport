run:
	docker compose up --build

down:
	docker compose down

build:
	docker build -t lamport-server .

logs:
	docker compose logs -f