#!/bin/sh
set -e

PROJETO=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJETO"

if [ -z "$1" ]; then
    echo "Uso: deploy/restore.sh /caminho/para/finas-2026-09-04-0400.sql.gz"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Nao encontrei o ficheiro $1"
    exit 1
fi

echo "Isto substitui os dados atuais da base de dados pelo conteudo de $1"
echo "Antes de continuar, para o bot e a API:"
echo "  docker compose -f docker-compose.prod.yml stop api bot"
printf "Escreve sim para continuar: "
read RESPOSTA

if [ "$RESPOSTA" != "sim" ]; then
    echo "Cancelado"
    exit 1
fi

if [ "${1##*.}" = "gz" ]; then
    gunzip -c "$1" | docker compose -f docker-compose.prod.yml exec -T db psql -U finas -d finas
else
    docker compose -f docker-compose.prod.yml exec -T db psql -U finas -d finas < "$1"
fi

echo "Restauro concluido. Arranca outra vez o bot e a API:"
echo "  docker compose -f docker-compose.prod.yml start api bot"
