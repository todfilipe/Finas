#!/bin/sh
set -e

PROJETO=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJETO"

ler_do_env() {
    if [ ! -f .env ]; then
        echo ""
        return
    fi
    grep "^$1=" .env | tail -n 1 | cut -d= -f2- | tr -d '\r'
}

PASTA=$(ler_do_env BACKUP_DIR)
if [ -z "$PASTA" ]; then
    PASTA="$PROJETO/backups"
fi

DIAS=$(ler_do_env BACKUP_DAYS)
if [ -z "$DIAS" ]; then
    DIAS=14
fi

TOKEN=$(ler_do_env TELEGRAM_BOT_TOKEN)
ADMIN=$(ler_do_env ADMIN_TELEGRAM_ID)

avisar() {
    echo "$1"
    if [ -n "$TOKEN" ] && [ -n "$ADMIN" ]; then
        curl -s -m 10 -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d "chat_id=$ADMIN" -d "text=$1" > /dev/null || true
    fi
}

mkdir -p "$PASTA"

DATA=$(date +%Y-%m-%d-%H%M)
FICHEIRO="$PASTA/finas-$DATA.sql"

if ! docker compose -f docker-compose.prod.yml exec -T db pg_dump -U finas -d finas --clean --if-exists > "$FICHEIRO"; then
    rm -f "$FICHEIRO"
    avisar "Finas: o backup da base de dados falhou"
    exit 1
fi

if [ ! -s "$FICHEIRO" ]; then
    rm -f "$FICHEIRO"
    avisar "Finas: o backup da base de dados ficou vazio"
    exit 1
fi

gzip -f "$FICHEIRO"

find "$PASTA" -name "finas-*.sql.gz" -mtime +"$DIAS" -delete

echo "$(date +%Y-%m-%dT%H:%M:%S) backup guardado em $FICHEIRO.gz"
