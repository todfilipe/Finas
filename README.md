<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/simbolo-dark.svg">
    <img src=".github/assets/simbolo-light.svg" width="48" alt="Símbolo original do Finas, enquadrado num círculo branco">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/abertura-dark.svg">
    <img src=".github/assets/abertura-light.svg" width="640" alt="Finas. Escreve. Ele trata do resto. Python 3.12+, PostgreSQL 16 e Next.js 16.">
  </picture>
</p>

<p align="center">
  <a href="#conversa">Ver a conversa</a> · <a href="#dashboard">Explorar a dashboard</a> · <a href="#correr-localmente">Correr localmente</a> · <a href="docs/DEPLOY.md">Alojar na tua VPS</a>
</p>

<p align="center">
  Contas pessoais escritas como pensas nelas.<br>
  Para quem quer anotar o que entra e sai numa mensagem de Telegram.<br>
  A IA interpreta, o Finas guarda e tu vês tudo numa dashboard.
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/conversa-dark.webp">
    <img src=".github/assets/conversa-light.webp" width="144" alt="Ilustração de uma tira de papel dobrada num balão de conversa, com um pequeno apontamento dourado">
  </picture>
</p>

<a id="conversa"></a>

## É só uma conversa.

> **Tu**<br>
> hoje gastei 30 euros na fnac
>
> **Finas**<br>
> Anotado! 30€ na Fnac, categoria Tecnologia.
>
> **Tu**<br>
> não foi na fnac, foi no continente
>
> **Finas**<br>
> Ah, faz sentido! Corrigido: Continente (Alimentação), 30€.
>
> **Tu**<br>
> recebi o ordenado, 1200
>
> **Finas**<br>
> Boa! 1200€ de salário anotados 🙌

<sub>Exemplo de conversa com respostas presentes no prompt do bot. A IA gera a resposta em cada mensagem, por isso as palavras podem variar.</sub>

Também podes escrever **“ontem gastei 10 no café e 20 no almoço”**. O Finas trata até cinco movimentos por mensagem. Se corrigires uma mensagem com vários movimentos, pergunta qual deles queres mudar.

<details>
<summary>Vê a conversa no telemóvel</summary>

<p align="center">
  <img src="landing/img/telemovel.webp" width="280" alt="Imagem da landing: telemóvel com uma despesa, uma correção de comerciante e uma receita numa conversa com o Finas">
</p>

</details>

<br>

## Três passos, e já está.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/passos-dark.svg">
    <img src=".github/assets/passos-light.svg" width="640" alt="1. Escreves no Telegram. 2. A IA interpreta e o backend valida e guarda. 3. Consultas, filtras e editas na dashboard.">
  </picture>
</p>

<a id="dashboard"></a>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/divisor-dashboard-dark.svg">
    <img src=".github/assets/divisor-dashboard-light.svg" width="640" alt="A conversa, organizada.">
  </picture>
</p>

### O mês, num olhar.

Saldo, entradas e saídas lado a lado. Mais abaixo, despesas e receitas por categoria, tendência das despesas dos últimos seis meses e os comerciantes onde gastaste mais.

<p align="center">
  <a href="landing/img/dashboard-resumo.webp">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/assets/dashboard-resumo-dark.svg">
      <img src=".github/assets/dashboard-resumo-light.svg" width="800" alt="Screenshot real do resumo mensal: saldo, receitas, despesas e início da distribuição por categoria">
    </picture>
  </a>
  <br><sub>O resumo da app, com dados de demonstração.</sub>
</p>

<br>

### Encontra aquela conta.

Filtra por tipo, período, categoria, comerciante, texto ou valor. Edita e apaga movimentos na lista. Em **Categorias**, podes criar, renomear e juntar categorias do mesmo tipo; as que já não têm movimentos podem ser apagadas.

<p align="center">
  <a href="landing/img/dashboard-transacoes.webp">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/assets/dashboard-transacoes-dark.svg">
      <img src=".github/assets/dashboard-transacoes-light.svg" width="800" alt="Screenshot real das transações: filtros, receitas e despesas, categorias e ações de editar e apagar">
    </picture>
  </a>
  <br><sub>Cada movimento tem o seu lugar. E pode ser corrigido.</sub>
</p>

O acesso começa no Telegram: escreve <kbd>/dashboard</kbd> ou <kbd>/entrar</kbd>. Recebes um link e um código de utilização única, válido por cinco minutos por defeito. A sessão dura 30 dias por defeito.

<details>
<summary>Os comandos que tens à mão</summary>

| Comando | O que faz |
|---|---|
| `/start` | Apresenta o Finas e envia acesso à dashboard. |
| `/dashboard` ou `/entrar` | Gera um novo código de acesso. |
| `/editar` | Abre a edição manual do último movimento: valor, categoria, comerciante ou data. |
| `/apagar` | Pede confirmação para apagar o último movimento. |

As confirmações de registo também trazem um botão **Apagar**, ou **Apagar as N** quando há vários movimentos.

</details>

<a id="por-dentro"></a>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/divisor-tecnico-dark.svg">
    <img src=".github/assets/divisor-tecnico-light.svg" width="640" alt="Agora, por dentro.">
  </picture>
</p>

## Uma conversa à entrada. Dados teus à saída.

O bot chama a OpenAI e guarda os movimentos através de `backend/core/`. A API usa essa mesma lógica para servir a dashboard. Em produção, o navegador chega ao Next.js pelo Nginx; os pedidos à API partem do servidor Next.js, pela rede do Docker.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/arquitetura-dark.svg">
    <img src=".github/assets/arquitetura-light.svg" width="640" alt="Arquitetura de produção: Telegram liga ao bot, que chama a OpenAI e usa core. Navegador liga a Nginx, Next.js e FastAPI. Bot e API partilham core e PostgreSQL.">
  </picture>
</p>

| Peça | Para que serve aqui |
|---|---|
| Python 3.12+ e python-telegram-bot | Recebem mensagens e botões do Telegram por polling. |
| OpenAI e Pydantic | Extraem uma resposta estruturada e validam os movimentos. O modelo é escolhido em `OPENAI_MODEL`. |
| FastAPI | Expõe autenticação, movimentos, categorias e estatísticas. |
| PostgreSQL 16, SQLAlchemy e Alembic | Guardam os dados e fazem evoluir o esquema com migrações. |
| Next.js 16.3.4, React 19 e TypeScript | Renderizam a dashboard e comunicam com a API no servidor. |
| Tailwind CSS 4 | Dá forma à interface em preto, branco e dourado. |
| Docker Compose e Nginx | Correm os serviços na VPS e encaminham o acesso à dashboard. |

<details>
<summary>Dados, configuração e limites</summary>

Os modelos vivem em [`backend/core/models.py`](backend/core/models.py). Há quatro tabelas da aplicação:

| Tabela | Conteúdo |
|---|---|
| `users` | Identidade do Telegram, nome, fuso horário e moeda por defeito. |
| `expenses` | Despesas e receitas, valor inteiro em cêntimos, data, categoria, comerciante e mensagem original. |
| `categories` | Categorias de despesa ou receita associadas a cada utilizador. |
| `login_tokens` | Códigos de acesso, validade, utilização e tentativas. |

O parsing envia à OpenAI o texto da mensagem, as categorias e os movimentos recentes usados como contexto de correção. Os timestamps de criação são guardados em UTC; o dia do movimento é uma data. As datas relativas são interpretadas no fuso do utilizador, `Europe/Lisbon` por defeito.

Valores por defeito, configuráveis no [`.env.example`](.env.example):

| Configuração | Valor |
|---|---|
| `DEFAULT_CURRENCY` / `DEFAULT_TIMEZONE` | `EUR` / `Europe/Lisbon` |
| `BOT_MAX_MESSAGES` / `BOT_RATE_WINDOW_SECONDS` | 20 mensagens por utilizador em 60 segundos |
| `API_MAX_REQUESTS` / `API_RATE_WINDOW_SECONDS` | 120 pedidos autenticados por utilizador em 60 segundos |
| `LOGIN_CODE_MINUTES` / `SESSION_DAYS` | 5 minutos / 30 dias |
| `MAX_LOGIN_ATTEMPTS` | 5 tentativas por código ativo; uma tentativa inválida incrementa todos os códigos ativos |
| `ALERT_MINUTES` | 5 minutos antes de repetir um alerta da mesma origem e tipo de erro |

O endpoint de login tem ainda um limite de 10 pedidos por IP em 300 segundos. Os limites de pedidos ficam em memória por processo e são reiniciados com o serviço. `ALLOWED_TELEGRAM_IDS` restringe o bot; vazio permite o acesso a qualquer pessoa que o encontre.

O campo de moeda existe nos dados, mas os totais não fazem conversão entre moedas. O suporte multi-moeda continua em standby.

</details>

<a id="correr-localmente"></a>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/divisor-local-dark.svg">
    <img src=".github/assets/divisor-local-light.svg" width="640" alt="O teu Finas.">
  </picture>
</p>

## Põe o teu Finas a funcionar.

Precisas de **Python 3.12+, uv, Node.js 22, pnpm 10.12.1 e Docker com Compose**. Usa uma cópia local deste repositório. Nos passos abaixo, `finas/` é a pasta que contém este README.

Cria o teu bot em [@BotFather](https://t.me/BotFather) e prepara uma chave da API da OpenAI com acesso ao modelo que vais configurar. As mensagens ao bot fazem chamadas à API da OpenAI.

### 1. Prepara o ambiente e a base de dados

Num terminal em **`finas/`**, numa instalação nova sem `.env`:

```sh
cp .env.example .env
```

Abre o `.env` e preenche `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY` e `SESSION_SECRET`. Define `ALLOWED_TELEGRAM_IDS` com o teu ID de utilizador do Telegram, que podes consultar em [@userinfobot](https://t.me/userinfobot).

`OPENAI_MODEL` vem com `gpt-5.6-luna` no projeto. Usa um identificador de modelo disponível na tua conta que aceite o parsing estruturado usado em [`ai_parsing.py`](backend/core/ai_parsing.py). Esse valor no ficheiro não garante acesso ao modelo.

Para o setup local, mantém:

```dotenv
DATABASE_URL=postgresql+psycopg://finas:finas@localhost:5432/finas
DASHBOARD_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
COOKIE_SECURE=false
```

Ainda em **`finas/`**, arranca o PostgreSQL:

```sh
docker compose up -d db
docker compose exec db pg_isready -U finas -d finas
```

Espera que o último comando indique que aceita ligações. O Compose local só arranca a base de dados, na porta **5432**.

### 2. Instala o backend e arranca a API

No mesmo terminal, a partir de **`finas/`**:

```sh
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn api.main:app --reload
```

Deixa este terminal aberto. A API fica em [localhost:8000](http://localhost:8000/docs), com o estado em [health](http://localhost:8000/health). O `pyproject.toml` está em `backend/`.

### 3. Liga o bot

Abre outro terminal em **`finas/`**:

```sh
cd backend
uv run python -m bot.main
```

No Telegram, abre o teu bot, envia `/start` e escreve **“hoje gastei 30 euros na fnac”**. O bot já deve responder e guardar o movimento. Deixa este terminal aberto.

### 4. Abre a dashboard

Abre um terceiro terminal em **`finas/`**:

```sh
cd dashboard
pnpm install --frozen-lockfile
pnpm dev
```

Abre [localhost:3000](http://localhost:3000). Pede `/dashboard` ao bot e usa o link ou o código para entrar. A dashboard usa `http://localhost:8000` por defeito; não precisas de outro ficheiro de ambiente para este setup.

### 5. Corre os testes

Noutro terminal em **`finas/backend/`**:

```sh
uv run pytest
```

A suite cobre parsing, movimentos, receitas, categorias, autenticação, endpoints, handlers do bot, limites, alertas e a regra de escrita sem travessões. Os testes de dados usam SQLite em memória e as chamadas à IA são simuladas.

<details>
<summary>Se alguma coisa não arrancar</summary>

| Sintoma | O que verificar |
|---|---|
| Falta `TELEGRAM_BOT_TOKEN` ou `OPENAI_API_KEY` | O ficheiro chama-se `.env` e está em `finas/`, ao lado do Compose. Reinicia o serviço depois de o editar. |
| O bot diz que é privado | `ALLOWED_TELEGRAM_IDS` precisa do teu ID de utilizador, não do ID ou nome do bot. |
| O bot pede para reformular todas as despesas | Consulta o terminal do bot. Verifica a chave e o acesso ao modelo em `OPENAI_MODEL`. |
| A base de dados recusa a ligação | Confirma que o container `db` está pronto e que a porta 5432 está livre. Em local, o host é `localhost`. |
| A tabela ainda não existe | Corre `uv run alembic upgrade head` em `backend/` antes de iniciar o bot. |
| A dashboard não consegue falar com o servidor | Mantém a API na porta 8000. Se a mudares, configura `API_URL` no ambiente do Next.js e reinicia-o. |
| O código já não serve | Pede outro com `/dashboard`. O código só serve uma vez e expira. |
| A sessão não fica guardada em HTTP local | Mantém `COOKIE_SECURE=false` em local e entra outra vez. |
| Resposta 429 | Espera pela janela do limite do serviço antes de repetir o pedido. |

No PowerShell, `Copy-Item .env.example .env` é a alternativa explícita a `cp`. Os restantes comandos locais podem ser usados nos dois terminais.

</details>

<br>

## Na tua VPS.

O [`docker-compose.prod.yml`](docker-compose.prod.yml) corre PostgreSQL, API, bot e dashboard. Só a dashboard publica uma porta no host, em `127.0.0.1:3000`. O Nginx da VPS encaminha o subdomínio para essa porta.

O **[guia completo de deploy](docs/DEPLOY.md)** leva-te pela configuração do `.env`, arranque e migrações, server block, HTTPS com Certbot, verificações, logs, alertas e agendamento dos backups. Inclui também atualização e restauro.

<details>
<summary>Os ficheiros de operação</summary>

| Ficheiro | Papel |
|---|---|
| [`docker-compose.prod.yml`](docker-compose.prod.yml) | Serviços, rede interna, volume e rotação de logs. |
| [`deploy/nginx-finas.conf.example`](deploy/nginx-finas.conf.example) | Server block da dashboard. |
| [`deploy/backup.sh`](deploy/backup.sh) | Dump SQL comprimido e retenção dos backups. |
| [`deploy/restore.sh`](deploy/restore.sh) | Restauro de um dump, com confirmação antes de substituir os dados. |
| [`.env.example`](.env.example) | Variáveis disponíveis e valores de referência. |

</details>

## Onde estamos.

O registo por texto, receitas, correções, dashboard, gestão de categorias, testes, logs, alertas, limites de pedidos e scripts de backup estão implementados. O deploy está documentado; o agendamento do backup é configurado por quem aloja a instância.

**Em standby:** orçamentos e alertas de orçamento, movimentos recorrentes com lembretes, multi-moeda, exportação CSV/Excel, leitura de recibos e contas partilhadas em família. Já existem dados separados por utilizador; a partilha de despesas entre utilizadores ainda não existe. Sem datas prometidas para estas funcionalidades.

<br>

<p align="center"><strong>Contas finas, sem stress.</strong></p>

<p align="center">
  Um projeto pessoal de <a href="https://github.com/todfilipe">@todfilipe</a>.<br>
  O acesso ao bot da instância pessoal é dado a pedido.<br>
  <a href="https://t.me/todfilipe">Fala comigo no Telegram</a> · <a href="https://finas.online">Visita o site</a>
</p>

<p align="center"><sub>Licença: ainda não definida num ficheiro de licença deste repositório.</sub></p>
