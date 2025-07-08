FROM python:3.13-slim

WORKDIR /app

COPY telegram /app
COPY telegram/.env /app/.env

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs

CMD ["python", "main.py"]
