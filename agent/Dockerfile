FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user (uid 1000 matches the usual host user for the ~/.aws mount)
RUN useradd --create-home --uid 1000 app
USER app

CMD ["python", "worker.py"]
