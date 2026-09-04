from bot.main import (
    TEXTO_ACESSO,
    resumo_despesa,
    teclado_apagar,
    teclado_categorias,
    teclado_confirmar_apagar,
    teclado_editar,
)
from core.ai_parsing import CATEGORIAS


def test_teclado_tem_botao_apagar():
    teclado = teclado_apagar(7)
    botao = teclado.inline_keyboard[0][0]
    assert botao.text == "Apagar"
    assert botao.callback_data == "apagar:7"


def test_teclado_so_tem_um_botao():
    teclado = teclado_apagar(1)
    assert len(teclado.inline_keyboard) == 1
    assert len(teclado.inline_keyboard[0]) == 1


def test_teclado_editar_tem_os_campos():
    dados = []
    for linha in teclado_editar().inline_keyboard:
        for botao in linha:
            dados.append(botao.callback_data)

    assert dados == [
        "editar:valor",
        "editar:categoria",
        "editar:comerciante",
        "editar:data",
        "editar:cancelar",
    ]


def test_teclado_categorias_tem_todas_as_categorias():
    nomes = []
    for linha in teclado_categorias().inline_keyboard:
        for botao in linha:
            if botao.callback_data.startswith("categoria:"):
                nomes.append(botao.text)

    assert nomes == CATEGORIAS


def test_teclado_categorias_tem_cancelar():
    ultima_linha = teclado_categorias().inline_keyboard[-1]
    assert ultima_linha[0].callback_data == "editar:cancelar"


def test_resumo_despesa():
    despesa = {
        "id": 1,
        "amount_cents": 3550,
        "currency": "EUR",
        "category": "Tecnologia",
        "merchant": "Fnac",
        "date": "2026-09-03",
    }
    assert resumo_despesa(despesa) == "35.50 EUR · Fnac · Tecnologia · 2026-09-03"


def test_resumo_despesa_sem_comerciante():
    despesa = {
        "id": 1,
        "amount_cents": 500,
        "currency": "EUR",
        "category": "Alimentação",
        "merchant": None,
        "date": "2026-09-03",
    }
    assert resumo_despesa(despesa) == "5.00 EUR · Alimentação · 2026-09-03"


def test_teclado_confirmar_apagar():
    linha = teclado_confirmar_apagar(7).inline_keyboard[0]

    assert linha[0].text == "Sim, apagar"
    assert linha[0].callback_data == "confirmar:7"
    assert linha[1].text == "Cancelar"
    assert linha[1].callback_data == "confirmar:nao"


def test_teclado_confirmar_apagar_so_tem_uma_linha():
    assert len(teclado_confirmar_apagar(1).inline_keyboard) == 1


def test_texto_de_acesso_tem_link_e_codigo():
    texto = TEXTO_ACESSO.format(link="http://localhost:3000/login?code=123456", codigo="123456")

    assert "http://localhost:3000/login?code=123456" in texto
    assert "123456" in texto
