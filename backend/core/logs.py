import logging
import sys

from core.config import LOG_LEVEL

NIVEIS = ["DEBUG", "INFO", "WARNING", "ERROR"]

MENOS_FALADORES = [
    "httpx",
    "httpx2",
    "httpcore",
    "telegram.ext.Application",
    "openai",
]


def nivel_de_log():
    if LOG_LEVEL in NIVEIS:
        return LOG_LEVEL

    return "INFO"


def configurar_logging(servico):
    logging.basicConfig(
        level=nivel_de_log(),
        format="%(asctime)s %(levelname)s [" + servico + "] %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )

    for nome in MENOS_FALADORES:
        logging.getLogger(nome).setLevel(logging.WARNING)
