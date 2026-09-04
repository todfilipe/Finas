# Deploy

Como pôr o Finas a correr numa VPS que já tem Nginx e outros projetos.

## Antes de começar

Na VPS é preciso ter Docker, Docker Compose e Nginx instalados. Também é preciso
o subdomínio `dashboard.finas.online` com um registo A a apontar para o IP da VPS.

Ver que portas já estão ocupadas pelos outros projetos e que vhosts já existem:

```
sudo ss -tlnp
ls /etc/nginx/sites-enabled/
```

Se a porta 3000 já estiver ocupada, escolher outra e trocar nos dois sítios:
no `docker-compose.prod.yml` (linha `127.0.0.1:3000:3000`) e no ficheiro do Nginx.

## Como está montado

- `db`, `api` e `bot` não publicam portas nenhumas, só falam entre si na rede do Docker
- `dashboard` publica em `127.0.0.1:3000`, ou seja só é acessível a partir da própria VPS
- o Nginx é o único a receber pedidos da internet e reencaminha para a dashboard
- o browser nunca fala com a API diretamente: quem chama a API é o servidor do Next,
  por dentro da rede do Docker (`http://api:8000`), reenviando o cookie de sessão

Por isso só é preciso um subdomínio e um certificado, e a API nunca fica exposta.

## Passos

1. Clonar o repositório na VPS e entrar na pasta

```
git clone <url-do-repositorio> finas
cd finas
```

2. Criar o `.env` a partir do exemplo e preencher

```
cp .env.example .env
```

Valores que têm mesmo de mudar em produção:

- `TELEGRAM_BOT_TOKEN` e `OPENAI_API_KEY`
- `POSTGRES_PASSWORD`: uma password forte
- `DATABASE_URL`: `postgresql+psycopg://finas:<password>@db:5432/finas` (o host é `db`)
- `DASHBOARD_URL`: `https://dashboard.finas.online`
- `SESSION_SECRET`: um valor aleatório longo, por exemplo `openssl rand -hex 32`
- `COOKIE_SECURE`: `true`

3. Construir e arrancar os containers

```
docker compose -f docker-compose.prod.yml up -d --build
```

As migrations do Alembic correm sozinhas quando o container da API arranca.

4. Configurar o Nginx

Copiar `deploy/nginx-finas.conf.example` para `/etc/nginx/sites-available/finas`,
e ativar:

```
sudo ln -s /etc/nginx/sites-available/finas /etc/nginx/sites-enabled/finas
sudo nginx -t
sudo systemctl reload nginx
```

5. Gerar o certificado HTTPS

```
sudo certbot --nginx -d dashboard.finas.online
```

O Certbot altera só este vhost, acrescenta o bloco de HTTPS e trata da renovação
automática. Os outros projetos da VPS ficam na mesma.

## Depois do deploy

Ver se está tudo de pé:

```
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f bot
```

Testar de ponta a ponta: escrever uma despesa ao bot no Telegram, depois `/dashboard`,
e abrir o link que ele envia.

## Atualizar

```
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Backup da base de dados

```
docker compose -f docker-compose.prod.yml exec db pg_dump -U finas finas > backup.sql
```
