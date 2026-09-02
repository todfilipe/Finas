import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from core.config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Sou o Finas. Ainda estou em testes, mas já te ouço.")


async def eco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Recebi: " + update.message.text)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN no .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, eco))
    app.run_polling()


if __name__ == "__main__":
    main()
