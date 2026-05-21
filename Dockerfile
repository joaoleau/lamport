FROM python:3.14-alpine

WORKDIR /app

COPY server/main.py .

CMD ["python", "main.py"]