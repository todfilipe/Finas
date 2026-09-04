import logging

import pytest

from core import alerts
from core.alerts import (
    alertas_ligados,
    avisar_erro,
    descrever_erro,
    montar_texto,
    ultimos_avisos,
)
from core.logs import configurar_logging, nivel_de_log


class FakeResposta:
    def __init__(self, rebenta=False):
        self.rebenta = rebenta

    def raise_for_status(self):
        if self.rebenta:
            raise RuntimeError("o telegram devolveu 400")


@pytest.fixture
def alertas_a_funcionar(monkeypatch):
    ultimos_avisos.clear()
    monkeypatch.setattr(alerts, "TELEGRAM_BOT_TOKEN", "token-de-teste")
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "555")
    monkeypatch.setattr(alerts, "ALERT_MINUTES", 5)

    enviados = []

    def fake_post(url, json=None, timeout=None):
        enviados.append({"url": url, "json": json})
        return FakeResposta()

    monkeypatch.setattr(alerts.httpx, "post", fake_post)
    return enviados


def test_sem_admin_nao_ha_alertas(monkeypatch):
    monkeypatch.setattr(alerts, "TELEGRAM_BOT_TOKEN", "token-de-teste")
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "")

    assert alertas_ligados() is False


def test_sem_token_nao_ha_alertas(monkeypatch):
    monkeypatch.setattr(alerts, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "555")

    assert alertas_ligados() is False


def test_alertas_desligados_nao_enviam_nada(monkeypatch):
    ultimos_avisos.clear()
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "")

    def nao_pode_ser_chamado(url, json=None, timeout=None):
        raise AssertionError("nao devia ter enviado nada")

    monkeypatch.setattr(alerts.httpx, "post", nao_pode_ser_chamado)

    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is False


def test_alerta_vai_para_o_admin(alertas_a_funcionar):
    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is True

    enviado = alertas_a_funcionar[0]
    assert "token-de-teste" in enviado["url"]
    assert enviado["json"]["chat_id"] == "555"
    assert "GET /expenses" in enviado["json"]["text"]
    assert "RuntimeError: boom" in enviado["json"]["text"]


def test_alerta_diz_em_que_servico_foi(alertas_a_funcionar):
    avisar_erro("no bot", "guardar a despesa", ValueError("valor errado"))

    assert "erro no bot" in alertas_a_funcionar[0]["json"]["text"]


def test_erro_igual_seguido_so_avisa_uma_vez(alertas_a_funcionar):
    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is True
    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is False
    assert avisar_erro("na API", "GET /expenses", RuntimeError("outro texto")) is False

    assert len(alertas_a_funcionar) == 1


def test_erro_diferente_avisa_a_mesma(alertas_a_funcionar):
    avisar_erro("na API", "GET /expenses", RuntimeError("boom"))
    avisar_erro("na API", "GET /expenses", ValueError("boom"))
    avisar_erro("na API", "POST /auth/verify", RuntimeError("boom"))

    assert len(alertas_a_funcionar) == 3


def test_erro_igual_avisa_outra_vez_passado_o_tempo(alertas_a_funcionar, monkeypatch):
    avisar_erro("na API", "GET /expenses", RuntimeError("boom"))

    for chave in ultimos_avisos:
        ultimos_avisos[chave] = ultimos_avisos[chave] - 6 * 60

    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is True
    assert len(alertas_a_funcionar) == 2


def test_telegram_em_baixo_nao_rebenta(monkeypatch, caplog):
    ultimos_avisos.clear()
    monkeypatch.setattr(alerts, "TELEGRAM_BOT_TOKEN", "token-de-teste")
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "555")

    def fake_post(url, json=None, timeout=None):
        raise RuntimeError("sem rede")

    monkeypatch.setattr(alerts.httpx, "post", fake_post)

    with caplog.at_level(logging.WARNING):
        assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is False

    assert "Nao consegui enviar o alerta" in caplog.text


def test_telegram_a_recusar_nao_rebenta(monkeypatch):
    ultimos_avisos.clear()
    monkeypatch.setattr(alerts, "TELEGRAM_BOT_TOKEN", "token-de-teste")
    monkeypatch.setattr(alerts, "ADMIN_TELEGRAM_ID", "555")

    def fake_post(url, json=None, timeout=None):
        return FakeResposta(rebenta=True)

    monkeypatch.setattr(alerts.httpx, "post", fake_post)

    assert avisar_erro("na API", "GET /expenses", RuntimeError("boom")) is False


def test_erro_muito_grande_e_cortado():
    descricao = descrever_erro(RuntimeError("x" * 1000))

    assert len(descricao) < 400
    assert descricao.endswith("...")


def test_erro_sem_texto_mostra_so_o_tipo():
    assert descrever_erro(RuntimeError()) == "RuntimeError"


def test_texto_do_alerta_tem_tres_linhas():
    texto = montar_texto("na API", "GET /expenses", RuntimeError("boom"))

    assert texto.split("\n") == ["🔴 Finas: erro na API", "GET /expenses", "RuntimeError: boom"]


def test_nivel_de_log_por_defeito(monkeypatch):
    monkeypatch.setattr("core.logs.LOG_LEVEL", "TAGARELA")

    assert nivel_de_log() == "INFO"


def test_nivel_de_log_configurado(monkeypatch):
    monkeypatch.setattr("core.logs.LOG_LEVEL", "DEBUG")

    assert nivel_de_log() == "DEBUG"


def test_configurar_logging_poe_o_nome_do_servico(capsys):
    configurar_logging("teste")
    logging.getLogger("qualquer").info("uma mensagem")

    assert "[teste]" in capsys.readouterr().out


def test_configurar_logging_cala_as_bibliotecas_faladoras(capsys):
    configurar_logging("teste")

    for nome in ["httpx", "httpx2", "httpcore", "openai"]:
        logging.getLogger(nome).info("um pedido qualquer")

    assert "um pedido qualquer" not in capsys.readouterr().out


def test_configurar_logging_deixa_passar_os_avisos_das_bibliotecas(capsys):
    configurar_logging("teste")
    logging.getLogger("httpx2").warning("isto e importante")

    assert "isto e importante" in capsys.readouterr().out
