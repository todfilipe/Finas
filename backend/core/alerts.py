import logging
import time

import httpx

from core.config import ADMIN_TELEGRAM_ID, ALERT_MINUTES, TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_DO_ERRO = 300

SEGUNDOS_DE_ESPERA = 5

ultimos_avisos = {}


def alertas_ligados():
    if not TELEGRAM_BOT_TOKEN:
        return False

    if not ADMIN_TELEGRAM_ID:
        return False

    return True


def ja_avisei_ha_pouco(chave, agora):
    ultimo = ultimos_avisos.get(chave)
    if ultimo is None:
        return False

    return agora - ultimo < ALERT_MINUTES * 60


def descrever_erro(erro):
    detalhe = str(erro)
    if len(detalhe) > TAMANHO_MAXIMO_DO_ERRO:
        detalhe = detalhe[:TAMANHO_MAXIMO_DO_ERRO] + "..."

    if detalhe == "":
        return type(erro).__name__

    return type(erro).__name__ + ": " + detalhe


def montar_texto(servico, onde, erro):
    return "🔴 Finas: erro " + servico + "\n" + onde + "\n" + descrever_erro(erro)


def enviar_ao_telegram(texto):
    url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
    resposta = httpx.post(
        url,
        json={"chat_id": ADMIN_TELEGRAM_ID, "text": texto},
        timeout=SEGUNDOS_DE_ESPERA,
    )
    resposta.raise_for_status()


def avisar_erro(servico, onde, erro):
    if not alertas_ligados():
        return False

    agora = time.time()
    chave = servico + "|" + onde + "|" + type(erro).__name__
    if ja_avisei_ha_pouco(chave, agora):
        return False

    ultimos_avisos[chave] = agora

    try:
        enviar_ao_telegram(montar_texto(servico, onde, erro))
    except Exception:
        logger.warning("Nao consegui enviar o alerta para o Telegram")
        return False

    return True
