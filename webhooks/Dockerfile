FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        python3-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONPATH=/app/src:/backend/src

ENV FLASK_APP=src/app.py
ENV FLASK_ENVIRONMENT=production

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "src.wsgi:app", "--workers", "2"]
