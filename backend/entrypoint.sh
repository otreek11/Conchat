#!/bin/sh

echo "Inicializando container..."

# Gera .env apenas se não existir
if [ ! -f .env ]; then
    echo "Gerando .env..."
    python init_dotenv.py 32 development sqlite:///teste.db
else
    echo ".env encontrado, mantendo."
fi

echo "Rodando migrations..."
flask db migrate || true
flask db upgrade

echo "Iniciando servidor..."
exec gunicorn --bind 0.0.0.0:8000 src.wsgi:app --workers 3