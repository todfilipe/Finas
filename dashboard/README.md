# Dashboard

App Next.js que mostra as despesas guardadas pelo bot. Consome a API FastAPI em `backend/api`.

## Correr localmente

Primeiro a API (a partir de `backend/`):

```
uv run uvicorn api.main:app --reload
```

Depois a dashboard (a partir desta pasta):

```
pnpm install
pnpm dev
```

Copia o `.env.example` para `.env.local` e aponta `NEXT_PUBLIC_API_URL` para a API.

## Páginas

- `/` mostra o total gasto no mês escolhido, a comparação com o mês anterior, o peso de cada categoria, os últimos 6 meses e os comerciantes onde gastaste mais. O mês muda pelo parâmetro `?mes=AAAA-MM` (setas no topo).
- `/transacoes` lista todas as despesas com filtros por texto, categoria, comerciante, período e intervalo de valores. Os filtros ficam no URL, por isso a página pode ser guardada nos favoritos ou partilhada. 50 despesas por página.
- `/login` recebe o código de 6 dígitos enviado pelo bot.

## Entrar

Não há passwords. Escreve `/dashboard` ao bot no Telegram e usa o link ou o código de 6 dígitos que ele enviar. A sessão dura 30 dias.
