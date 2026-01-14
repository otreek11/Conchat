FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system build deps required by some Python packages (argon2, cryptography, etc.)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		gcc \
		libffi-dev \
		libssl-dev \
		python3-dev \
		pkg-config \
		libargon2-1 \
		libargon2-dev \
	&& rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
# Upgrade pip to ensure wheel availability then install
RUN pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
