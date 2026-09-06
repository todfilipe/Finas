# Deploy

Ficheiros de apoio ao deploy na VPS.

- `nginx-finas.conf.example`: server block do Nginx para o subdominio da dashboard
- `backup.sh`: backup automatico da base de dados
- `restore.sh`: restauro a partir de um backup

## Backup automatico da base de dados

O `backup.sh` corre um `pg_dump` dentro do container `db`, guarda o resultado
comprimido e apaga os backups antigos. Se alguma coisa correr mal, avisa no
Telegram (usa o `TELEGRAM_BOT_TOKEN` e o `ADMIN_TELEGRAM_ID` do `.env`, os mesmos
dos alertas de erro).

Configuracao no `.env` da VPS:

```
BACKUP_DIR=/var/backups/finas
BACKUP_DAYS=14
```

Se estas variaveis nao existirem, os backups vao para `backups/` dentro do
projeto e ficam guardados 14 dias.

Correr a mao, a partir da raiz do projeto:

```
./deploy/backup.sh
```

Para ficar automatico, um `cron` diario as 4 da manha (`crontab -e`):

```
0 4 * * * /home/utilizador/finas/deploy/backup.sh >> /var/log/finas-backup.log 2>&1
```

Trocar `/home/utilizador/finas` pelo caminho real do projeto na VPS. Se os
scripts nao tiverem permissao de execucao depois do `git clone`:

```
chmod +x deploy/backup.sh deploy/restore.sh
```

Os ficheiros ficam com o nome `finas-2026-09-04-0400.sql.gz`. Vale a pena copiar
de vez em quando um deles para fora da VPS: um backup que so existe na mesma
maquina que a base de dados nao protege de perder a maquina.

## Restauro

O dump e feito com `--clean --if-exists`, por isso o restauro apaga as tabelas
atuais e volta a cria-las com os dados do backup.

```
docker compose -f docker-compose.prod.yml stop api bot
./deploy/restore.sh /var/backups/finas/finas-2026-09-04-0400.sql.gz
docker compose -f docker-compose.prod.yml start api bot
```

O script pede confirmacao antes de mexer na base de dados.
