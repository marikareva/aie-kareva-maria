FROM python:3.12-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY src/ src/
COPY models/ models/

# Порт
EXPOSE 8000

# Логи и данные будут в volume
VOLUME ["/app/data", "/app/logs"]

# Запуск
CMD ["uvicorn", "src.app.api:app", "--host", "0.0.0.0", "--port", "8000"]