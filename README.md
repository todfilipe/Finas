# Finas

Tracker de despesas pessoais que se usa a escrever, não a preencher formulários.

## A ideia

1. Escreves ao bot de Telegram como escreverias a um amigo: *"hoje gastei 30 euros na fnac"*
2. Uma IA lê a mensagem, extrai o valor, categoriza a despesa (ex: Tecnologia) e identifica o comerciante (Fnac)
3. A despesa fica guardada automaticamente, sem fricção
4. Numa dashboard web consegues ver todos os gastos, filtrar, ver gráficos por categoria e por mês, editar ou apagar registos

Sem apps para abrir, sem formulários, só escrever a despesa como pensas nela.

## Correr o projeto

Ver `dashboard/README.md` para o desenvolvimento local e `DEPLOY.md` para o deploy numa VPS.

## Stack

- **Bot**: Python + python-telegram-bot
- **Backend**: FastAPI
- **IA**: OpenAI
- **Base de dados**: PostgreSQL
- **Dashboard**: Next.js + Tailwind CSS


