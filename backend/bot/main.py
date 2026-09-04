import asyncio
import logging
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.ai_parsing import (
    CATEGORIAS,
    campos_da_correcao,
    construir_despesa_nova,
    frase_de_recurso,
    parse_mensagem,
)
from core.auth import criar_codigo_de_acesso
from core.config import DASHBOARD_URL, TELEGRAM_BOT_TOKEN
from core.db import SessionLocal
from core.expenses import (
    apagar_despesa,
    atualizar_despesa,
    converter_data_escrita,
    converter_valor_para_centimos,
    garantir_categorias_por_defeito,
    guardar_despesa,
    obter_ou_criar_utilizador,
    obter_timezone,
    obter_ultima_despesa,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

FRASES_APAGADA = [
    "Pronto, apaguei essa 👍",
    "Já está, essa desapareceu.",
    "Feito! Tirei essa da lista.",
    "Apagada. Como se nunca tivesse existido 😉",
]

FRASES_JA_NAO_EXISTE = [
    "Essa já não estava cá.",
    "Hmm, essa despesa já não existe.",
]

PERGUNTA_APAGAR = "\nApago mesmo esta?"

TEXTO_ACESSO = (
    "Aqui tens o acesso à dashboard 👇\n"
    "{link}\n\n"
    "Se a dashboard estiver aberta noutro dispositivo, escreve lá este código: {codigo}\n\n"
    "Só serve uma vez e expira daqui a 5 minutos."
)

PERGUNTAS = {
    "valor": "Quanto foi? Escreve só o valor (ex: 35,50).",
    "comerciante": "Onde foi? Escreve o nome.",
    "data": "Que dia foi? Escreve a data (ex: 01/09/2026).",
}


def teclado_apagar(despesa_id):
    botao = InlineKeyboardButton("Apagar", callback_data="apagar:" + str(despesa_id))
    return InlineKeyboardMarkup([[botao]])


def teclado_editar():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Valor", callback_data="editar:valor"),
                InlineKeyboardButton("Categoria", callback_data="editar:categoria"),
            ],
            [
                InlineKeyboardButton("Comerciante", callback_data="editar:comerciante"),
                InlineKeyboardButton("Data", callback_data="editar:data"),
            ],
            [InlineKeyboardButton("Cancelar", callback_data="editar:cancelar")],
        ]
    )


def teclado_confirmar_apagar(despesa_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Sim, apagar", callback_data="confirmar:" + str(despesa_id)),
                InlineKeyboardButton("Cancelar", callback_data="confirmar:nao"),
            ]
        ]
    )


def teclado_cancelar():
    botao = InlineKeyboardButton("Cancelar", callback_data="editar:cancelar")
    return InlineKeyboardMarkup([[botao]])


def teclado_categorias():
    linhas = []
    for i in range(0, len(CATEGORIAS), 2):
        linha = []
        for nome in CATEGORIAS[i : i + 2]:
            linha.append(InlineKeyboardButton(nome, callback_data="categoria:" + nome))
        linhas.append(linha)

    linhas.append([InlineKeyboardButton("Cancelar", callback_data="editar:cancelar")])
    return InlineKeyboardMarkup(linhas)


def resumo_despesa(despesa):
    valor = despesa["amount_cents"] / 100
    partes = ["%.2f %s" % (valor, despesa["currency"])]

    if despesa["merchant"]:
        partes.append(despesa["merchant"])
    if despesa["category"]:
        partes.append(despesa["category"])

    partes.append(despesa["date"])
    return " · ".join(partes)


def limpar_edicao(context):
    context.user_data.pop("campo_a_editar", None)
    context.user_data.pop("despesa_a_editar", None)


def mensagem_de_acesso(telegram_user_id, nome):
    session = SessionLocal()
    try:
        utilizador = obter_ou_criar_utilizador(session, telegram_user_id, nome)
        codigo = criar_codigo_de_acesso(session, utilizador.id)
    finally:
        session.close()

    link = DASHBOARD_URL + "/login?code=" + codigo
    return TEXTO_ACESSO.format(link=link, codigo=codigo)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limpar_edicao(context)
    await update.message.reply_text(
        "Olá! Sou o Finas. Escreve-me as tuas despesas como falarias com um amigo. "
        'Por exemplo: "hoje gastei 30 euros na fnac".'
    )
    await update.message.reply_text(
        mensagem_de_acesso(update.effective_user.id, update.effective_user.first_name),
        disable_web_page_preview=True,
    )


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limpar_edicao(context)
    await update.message.reply_text(
        mensagem_de_acesso(update.effective_user.id, update.effective_user.first_name),
        disable_web_page_preview=True,
    )


async def comando_apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limpar_edicao(context)

    session = SessionLocal()
    try:
        ultima_despesa = obter_ultima_despesa(session, update.effective_user.id)
    finally:
        session.close()

    if ultima_despesa is None:
        await update.message.reply_text("Ainda não tens nenhuma despesa registada.")
        return

    await update.message.reply_text(
        "Última despesa: " + resumo_despesa(ultima_despesa) + PERGUNTA_APAGAR,
        reply_markup=teclado_confirmar_apagar(ultima_despesa["id"]),
    )


async def confirmar_apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    escolha = query.data.split(":")[1]
    if escolha == "nao":
        await query.edit_message_text("Ok, não apaguei nada.")
        return

    session = SessionLocal()
    try:
        apagou = apagar_despesa(session, int(escolha), update.effective_user.id)
    finally:
        session.close()

    if apagou:
        await query.edit_message_text(random.choice(FRASES_APAGADA))
    else:
        await query.edit_message_text(random.choice(FRASES_JA_NAO_EXISTE))


async def editar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limpar_edicao(context)

    session = SessionLocal()
    try:
        ultima_despesa = obter_ultima_despesa(session, update.effective_user.id)
    finally:
        session.close()

    if ultima_despesa is None:
        await update.message.reply_text("Ainda não tens nenhuma despesa registada.")
        return

    context.user_data["despesa_a_editar"] = ultima_despesa["id"]

    await update.message.reply_text(
        "Última despesa: " + resumo_despesa(ultima_despesa) + "\nO que queres mudar?",
        reply_markup=teclado_editar(),
    )


async def escolher_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    campo = query.data.split(":")[1]

    if campo == "cancelar":
        limpar_edicao(context)
        await query.edit_message_text("Ok, deixei ficar como estava.")
        return

    if context.user_data.get("despesa_a_editar") is None:
        await query.edit_message_text("Já não sei qual era a despesa. Escreve /editar outra vez.")
        return

    context.user_data["campo_a_editar"] = campo

    if campo == "categoria":
        await query.edit_message_text("Escolhe a categoria:", reply_markup=teclado_categorias())
        return

    await query.edit_message_text(PERGUNTAS[campo], reply_markup=teclado_cancelar())


async def escolher_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    despesa_id = context.user_data.get("despesa_a_editar")
    if despesa_id is None:
        await query.edit_message_text("Já não sei qual era a despesa. Escreve /editar outra vez.")
        return

    nome = query.data.split(":")[1]

    session = SessionLocal()
    try:
        atualizada = atualizar_despesa(
            session, despesa_id, update.effective_user.id, {"category": nome}
        )
        ultima_despesa = obter_ultima_despesa(session, update.effective_user.id)
    finally:
        session.close()

    limpar_edicao(context)

    if atualizada is None:
        await query.edit_message_text(random.choice(FRASES_JA_NAO_EXISTE))
        return

    await query.edit_message_text("Feito! Agora está: " + resumo_despesa(ultima_despesa))


async def aplicar_edicao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    campo = context.user_data.get("campo_a_editar")
    despesa_id = context.user_data.get("despesa_a_editar")
    texto = update.message.text

    campos = {}
    if campo == "valor":
        centimos = converter_valor_para_centimos(texto)
        if centimos is None:
            await update.message.reply_text(
                "Não percebi o valor. Escreve só o número (ex: 35,50).",
                reply_markup=teclado_cancelar(),
            )
            return
        campos["amount_cents"] = centimos

    if campo == "comerciante":
        campos["merchant"] = texto.strip()

    if campo == "data":
        data = converter_data_escrita(texto)
        if data is None:
            await update.message.reply_text(
                "Não percebi a data. Escreve assim: 01/09/2026.",
                reply_markup=teclado_cancelar(),
            )
            return
        campos["expense_date"] = data

    session = SessionLocal()
    try:
        atualizada = atualizar_despesa(session, despesa_id, update.effective_user.id, campos)
        ultima_despesa = obter_ultima_despesa(session, update.effective_user.id)
    finally:
        session.close()

    limpar_edicao(context)

    if atualizada is None:
        await update.message.reply_text(random.choice(FRASES_JA_NAO_EXISTE))
        return

    await update.message.reply_text("Feito! Agora está: " + resumo_despesa(ultima_despesa))


async def mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    telegram_user_id = update.effective_user.id

    if context.user_data.get("campo_a_editar"):
        await aplicar_edicao(update, context)
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    session = SessionLocal()
    try:
        ultima_despesa = obter_ultima_despesa(session, telegram_user_id)
        timezone_utilizador = obter_timezone(session, telegram_user_id)

        try:
            resultado = await asyncio.to_thread(
                parse_mensagem, texto, timezone_utilizador, ultima_despesa
            )
        except Exception:
            logger.exception("Não consegui processar a mensagem")
            await update.message.reply_text(frase_de_recurso())
            return

        if resultado.e_correcao and ultima_despesa is not None:
            atualizar_despesa(
                session,
                ultima_despesa["id"],
                telegram_user_id,
                campos_da_correcao(resultado, timezone_utilizador),
            )
            await update.message.reply_text(
                resultado.resposta, reply_markup=teclado_apagar(ultima_despesa["id"])
            )
            return

        despesa = construir_despesa_nova(resultado, timezone_utilizador)
        if despesa is None:
            await update.message.reply_text(resultado.resposta)
            return

        guardada = guardar_despesa(
            session,
            telegram_user_id,
            despesa,
            texto,
            update.effective_user.first_name,
        )
        await update.message.reply_text(
            resultado.resposta, reply_markup=teclado_apagar(guardada.id)
        )
    except Exception:
        logger.exception("Não consegui guardar a despesa")
        await update.message.reply_text(frase_de_recurso())
    finally:
        session.close()


async def apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    despesa_id = int(query.data.split(":")[1])

    session = SessionLocal()
    try:
        apagou = apagar_despesa(session, despesa_id, update.effective_user.id)
    finally:
        session.close()

    if apagou:
        await query.edit_message_text(random.choice(FRASES_APAGADA))
    else:
        await query.edit_message_text(random.choice(FRASES_JA_NAO_EXISTE))


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN no .env")

    session = SessionLocal()
    try:
        garantir_categorias_por_defeito(session)
    finally:
        session.close()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("entrar", dashboard))
    app.add_handler(CommandHandler("editar", editar))
    app.add_handler(CommandHandler("apagar", comando_apagar))
    app.add_handler(CallbackQueryHandler(apagar, pattern="^apagar:"))
    app.add_handler(CallbackQueryHandler(escolher_campo, pattern="^editar:"))
    app.add_handler(CallbackQueryHandler(escolher_categoria, pattern="^categoria:"))
    app.add_handler(CallbackQueryHandler(confirmar_apagar, pattern="^confirmar:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem))
    app.run_polling()


if __name__ == "__main__":
    main()
