FROM python:3.13-slim

WORKDIR /app

COPY discord /app
COPY static /app/static
COPY db /app/db
COPY discord/.env /app/.env

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs

RUN echo "Files in /app:" && ls -la /app

CMD ["python", "main.py"]
