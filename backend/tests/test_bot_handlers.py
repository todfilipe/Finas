import asyncio
import logging
from datetime import date

import pytest
from sqlalchemy import select

from telegram.ext import CallbackQueryHandler

from bot import main as bot
from core.ai_parsing import FRASES_DE_RECURSO, DespesaDaIA, DespesaNova, RespostaIA
from core.categories import CATEGORIAS, CATEGORIAS_RECEITA, TIPO_RECEITA
from core.expenses import guardar_despesa, obter_ultima_despesa
from core.models import Expense


class FakeChat:
    def __init__(self):
        self.acoes = []

    async def send_action(self, acao):
        self.acoes.append(acao)


class FakeMensagem:
    def __init__(self, texto):
        self.text = texto
        self.chat = FakeChat()
        self.respostas = []
        self.teclados = []

    async def reply_text(self, texto, reply_markup=None, disable_web_page_preview=None):
        self.respostas.append(texto)
        self.teclados.append(reply_markup)


class FakeQuery:
    def __init__(self, dados):
        self.data = dados
        self.respondeu = False
        self.textos = []
        self.teclados = []

    async def answer(self, texto=None):
        self.respondeu = True
        if texto is not None:
            self.textos.append(texto)

    async def edit_message_text(self, texto, reply_markup=None):
        self.textos.append(texto)
        self.teclados.append(reply_markup)


class FakeUtilizador:
    def __init__(self, telegram_user_id, nome):
        self.id = telegram_user_id
        self.first_name = nome


class FakeUpdate:
    def __init__(self, texto=None, dados=None, telegram_user_id=111, nome="Filipe"):
        self.message = None
        self.callback_query = None

        if texto is not None:
            self.message = FakeMensagem(texto)
        if dados is not None:
            self.callback_query = FakeQuery(dados)

        self.effective_user = FakeUtilizador(telegram_user_id, nome)


class FakeContext:
    def __init__(self):
        self.user_data = {}


def correr(coroutine):
    return asyncio.run(coroutine)


@pytest.fixture(autouse=True)
def limites_limpos():
    bot.mensagens_por_utilizador.clear()
    yield
    bot.mensagens_por_utilizador.clear()


@pytest.fixture
def bot_session(session, monkeypatch):
    monkeypatch.setattr(bot, "SessionLocal", lambda: session)
    return session


def criar_despesa(session, telegram_user_id=111, **campos):
    base = {
        "kind": "expense",
        "amount_cents": 3000,
        "currency": "EUR",
        "category": "Tecnologia",
        "subcategory": None,
        "merchant": "Fnac",
        "description": None,
        "expense_date": date(2026, 1, 15),
        "payment_method": None,
        "confidence": 0.9,
        "needs_confirmation": False,
    }
    base.update(campos)
    guardada = guardar_despesa(
        session, telegram_user_id, DespesaNova(**base), "gastei 30 na fnac", "Filipe"
    )
    return guardada.id


def despesa_ia(**campos):
    base = {
        "kind": "expense",
        "amount_cents": 1000,
        "currency": "EUR",
        "category": "Alimentação",
        "subcategory": None,
        "merchant": "Café Central",
        "description": None,
        "date": "2026-01-15",
        "payment_method": None,
        "confidence": 0.9,
        "needs_confirmation": False,
    }
    base.update(campos)
    return DespesaDaIA(**base)


def resposta_ia(resposta="Anotado!", e_despesa=True, e_correcao=False, despesas=None):
    if despesas is None:
        despesas = []

    return RespostaIA(
        e_despesa=e_despesa,
        e_correcao=e_correcao,
        despesas=despesas,
        resposta=resposta,
    )


def fingir_ia(monkeypatch, resultado):
    def fake_parse(texto, timezone_utilizador, candidatas, nomes, nomes_receita):
        return resultado

    monkeypatch.setattr(bot, "parse_mensagem", fake_parse)


def contar_despesas(session):
    return len(list(session.scalars(select(Expense)).all()))


def nomes_das_categorias(teclado):
    nomes = []
    for linha in teclado.inline_keyboard:
        for botao in linha:
            if botao.callback_data.startswith("categoria:"):
                nomes.append(botao.text)

    return nomes


def test_start_diz_ola_e_manda_o_acesso(bot_session):
    update = FakeUpdate(texto="/start")
    context = FakeContext()

    correr(bot.start(update, context))

    assert len(update.message.respostas) == 2
    assert "Finas" in update.message.respostas[0]
    assert "/login?code=" in update.message.respostas[1]


def test_start_limpa_uma_edicao_a_meio(bot_session):
    update = FakeUpdate(texto="/start")
    context = FakeContext()
    context.user_data["campo_a_editar"] = "valor"
    context.user_data["despesa_a_editar"] = 1

    correr(bot.start(update, context))

    assert context.user_data == {}


def test_dashboard_manda_link_e_codigo(bot_session):
    update = FakeUpdate(texto="/dashboard")

    correr(bot.dashboard(update, FakeContext()))

    texto = update.message.respostas[0]
    assert "/login?code=" in texto
    assert "expira" in texto


def test_comando_apagar_sem_despesas(bot_session):
    update = FakeUpdate(texto="/apagar")

    correr(bot.comando_apagar(update, FakeContext()))

    assert update.message.respostas == ["Ainda não tens nenhuma despesa registada."]
    assert update.message.teclados[0] is None


def test_comando_apagar_mostra_a_ultima_e_pergunta(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="/apagar")

    correr(bot.comando_apagar(update, FakeContext()))

    assert bot.PERGUNTA_APAGAR in update.message.respostas[0]
    assert "30.00 EUR" in update.message.respostas[0]
    botao = update.message.teclados[0].inline_keyboard[0][0]
    assert botao.callback_data == "confirmar:" + str(despesa_id)


def test_confirmar_apagar_com_nao_nao_apaga(bot_session):
    criar_despesa(bot_session)
    update = FakeUpdate(dados="confirmar:nao")

    correr(bot.confirmar_apagar(update, FakeContext()))

    assert update.callback_query.textos == ["Ok, não apaguei nada."]
    assert obter_ultima_despesa(bot_session, 111) is not None


def test_confirmar_apagar_apaga_mesmo(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="confirmar:" + str(despesa_id))

    correr(bot.confirmar_apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_APAGADA
    assert obter_ultima_despesa(bot_session, 111) is None


def test_confirmar_apagar_de_uma_despesa_que_ja_nao_existe(bot_session):
    criar_despesa(bot_session)
    update = FakeUpdate(dados="confirmar:9999")

    correr(bot.confirmar_apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_JA_NAO_EXISTE


def test_callback_responde_sempre_ao_telegram(bot_session):
    update = FakeUpdate(dados="confirmar:nao")

    correr(bot.confirmar_apagar(update, FakeContext()))

    assert update.callback_query.respondeu is True


def test_editar_sem_despesas(bot_session):
    update = FakeUpdate(texto="/editar")
    context = FakeContext()

    correr(bot.editar(update, context))

    assert update.message.respostas == ["Ainda não tens nenhuma despesa registada."]
    assert "despesa_a_editar" not in context.user_data


def test_editar_guarda_a_despesa_e_mostra_os_campos(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="/editar")
    context = FakeContext()

    correr(bot.editar(update, context))

    assert context.user_data["despesa_a_editar"] == despesa_id
    assert "O que queres mudar?" in update.message.respostas[0]
    assert len(update.message.teclados[0].inline_keyboard) == 3


def test_escolher_campo_cancelar_limpa_tudo(bot_session):
    update = FakeUpdate(dados="editar:cancelar")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = 1
    context.user_data["campo_a_editar"] = "valor"

    correr(bot.escolher_campo(update, context))

    assert context.user_data == {}
    assert update.callback_query.textos == ["Ok, deixei ficar como estava."]


def test_escolher_campo_sem_despesa_guardada(bot_session):
    update = FakeUpdate(dados="editar:valor")
    context = FakeContext()

    correr(bot.escolher_campo(update, context))

    assert "escreve /editar outra vez" in update.callback_query.textos[0].lower()
    assert "campo_a_editar" not in context.user_data


def test_escolher_campo_valor_faz_a_pergunta(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="editar:valor")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id

    correr(bot.escolher_campo(update, context))

    assert context.user_data["campo_a_editar"] == "valor"
    assert update.callback_query.textos == [bot.PERGUNTAS["valor"]]


def test_escolher_campo_data_faz_a_pergunta(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="editar:data")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id

    correr(bot.escolher_campo(update, context))

    assert update.callback_query.textos == [bot.PERGUNTAS["data"]]


def test_escolher_campo_categoria_mostra_as_de_despesa(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="editar:categoria")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id

    correr(bot.escolher_campo(update, context))

    nomes = nomes_das_categorias(update.callback_query.teclados[0])
    assert sorted(nomes) == sorted(CATEGORIAS)


def test_escolher_campo_categoria_de_receita_mostra_as_de_receita(bot_session):
    receita_id = criar_despesa(bot_session, kind=TIPO_RECEITA, category="Salário")
    update = FakeUpdate(dados="editar:categoria")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = receita_id

    correr(bot.escolher_campo(update, context))

    nomes = nomes_das_categorias(update.callback_query.teclados[0])
    assert sorted(nomes) == sorted(CATEGORIAS_RECEITA)


def test_escolher_categoria_muda_a_categoria(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="categoria:Lazer")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id

    correr(bot.escolher_categoria(update, context))

    assert obter_ultima_despesa(bot_session, 111)["category"] == "Lazer"
    assert "Lazer" in update.callback_query.textos[0]
    assert context.user_data == {}


def test_escolher_categoria_sem_despesa_guardada(bot_session):
    update = FakeUpdate(dados="categoria:Lazer")

    correr(bot.escolher_categoria(update, FakeContext()))

    assert "escreve /editar outra vez" in update.callback_query.textos[0].lower()


def test_escolher_categoria_de_despesa_apagada(bot_session):
    update = FakeUpdate(dados="categoria:Lazer")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = 9999

    correr(bot.escolher_categoria(update, context))

    assert update.callback_query.textos[0] in bot.FRASES_JA_NAO_EXISTE


def test_aplicar_edicao_muda_o_valor(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="12,50")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "valor"

    correr(bot.aplicar_edicao(update, context))

    assert obter_ultima_despesa(bot_session, 111)["amount_cents"] == 1250
    assert context.user_data == {}


def test_aplicar_edicao_com_valor_que_nao_se_percebe(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="muito dinheiro")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "valor"

    correr(bot.aplicar_edicao(update, context))

    assert "Não percebi o valor" in update.message.respostas[0]
    assert obter_ultima_despesa(bot_session, 111)["amount_cents"] == 3000
    assert context.user_data["campo_a_editar"] == "valor"


def test_aplicar_edicao_muda_o_comerciante(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="  Continente  ")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "comerciante"

    correr(bot.aplicar_edicao(update, context))

    assert obter_ultima_despesa(bot_session, 111)["merchant"] == "Continente"


def test_aplicar_edicao_muda_a_data(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="01/02/2026")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "data"

    correr(bot.aplicar_edicao(update, context))

    assert obter_ultima_despesa(bot_session, 111)["date"] == "2026-02-01"


def test_aplicar_edicao_com_data_que_nao_se_percebe(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(texto="para a semana")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "data"

    correr(bot.aplicar_edicao(update, context))

    assert "Não percebi a data" in update.message.respostas[0]
    assert obter_ultima_despesa(bot_session, 111)["date"] == "2026-01-15"


def test_aplicar_edicao_de_despesa_apagada(bot_session):
    criar_despesa(bot_session)
    update = FakeUpdate(texto="12,50")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = 9999
    context.user_data["campo_a_editar"] = "valor"

    correr(bot.aplicar_edicao(update, context))

    assert update.message.respostas[0] in bot.FRASES_JA_NAO_EXISTE


def test_mensagem_com_edicao_a_meio_vai_para_a_edicao(bot_session, monkeypatch):
    despesa_id = criar_despesa(bot_session)
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))
    update = FakeUpdate(texto="12,50")
    context = FakeContext()
    context.user_data["despesa_a_editar"] = despesa_id
    context.user_data["campo_a_editar"] = "valor"

    correr(bot.mensagem(update, context))

    assert obter_ultima_despesa(bot_session, 111)["amount_cents"] == 1250
    assert contar_despesas(bot_session) == 1


def test_mensagem_guarda_uma_despesa(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia("Anotado! 10 euros no café.", despesas=[despesa_ia()]))
    update = FakeUpdate(texto="gastei 10 no café")
    context = FakeContext()

    correr(bot.mensagem(update, context))

    ultima = obter_ultima_despesa(bot_session, 111)
    assert ultima["amount_cents"] == 1000
    assert ultima["merchant"] == "Café Central"
    assert update.message.respostas == ["Anotado! 10 euros no café."]
    assert context.user_data["ultimas_despesas"] == [ultima["id"]]


def test_mensagem_avisa_que_esta_a_escrever(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))
    update = FakeUpdate(texto="gastei 10 no café")

    correr(bot.mensagem(update, FakeContext()))

    assert len(update.message.chat.acoes) == 1


def test_mensagem_guarda_varias_despesas(bot_session, monkeypatch):
    duas = [despesa_ia(), despesa_ia(amount_cents=2000, merchant="Almoço")]
    fingir_ia(monkeypatch, resposta_ia("Guardei as duas!", despesas=duas))
    update = FakeUpdate(texto="gastei 10 no café e 20 no almoço")
    context = FakeContext()

    correr(bot.mensagem(update, context))

    assert contar_despesas(bot_session) == 2
    assert len(context.user_data["ultimas_despesas"]) == 2
    assert update.message.teclados[0].inline_keyboard[0][0].text == "Apagar as 2"


def test_mensagem_que_nao_e_despesa_nao_guarda_nada(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia("Olá! Tudo bem?", e_despesa=False))
    update = FakeUpdate(texto="bom dia")
    context = FakeContext()

    correr(bot.mensagem(update, context))

    assert contar_despesas(bot_session) == 0
    assert update.message.respostas == ["Olá! Tudo bem?"]
    assert update.message.teclados[0] is None
    assert "ultimas_despesas" not in context.user_data


def test_mensagem_quando_a_ia_rebenta(bot_session, monkeypatch):
    def fake_parse(texto, timezone_utilizador, candidatas, nomes, nomes_receita):
        raise RuntimeError("a ia foi abaixo")

    monkeypatch.setattr(bot, "parse_mensagem", fake_parse)
    update = FakeUpdate(texto="gastei 10 no café")

    correr(bot.mensagem(update, FakeContext()))

    assert update.message.respostas[0] in FRASES_DE_RECURSO
    assert contar_despesas(bot_session) == 0


def test_mensagem_quando_guardar_rebenta(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    def fake_guardar(session, telegram_user_id, despesa, raw_message=None, nome=None):
        raise RuntimeError("a base de dados foi abaixo")

    monkeypatch.setattr(bot, "guardar_despesa", fake_guardar)
    update = FakeUpdate(texto="gastei 10 no café")

    correr(bot.mensagem(update, FakeContext()))

    assert update.message.respostas[0] in FRASES_DE_RECURSO


def test_correcao_com_uma_candidata_atualiza_logo(bot_session, monkeypatch):
    despesa_id = criar_despesa(bot_session)
    correcao = despesa_ia(amount_cents=None, merchant="Continente", category=None, date=None)
    fingir_ia(monkeypatch, resposta_ia("Corrigido!", e_correcao=True, despesas=[correcao]))
    update = FakeUpdate(texto="não foi na fnac, foi no continente")
    context = FakeContext()
    context.user_data["ultimas_despesas"] = [despesa_id]

    correr(bot.mensagem(update, context))

    assert obter_ultima_despesa(bot_session, 111)["merchant"] == "Continente"
    assert contar_despesas(bot_session) == 1
    assert update.message.respostas == ["Corrigido!"]


def test_correcao_com_varias_candidatas_pergunta_qual(bot_session, monkeypatch):
    primeira_id = criar_despesa(bot_session, merchant="Café")
    segunda_id = criar_despesa(bot_session, merchant="Almoço", amount_cents=2000)
    correcao = despesa_ia(amount_cents=1500, merchant=None, category=None, date=None)
    fingir_ia(monkeypatch, resposta_ia("Qual?", e_correcao=True, despesas=[correcao]))
    update = FakeUpdate(texto="foram 15 e não 10")
    context = FakeContext()
    context.user_data["ultimas_despesas"] = [primeira_id, segunda_id]

    correr(bot.mensagem(update, context))

    assert update.message.respostas[0] in bot.PERGUNTAS_QUAL_DESPESA
    assert context.user_data["correcao_pendente"] == {"amount_cents": 1500, "currency": "EUR"}
    assert context.user_data["despesas_a_escolher"] == [primeira_id, segunda_id]
    assert obter_ultima_despesa(bot_session, 111)["amount_cents"] == 2000


def test_correcao_sem_despesas_anteriores_nao_guarda_nada(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia("Anotado!", e_correcao=True, despesas=[despesa_ia()]))
    update = FakeUpdate(texto="afinal foram 10")

    correr(bot.mensagem(update, FakeContext()))

    assert contar_despesas(bot_session) == 0


def test_mensagem_nova_limpa_a_correcao_pendente(bot_session, monkeypatch):
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))
    update = FakeUpdate(texto="gastei 10 no café")
    context = FakeContext()
    context.user_data["correcao_pendente"] = {"amount_cents": 500}
    context.user_data["despesas_a_escolher"] = [1, 2]

    correr(bot.mensagem(update, context))

    assert "correcao_pendente" not in context.user_data
    assert "despesas_a_escolher" not in context.user_data


def test_apagar_uma_despesa(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="apagar:" + str(despesa_id))

    correr(bot.apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_APAGADA
    assert contar_despesas(bot_session) == 0


def test_apagar_varias_despesas(bot_session):
    primeira_id = criar_despesa(bot_session)
    segunda_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="apagar:%s-%s" % (primeira_id, segunda_id))

    correr(bot.apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_APAGADAS
    assert contar_despesas(bot_session) == 0


def test_apagar_quando_ja_nao_existe_nenhuma(bot_session):
    criar_despesa(bot_session)
    update = FakeUpdate(dados="apagar:8888-9999")

    correr(bot.apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_JA_NAO_EXISTE
    assert contar_despesas(bot_session) == 1


def test_apagar_nao_apaga_despesas_de_outro_utilizador(bot_session):
    despesa_id = criar_despesa(bot_session, telegram_user_id=111)
    update = FakeUpdate(dados="apagar:" + str(despesa_id), telegram_user_id=222)

    correr(bot.apagar(update, FakeContext()))

    assert update.callback_query.textos[0] in bot.FRASES_JA_NAO_EXISTE
    assert contar_despesas(bot_session) == 1


def test_escolher_despesa_da_correcao_aplica_na_escolhida(bot_session):
    primeira_id = criar_despesa(bot_session, merchant="Café", amount_cents=1000)
    segunda_id = criar_despesa(bot_session, merchant="Almoço", amount_cents=2000)
    update = FakeUpdate(dados="correcao:" + str(primeira_id))
    context = FakeContext()
    context.user_data["correcao_pendente"] = {"amount_cents": 1500}
    context.user_data["despesas_a_escolher"] = [primeira_id, segunda_id]

    correr(bot.escolher_despesa_da_correcao(update, context))

    assert bot_session.get(Expense, primeira_id).amount_cents == 1500
    assert bot_session.get(Expense, segunda_id).amount_cents == 2000
    assert context.user_data["ultimas_despesas"] == [primeira_id]
    assert "correcao_pendente" not in context.user_data


def test_escolher_despesa_da_correcao_cancelar(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="correcao:cancelar")
    context = FakeContext()
    context.user_data["correcao_pendente"] = {"amount_cents": 1500}
    context.user_data["despesas_a_escolher"] = [despesa_id]

    correr(bot.escolher_despesa_da_correcao(update, context))

    assert update.callback_query.textos == ["Ok, deixei ficar como estava."]
    assert bot_session.get(Expense, despesa_id).amount_cents == 3000
    assert context.user_data == {}


def test_escolher_despesa_da_correcao_sem_correcao_guardada(bot_session):
    despesa_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="correcao:" + str(despesa_id))

    correr(bot.escolher_despesa_da_correcao(update, FakeContext()))

    assert update.callback_query.textos == [bot.FRASE_CORRECAO_PERDIDA]


def test_escolher_despesa_da_correcao_com_id_que_nao_foi_oferecido(bot_session):
    primeira_id = criar_despesa(bot_session)
    segunda_id = criar_despesa(bot_session)
    update = FakeUpdate(dados="correcao:" + str(segunda_id))
    context = FakeContext()
    context.user_data["correcao_pendente"] = {"amount_cents": 1500}
    context.user_data["despesas_a_escolher"] = [primeira_id]

    correr(bot.escolher_despesa_da_correcao(update, context))

    assert update.callback_query.textos == [bot.FRASE_CORRECAO_PERDIDA]
    assert bot_session.get(Expense, segunda_id).amount_cents == 3000


def test_escolher_despesa_da_correcao_de_despesa_apagada(bot_session):
    update = FakeUpdate(dados="correcao:9999")
    context = FakeContext()
    context.user_data["correcao_pendente"] = {"amount_cents": 1500}
    context.user_data["despesas_a_escolher"] = [9999]

    correr(bot.escolher_despesa_da_correcao(update, context))

    assert update.callback_query.textos[0] in bot.FRASES_JA_NAO_EXISTE


def test_despesas_a_corrigir_usa_os_ids_da_ultima_mensagem(bot_session):
    primeira_id = criar_despesa(bot_session)
    segunda_id = criar_despesa(bot_session)
    context = FakeContext()
    context.user_data["ultimas_despesas"] = [primeira_id, segunda_id]

    candidatas = bot.despesas_a_corrigir(bot_session, 111, context)

    assert [d["id"] for d in candidatas] == [primeira_id, segunda_id]


def test_despesas_a_corrigir_sem_ids_usa_a_ultima(bot_session):
    criar_despesa(bot_session)
    segunda_id = criar_despesa(bot_session)

    candidatas = bot.despesas_a_corrigir(bot_session, 111, FakeContext())

    assert [d["id"] for d in candidatas] == [segunda_id]


def test_despesas_a_corrigir_sem_nada(bot_session):
    assert bot.despesas_a_corrigir(bot_session, 111, FakeContext()) == []


def test_categorias_do_utilizador_desconhecido(bot_session):
    assert bot.categorias_do_utilizador(bot_session, 999) == []


def test_resumo_curto_de_receita_leva_sinal():
    receita = {
        "id": 1,
        "kind": TIPO_RECEITA,
        "amount_cents": 120000,
        "currency": "EUR",
        "category": "Salário",
        "merchant": None,
    }

    assert bot.resumo_curto(receita) == "+1200.00 EUR · Salário"


def fingir_alertas(monkeypatch):
    avisos = []
    monkeypatch.setattr(
        bot, "avisar_erro", lambda servico, onde, erro: avisos.append((servico, onde, str(erro)))
    )
    return avisos


def test_onde_rebentou_numa_mensagem():
    assert bot.onde_rebentou(FakeUpdate(texto="gastei 10")) == "mensagem"


def test_onde_rebentou_num_botao():
    assert bot.onde_rebentou(FakeUpdate(dados="apagar:7")) == "botao apagar:7"


def test_onde_rebentou_sem_update():
    assert bot.onde_rebentou(None) == "sem update"


def test_erro_do_bot_avisa_o_admin(monkeypatch):
    avisos = fingir_alertas(monkeypatch)
    context = FakeContext()
    context.error = RuntimeError("boom")

    correr(bot.erro_do_bot(FakeUpdate(texto="gastei 10"), context))

    assert avisos == [("no bot", "mensagem", "boom")]


def erro_ja_lancado(mensagem):
    try:
        raise RuntimeError(mensagem)
    except RuntimeError as erro:
        return erro


def test_erro_do_bot_fica_no_log(monkeypatch, caplog):
    fingir_alertas(monkeypatch)
    context = FakeContext()
    context.error = erro_ja_lancado("boom")

    with caplog.at_level(logging.ERROR, logger="bot.main"):
        correr(bot.erro_do_bot(FakeUpdate(dados="apagar:7"), context))

    assert "botao apagar:7" in caplog.text
    assert "Traceback" in caplog.text


def test_ia_em_baixo_avisa_o_admin(bot_session, monkeypatch):
    avisos = fingir_alertas(monkeypatch)

    def fake_parse(texto, timezone_utilizador, candidatas, nomes, nomes_receita):
        raise RuntimeError("a ia foi abaixo")

    monkeypatch.setattr(bot, "parse_mensagem", fake_parse)
    update = FakeUpdate(texto="gastei 10 no café")

    correr(bot.mensagem(update, FakeContext()))

    assert avisos == [("no bot", "parsing da mensagem", "a ia foi abaixo")]
    assert update.message.respostas[0] in FRASES_DE_RECURSO


def test_guardar_em_baixo_avisa_o_admin(bot_session, monkeypatch):
    avisos = fingir_alertas(monkeypatch)
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    def fake_guardar(session, telegram_user_id, despesa, raw_message=None, nome=None):
        raise RuntimeError("a base de dados foi abaixo")

    monkeypatch.setattr(bot, "guardar_despesa", fake_guardar)

    correr(bot.mensagem(FakeUpdate(texto="gastei 10 no café"), FakeContext()))

    assert avisos == [("no bot", "guardar a despesa", "a base de dados foi abaixo")]


def test_despesa_guardada_fica_no_log_sem_o_texto_da_pessoa(bot_session, monkeypatch, caplog):
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    with caplog.at_level(logging.INFO, logger="bot.main"):
        correr(bot.mensagem(FakeUpdate(texto="gastei 10 no café"), FakeContext()))

    assert "Guardei 1 movimentos do utilizador 111" in caplog.text
    assert "café" not in caplog.text


def test_lista_de_permitidos_vazia_deixa_entrar_toda_a_gente(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "")

    assert bot.pode_usar_o_bot(111) is True


def test_lista_de_permitidos_com_espacos_e_lida_na_mesma(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", " 111 , 222 ,")

    assert bot.ids_permitidos() == ["111", "222"]
    assert bot.pode_usar_o_bot(111) is True
    assert bot.pode_usar_o_bot(222) is True


def test_quem_nao_esta_na_lista_fica_de_fora(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")

    assert bot.pode_usar_o_bot(999) is False


def test_estranho_nao_chega_a_falar_com_a_ia(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")

    def nao_pode_ser_chamada(texto, timezone_utilizador, candidatas, nomes, nomes_receita):
        raise AssertionError("a ia nao devia ter sido chamada")

    monkeypatch.setattr(bot, "parse_mensagem", nao_pode_ser_chamada)
    update = FakeUpdate(texto="gastei 30 na fnac", telegram_user_id=999)

    correr(bot.mensagem(update, FakeContext()))

    assert update.message.respostas == [bot.TEXTO_BOT_PRIVADO]
    assert contar_despesas(bot_session) == 0


def test_estranho_nao_recebe_acesso_a_dashboard(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")
    update = FakeUpdate(texto="/dashboard", telegram_user_id=999)

    correr(bot.dashboard(update, FakeContext()))

    assert update.message.respostas == [bot.TEXTO_BOT_PRIVADO]
    assert "/login?code=" not in update.message.respostas[0]


def test_estranho_nao_pode_carregar_nos_botoes(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")
    despesa_id = criar_despesa(bot_session, telegram_user_id=111)
    update = FakeUpdate(dados="apagar:" + str(despesa_id), telegram_user_id=999)

    correr(bot.apagar(update, FakeContext()))

    assert update.callback_query.textos == [bot.TEXTO_BOT_PRIVADO]
    assert contar_despesas(bot_session) == 1


def test_dono_continua_a_passar_com_a_lista_ligada(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    correr(bot.mensagem(FakeUpdate(texto="gastei 10 no café"), FakeContext()))

    assert contar_despesas(bot_session) == 1


def test_quem_escreve_depressa_de_mais_e_travado(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "BOT_MAX_MESSAGES", 3)
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    for _ in range(3):
        correr(bot.mensagem(FakeUpdate(texto="gastei 10 no café"), FakeContext()))

    travado = FakeUpdate(texto="gastei 10 no café")
    correr(bot.mensagem(travado, FakeContext()))

    assert travado.message.respostas == [bot.TEXTO_DEMASIADAS_MENSAGENS]
    assert contar_despesas(bot_session) == 3


def test_limite_do_bot_nao_chega_a_gastar_dinheiro_na_ia(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "BOT_MAX_MESSAGES", 1)
    chamadas = []

    def contar_chamada(texto, timezone_utilizador, candidatas, nomes, nomes_receita):
        chamadas.append(texto)
        return resposta_ia(despesas=[despesa_ia()])

    monkeypatch.setattr(bot, "parse_mensagem", contar_chamada)

    for _ in range(5):
        correr(bot.mensagem(FakeUpdate(texto="gastei 10 no café"), FakeContext()))

    assert len(chamadas) == 1


def test_limite_do_bot_e_por_utilizador(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "BOT_MAX_MESSAGES", 1)
    fingir_ia(monkeypatch, resposta_ia(despesas=[despesa_ia()]))

    correr(bot.mensagem(FakeUpdate(texto="gastei 10", telegram_user_id=111), FakeContext()))
    do_outro = FakeUpdate(texto="gastei 20", telegram_user_id=222)
    correr(bot.mensagem(do_outro, FakeContext()))

    assert do_outro.message.respostas != [bot.TEXTO_DEMASIADAS_MENSAGENS]
    assert contar_despesas(bot_session) == 2


def test_comandos_tambem_contam_para_o_limite(bot_session, monkeypatch):
    monkeypatch.setattr(bot, "BOT_MAX_MESSAGES", 2)

    correr(bot.start(FakeUpdate(texto="/start"), FakeContext()))
    correr(bot.dashboard(FakeUpdate(texto="/dashboard"), FakeContext()))
    travado = FakeUpdate(texto="/dashboard")
    correr(bot.dashboard(travado, FakeContext()))

    assert travado.message.respostas == [bot.TEXTO_DEMASIADAS_MENSAGENS]


@pytest.fixture
def app_do_bot(monkeypatch):
    monkeypatch.setattr(bot, "TELEGRAM_BOT_TOKEN", "123:fake")
    return bot.montar_app()


def correr_handler(handler, telegram_user_id):
    if isinstance(handler, CallbackQueryHandler):
        update = FakeUpdate(dados="apagar:1", telegram_user_id=telegram_user_id)
    else:
        update = FakeUpdate(texto="olá", telegram_user_id=telegram_user_id)

    correr(handler.callback(update, FakeContext()))
    return update


def resposta_do_handler(update):
    if update.callback_query is not None:
        return update.callback_query.textos

    return update.message.respostas


def test_montar_app_sem_token(monkeypatch):
    monkeypatch.setattr(bot, "TELEGRAM_BOT_TOKEN", "")

    with pytest.raises(RuntimeError):
        bot.montar_app()


def test_todos_os_handlers_registados_travam_um_estranho(bot_session, app_do_bot, monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_TELEGRAM_IDS", "111")

    for handler in app_do_bot.handlers[0]:
        update = correr_handler(handler, 999)

        assert resposta_do_handler(update) == [bot.TEXTO_BOT_PRIVADO]


def test_todos_os_handlers_registados_respeitam_o_limite(bot_session, app_do_bot, monkeypatch):
    monkeypatch.setattr(bot, "BOT_MAX_MESSAGES", 0)

    for handler in app_do_bot.handlers[0]:
        update = correr_handler(handler, 111)

        assert resposta_do_handler(update) == [bot.TEXTO_DEMASIADAS_MENSAGENS]


def test_o_bot_tem_um_error_handler(app_do_bot):
    assert bot.erro_do_bot in app_do_bot.error_handlers
