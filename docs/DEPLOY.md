# O Finas na tua VPS

Este guia põe a dashboard atrás do Nginx da VPS e corre os quatro serviços com o [`docker-compose.prod.yml`](../docker-compose.prod.yml). O bot recebe mensagens por polling, sem webhook público.

[Voltar ao README](../README.md) · [Preparar](#preparar) · [Arrancar](#arrancar) · [HTTPS](#https) · [Logs](#logs) · [Backups](#backups) · [Restauro](#restauro)

<a id="preparar"></a>

## 1. Prepara a máquina

Precisas de uma VPS Linux com Docker Engine e o plugin Docker Compose, Nginx e Certbot com o plugin Nginx. Para os scripts de operação, precisas também de `sh`, `curl`, `gzip`, `gunzip`, `find` e cron. O utilizador que opera o projeto precisa de acesso ao Docker e de permissões para escrever na pasta de backups.

Os comandos de Nginx abaixo assumem uma instalação Debian/Ubuntu com `sites-available`, `sites-enabled` e systemd. Se a tua instalação usa outra estrutura, coloca o server block numa pasta incluída pelo teu `nginx.conf`.

Coloca uma cópia do repositório na VPS. Neste guia, `/home/utilizador/finas` é um caminho de exemplo: troca-o pelo teu caminho real em todos os comandos e no cron.

O exemplo de Nginx usa `dashboard.finas.online`. Para uma instância tua, troca esse nome pelo teu subdomínio no Nginx, no `.env` e nos comandos Certbot. O DNS desse subdomínio tem de apontar para a VPS, com HTTP e HTTPS acessíveis nas portas 80 e 443.

Confirma os serviços e as portas que já existem antes de instalar outro server block:

```sh
docker compose version
sudo ss -ltnp
sudo nginx -T
```

A porta `127.0.0.1:3000` tem de estar livre. Se já estiver ocupada, altera apenas a porta do host no Compose de produção, por exemplo `127.0.0.1:3001:3000`, e usa a mesma porta no `proxy_pass` do Nginx. A porta interna da dashboard continua a ser 3000. A API e a base de dados não publicam portas no host.

## 2. Configura o ambiente

Na primeira instalação, sem `.env` existente:

```sh
cd /home/utilizador/finas
cp .env.example .env
chmod 600 .env
```

Edita esse ficheiro antes de arrancar os serviços. Não uses os valores de demonstração para palavras-passe e segredos.

| Variável | O que colocar em produção |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do teu bot criado em @BotFather. |
| `OPENAI_API_KEY` | Chave da API da OpenAI com acesso ao modelo escolhido. |
| `OPENAI_MODEL` | Identificador de modelo compatível com `client.chat.completions.parse`. O exemplo do projeto é `gpt-5.6-luna`; confirma acesso na tua conta. |
| `POSTGRES_PASSWORD` | Palavra-passe forte para o utilizador `finas`. |
| `DATABASE_URL` | `postgresql+psycopg://finas:PALAVRA_PASSE@db:5432/finas`, com a mesma palavra-passe. O host é `db`. |
| `SESSION_SECRET` | Segredo aleatório próprio, usado para assinar as sessões. |
| `DASHBOARD_URL` | URL HTTPS do teu subdomínio, sem barra final. |
| `COOKIE_SECURE` | `true`. |
| `CORS_ORIGINS` | URL HTTPS da tua dashboard. Os pedidos da dashboard à API são feitos pelo servidor Next.js. |
| `ALLOWED_TELEGRAM_IDS` | IDs dos utilizadores autorizados, separados por vírgulas. Vazio abre o bot a qualquer pessoa que o encontre. |

`PALAVRA_PASSE` é um marcador para substituir, não um valor para copiar. Se usares caracteres especiais na palavra-passe, codifica-os para URL apenas em `DATABASE_URL`; em `POSTGRES_PASSWORD` usa a palavra-passe original. Uma cadeia aleatória hexadecimal evita essa diferença.

Para alertas e backups, configura também:

```dotenv
LOG_LEVEL=INFO
ADMIN_TELEGRAM_ID=
ALERT_MINUTES=5
BACKUP_DIR=/var/backups/finas
BACKUP_DAYS=14
```

Preenche `ADMIN_TELEGRAM_ID` com o teu ID de utilizador e inicia uma conversa com o bot para ele te poder enviar mensagens. Sem esse ID, os alertas ficam desligados. Os restantes limites, duração da sessão, fuso horário e moeda estão descritos no [`.env.example`](../.env.example).

Os scripts de backup leem os valores diretamente das linhas `NOME=valor`. Para as variáveis que usam, escreve valores sem aspas, sem `export` e sem comentários no fim da linha. Usa um caminho absoluto em `BACKUP_DIR`.

A dashboard recebe `API_URL=http://api:8000` do Compose. O `.env` da raiz é passado à API e ao bot; o Compose usa também `POSTGRES_PASSWORD` para configurar a base de dados.

<a id="arrancar"></a>

## 3. Constrói e arranca por ordem

Todos os comandos Compose deste guia correm em **`/home/utilizador/finas`** e indicam explicitamente o ficheiro de produção. O Compose sem `-f` usa o ficheiro local, que só arranca a base de dados.

```sh
docker compose -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml exec db pg_isready -U finas -d finas
```

Quando o PostgreSQL aceitar ligações, inicia a API:

```sh
docker compose -f docker-compose.prod.yml up -d api
docker compose -f docker-compose.prod.yml logs --tail=100 api
```

O comando de arranque da API executa `alembic upgrade head` antes do Uvicorn. Espera pelas migrações e pelo arranque do servidor. Verifica-o dentro do container, sem expor a porta 8000:

```sh
docker compose -f docker-compose.prod.yml exec api python -c "import httpx; r = httpx.get('http://127.0.0.1:8000/health'); r.raise_for_status(); print(r.json())"
```

A resposta esperada é `{'status': 'ok'}`. Este endpoint confirma que a API responde; não faz uma consulta à base de dados.

Depois liga o bot e a dashboard:

```sh
docker compose -f docker-compose.prod.yml up -d bot dashboard
docker compose -f docker-compose.prod.yml ps
curl -I http://127.0.0.1:3000/login
```

Esta ordem evita que o bot receba mensagens antes de existirem as tabelas. No Compose atual, o bot espera pela base de dados saudável, mas não pela conclusão das migrações da API.

Os Dockerfiles instalam as dependências a partir de `uv.lock` e `pnpm-lock.yaml`. Não precisas de instalar Python, uv, Node.js ou pnpm no host para correr estes containers.

As opções de construção e arranque estão na [referência oficial de `docker compose up`](https://docs.docker.com/reference/cli/docker/compose/up/).

<a id="https"></a>

## 4. Liga o Nginx e o HTTPS

Ainda na raiz do projeto, copia o exemplo para um novo server block:

```sh
sudo cp deploy/nginx-finas.conf.example /etc/nginx/sites-available/finas
sudo nano /etc/nginx/sites-available/finas
```

Este comando é para uma primeira instalação em que esse ficheiro ainda não existe. Se já existe, edita o bloco existente. Mantém os server blocks dos outros projetos.

No editor, troca `server_name dashboard.finas.online;` pelo teu subdomínio. O `proxy_pass` deve apontar para a porta publicada pela dashboard, `http://127.0.0.1:3000` por defeito. Os cabeçalhos de proxy necessários já estão no [exemplo](../deploy/nginx-finas.conf.example).

Ativa o bloco, se ainda não tiver uma ligação em `sites-enabled`:

```sh
sudo ln -s /etc/nginx/sites-available/finas /etc/nginx/sites-enabled/finas
sudo nginx -t
```

Só se a validação passar, recarrega o Nginx:

```sh
sudo systemctl reload nginx
```

O Nginx aplica a nova configuração após recarregar o serviço; consulta o [guia oficial](https://nginx.org/en/docs/beginners_guide.html) para instalações com outra estrutura.

Com o DNS a resolver e o subdomínio acessível por HTTP, pede o certificado. Substitui o domínio do exemplo pelo teu:

```sh
sudo certbot --nginx -d dashboard.finas.online
sudo certbot renew --dry-run
```

O plugin Nginx obtém e instala o certificado. Confirma também que a instalação do Certbot tem a renovação automática agendada. O `--dry-run` testa a renovação, não cria o agendamento. O [guia oficial do Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html#automated-renewals) descreve essa verificação.

Confirma que o HTTP redireciona para HTTPS e abre a dashboard por HTTPS antes de testar o login, porque `COOKIE_SECURE=true` está ligado.

## 5. Faz a primeira volta completa

1. No Telegram, envia `/start` ao teu bot com um utilizador autorizado.
2. Regista uma despesa de teste e confirma que o bot responde com valor e categoria.
3. Pede `/dashboard` e abre o link HTTPS, ou escreve o código na página de login.
4. Confirma que o movimento aparece na dashboard.
5. Corrige o movimento por texto e atualiza a página para verificar a alteração.
6. Apaga esse movimento de teste na dashboard.

Esta volta verifica Telegram, parsing, escrita e leitura da base de dados, autenticação e proxy. Não substituas esta verificação por um `/health` isolado.

<a id="logs"></a>

## 6. Vê logs e recebe alertas

Na raiz do projeto:

```sh
docker compose -f docker-compose.prod.yml logs -f --tail=100 api bot dashboard db
```

Sai do acompanhamento com `Ctrl+C`. Os serviços continuam a correr. A API regista método, caminho, estado e duração do pedido. O bot regista o arranque, movimentos guardados e erros. Cada serviço usa logs Docker `json-file`, com ficheiros de 10 MB e até três ficheiros por serviço no Compose.

Com `TELEGRAM_BOT_TOKEN` e `ADMIN_TELEGRAM_ID` definidos, erros tratados pelo sistema de alertas são enviados ao administrador: erros inesperados da API, parsing e gravação no bot, e erros não previstos nos handlers. `ALERT_MINUTES` reduz a repetição da mesma origem e tipo de erro, em memória por processo.

Os alertas dependem de o processo estar a correr e conseguir chegar ao Telegram. Não são um monitor externo de disponibilidade. O script de backup também tenta avisar quando o `pg_dump` falha ou produz um ficheiro vazio; não cobre todas as possíveis falhas do script, como falta de permissões ao criar a pasta.

<a id="backups"></a>

## 7. Agenda os backups

O [`deploy/backup.sh`](../deploy/backup.sh) executa `pg_dump` dentro do container `db`, comprime o SQL e remove dumps antigos de acordo com `BACKUP_DAYS`. Sem `BACKUP_DIR`, usa `backups/` dentro do projeto; sem `BACKUP_DAYS`, usa 14 dias. O `.env.example` define `/var/backups/finas`.

Na raiz do projeto, prepara a pasta para o utilizador que vai correr o cron:

```sh
sudo install -d -m 700 -o "$(id -un)" -g "$(id -gn)" /var/backups/finas
chmod +x deploy/backup.sh deploy/restore.sh
umask 077
./deploy/backup.sh
ls -lh /var/backups/finas
```

Se escolheste outro `BACKUP_DIR`, usa-o também nestes comandos. Confirma que apareceu um ficheiro `finas-AAAA-MM-DD-HHMM.sql.gz`. Usa o caminho do ficheiro criado para testar a integridade da compressão:

```sh
gzip -t /var/backups/finas/finas-AAAA-MM-DD-HHMM.sql.gz
```

Esse nome é um padrão ilustrativo: substitui-o pelo nome real. Um `gzip -t` bem-sucedido confirma a compressão; só um ensaio de restauro numa instância separada confirma a recuperação dos dados.

Abre `crontab -e` como o mesmo utilizador com acesso ao Docker. Adiciona uma execução diária às 04:00, no fuso horário da VPS:

```cron
0 4 * * * umask 077; /home/utilizador/finas/deploy/backup.sh >> /var/backups/finas/backup.log 2>&1
```

Troca ambos os caminhos se necessário. O script muda para a pasta do projeto sozinho. Confirma que o `PATH` do cron inclui o executável `docker` instalado na VPS. No dia seguinte, verifica o dump e `backup.log`. O ficheiro de log do backup precisa da tua política de rotação; a rotação Docker não se aplica a ele.

Copia os backups para fora da VPS de forma regular. Essa cópia externa não é feita pelo script.

<a id="restauro"></a>

## 8. Restaura quando precisares

O dump contém `--clean --if-exists`. **O restauro substitui as tabelas e os dados atuais pelo conteúdo do backup.** Guarda primeiro um backup do estado atual se precisares de o conservar.

Na raiz do projeto, valida o ficheiro real e para os serviços que acedem à base de dados:

```sh
gzip -t /var/backups/finas/finas-AAAA-MM-DD-HHMM.sql.gz
docker compose -f docker-compose.prod.yml stop dashboard bot api
./deploy/restore.sh /var/backups/finas/finas-AAAA-MM-DD-HHMM.sql.gz
```

O script pede que escrevas `sim` antes de continuar. Deixa o container `db` a correr. Também podes passar um ficheiro `.sql` sem compressão ao script.

Lê toda a saída do restauro e verifica se houve erros SQL. O script usa `psql` sem `ON_ERROR_STOP`, por isso a mensagem final, por si só, não prova que todas as instruções SQL foram aplicadas.

Se o restauro correu bem, inicia primeiro a API, que volta a aplicar as migrações necessárias:

```sh
docker compose -f docker-compose.prod.yml start api
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml exec api python -c "import httpx; r = httpx.get('http://127.0.0.1:8000/health'); r.raise_for_status(); print(r.json())"
```

Depois de confirmares o arranque:

```sh
docker compose -f docker-compose.prod.yml start bot dashboard
```

Entra com um código novo do bot e confirma os movimentos e os totais na dashboard. Se houver erros no restauro, mantém os serviços parados e resolve-os antes de retomar o uso.

## 9. Atualiza uma instalação existente

Na raiz do projeto, faz um backup e para os serviços da aplicação:

```sh
umask 077
./deploy/backup.sh
docker compose -f docker-compose.prod.yml stop dashboard bot api
```

Coloca a nova versão do código na pasta do projeto, preservando o `.env` e os backups. Compara as variáveis novas com o `.env.example`. Depois:

```sh
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d api
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml exec api python -c "import httpx; r = httpx.get('http://127.0.0.1:8000/health'); r.raise_for_status(); print(r.json())"
```

Espera pelas migrações e por uma resposta válida antes de retomar os restantes serviços:

```sh
docker compose -f docker-compose.prod.yml up -d bot dashboard
```

Usa `up -d` para aplicar alterações de imagem ou ambiente; um simples `restart` não recria o container com novas variáveis. Guarda o backup e a versão anterior do código para uma recuperação compatível com o esquema restaurado.

O volume `finas_db_data` mantém os dados entre recriações dos containers. Não o apagues durante atualizações. Alterar `POSTGRES_PASSWORD` no `.env` não altera a palavra-passe de uma base de dados já inicializada; uma rotação precisa de mudar também a credencial no PostgreSQL e o `DATABASE_URL` dos serviços.

<details>
<summary>Diagnóstico rápido</summary>

| Sintoma | Verificação |
|---|---|
| Nginx devolve 502 | Confirma a dashboard em `docker compose -f docker-compose.prod.yml ps`, a porta publicada e o `proxy_pass`. |
| API reinicia continuamente | Lê os logs: a migração corre antes do servidor. Confirma `DATABASE_URL`, host `db` e palavra-passe. |
| Bot não responde | Confirma token, IDs autorizados, logs e que não tens outra instância em polling com o mesmo token. |
| Erro de parsing em todas as mensagens | Confirma chave, modelo e acesso à API da OpenAI. |
| Código expirado ou usado | Pede outro com `/dashboard`; o prazo é configurado em `LOGIN_CODE_MINUTES`. |
| Login não mantém a sessão | Confirma HTTPS, `COOKIE_SECURE=true`, `SESSION_SECRET` estável e os logs de API e dashboard. |
| Não há alertas | Confirma `ADMIN_TELEGRAM_ID`, conversa iniciada com o bot e acesso ao Telegram. |
| Cron não cria dumps | Verifica cron ativo, `PATH`, acesso ao Docker, permissões da pasta e `backup.log`. |

</details>
