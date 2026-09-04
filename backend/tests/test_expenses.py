from datetime import date

from sqlalchemy import select

from core.ai_parsing import (
    CATEGORIAS,
    CATEGORIAS_RECEITA,
    DespesaDaIA,
    DespesaNova,
    RespostaIA,
    campos_da_correcao,
    construir_despesas_novas,
)
from core.categories import garantir_categorias_do_utilizador
from core.expenses import (
    apagar_despesa,
    atualizar_despesa,
    converter_data_escrita,
    converter_valor_para_centimos,
    guardar_despesa,
    obter_despesas_por_ids,
    obter_ou_criar_categoria,
    obter_ou_criar_utilizador,
    obter_timezone,
    obter_ultima_despesa,
)
from core.models import Category, Expense, User


def fazer_despesa(**campos):
    base = {
        "kind": "expense",
        "amount_cents": 3000,
        "currency": "EUR",
        "category": "Tecnologia",
        "subcategory": None,
        "merchant": "Fnac",
        "description": None,
        "expense_date": date(2026, 9, 3),
        "payment_method": None,
        "confidence": 0.98,
        "needs_confirmation": False,
    }
    base.update(campos)
    return DespesaNova(**base)


def test_cria_utilizador_novo(session):
    utilizador = obter_ou_criar_utilizador(session, 12345, "Filipe")
    assert utilizador.id is not None
    assert utilizador.telegram_user_id == 12345
    assert utilizador.timezone == "Europe/Lisbon"
    assert utilizador.currency_default == "EUR"


def test_nao_duplica_utilizador(session):
    primeiro = obter_ou_criar_utilizador(session, 12345, "Filipe")
    segundo = obter_ou_criar_utilizador(session, 12345, "Filipe")
    assert primeiro.id == segundo.id
    assert len(session.scalars(select(User)).all()) == 1


def nomes_das_categorias(session, tipo):
    consulta = select(Category).where(Category.kind == tipo)
    return sorted(c.name for c in session.scalars(consulta).all())


def test_utilizador_novo_fica_com_as_categorias_por_defeito(session):
    utilizador = obter_ou_criar_utilizador(session, 12345)

    assert nomes_das_categorias(session, "expense") == sorted(CATEGORIAS)
    assert nomes_das_categorias(session, "income") == sorted(CATEGORIAS_RECEITA)
    for categoria in session.scalars(select(Category)).all():
        assert categoria.user_id == utilizador.id


def test_categorias_por_defeito_nao_duplicam(session):
    utilizador = obter_ou_criar_utilizador(session, 12345)
    garantir_categorias_do_utilizador(session, utilizador.id)

    assert nomes_das_categorias(session, "expense") == sorted(CATEGORIAS)
    assert nomes_das_categorias(session, "income") == sorted(CATEGORIAS_RECEITA)


def test_cada_utilizador_tem_as_suas_categorias(session):
    primeiro = obter_ou_criar_utilizador(session, 111)
    segundo = obter_ou_criar_utilizador(session, 222)

    categorias = session.scalars(select(Category)).all()
    por_utilizador = len(CATEGORIAS) + len(CATEGORIAS_RECEITA)
    assert len(categorias) == por_utilizador * 2

    do_primeiro = [c for c in categorias if c.user_id == primeiro.id]
    do_segundo = [c for c in categorias if c.user_id == segundo.id]
    assert len(do_primeiro) == por_utilizador
    assert len(do_segundo) == por_utilizador


def test_nao_duplica_categoria(session):
    utilizador = obter_ou_criar_utilizador(session, 12345)
    primeira = obter_ou_criar_categoria(session, utilizador.id, "Lazer")
    segunda = obter_ou_criar_categoria(session, utilizador.id, "Lazer")
    assert primeira.id == segunda.id


def test_guardar_despesa(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac", "Filipe")

    assert despesa.id is not None
    assert despesa.amount_cents == 3000
    assert despesa.currency == "EUR"
    assert despesa.merchant == "Fnac"
    assert despesa.expense_date == date(2026, 9, 3)
    assert despesa.raw_message == "gastei 30 na fnac"
    assert despesa.ai_confidence == 0.98
    assert despesa.created_at is not None

    categoria = session.get(Category, despesa.category_id)
    assert categoria.name == "Tecnologia"

    utilizador = session.get(User, despesa.user_id)
    assert utilizador.telegram_user_id == 12345


def test_despesas_de_utilizadores_diferentes(session):
    guardar_despesa(session, 111, fazer_despesa(), "gastei 30 na fnac")
    guardar_despesa(session, 222, fazer_despesa(amount_cents=500), "gastei 5 no cafe")

    despesas = session.scalars(select(Expense)).all()
    assert len(despesas) == 2
    assert despesas[0].user_id != despesas[1].user_id


def test_categoria_fora_da_lista_vai_para_outros(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(category="Ginásio"))
    categoria = session.get(Category, despesa.category_id)
    assert categoria.name == "Outros"


def test_categoria_fora_da_lista_nao_cria_registo_novo(session):
    guardar_despesa(session, 12345, fazer_despesa(category="Ginásio"))
    assert nomes_das_categorias(session, "expense") == sorted(CATEGORIAS)


def test_categorias_por_defeito_ficam_marcadas_como_padrao(session):
    obter_ou_criar_utilizador(session, 12345)
    for categoria in session.scalars(select(Category)).all():
        assert categoria.is_default is True


def test_outros_e_criada_mesmo_sem_seed(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(category="Ginásio"))
    assert session.get(Category, despesa.category_id).name == "Outros"


def test_apagar_despesa(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")

    assert apagar_despesa(session, despesa.id, 12345) is True
    assert session.scalars(select(Expense)).all() == []


def test_apagar_despesa_que_nao_existe(session):
    obter_ou_criar_utilizador(session, 12345)
    assert apagar_despesa(session, 999, 12345) is False


def test_nao_apaga_despesa_de_outro_utilizador(session):
    despesa = guardar_despesa(session, 111, fazer_despesa(), "gastei 30 na fnac")
    obter_ou_criar_utilizador(session, 222)

    assert apagar_despesa(session, despesa.id, 222) is False
    assert len(session.scalars(select(Expense)).all()) == 1


def test_apagar_com_utilizador_desconhecido(session):
    despesa = guardar_despesa(session, 111, fazer_despesa(), "gastei 30 na fnac")
    assert apagar_despesa(session, despesa.id, 999999) is False


def test_ultima_despesa_sem_utilizador(session):
    assert obter_ultima_despesa(session, 12345) is None


def test_ultima_despesa_sem_despesas(session):
    obter_ou_criar_utilizador(session, 12345)
    assert obter_ultima_despesa(session, 12345) is None


def test_ultima_despesa_e_a_mais_recente(session):
    guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")
    guardar_despesa(session, 12345, fazer_despesa(amount_cents=500, merchant="Café"), "cafe")

    ultima = obter_ultima_despesa(session, 12345)
    assert ultima["amount_cents"] == 500
    assert ultima["merchant"] == "Café"
    assert ultima["currency"] == "EUR"
    assert ultima["category"] == "Tecnologia"
    assert ultima["date"] == "2026-09-03"


def test_ultima_despesa_nao_mistura_utilizadores(session):
    guardar_despesa(session, 111, fazer_despesa(merchant="Fnac"), "fnac")
    guardar_despesa(session, 222, fazer_despesa(merchant="Continente"), "continente")

    assert obter_ultima_despesa(session, 111)["merchant"] == "Fnac"
    assert obter_ultima_despesa(session, 222)["merchant"] == "Continente"


def test_atualizar_despesa_muda_so_os_campos_dados(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")

    atualizada = atualizar_despesa(
        session, despesa.id, 12345, {"merchant": "Continente", "category": "Alimentação"}
    )

    assert atualizada.id == despesa.id
    assert atualizada.merchant == "Continente"
    assert atualizada.amount_cents == 3000
    assert atualizada.expense_date == date(2026, 9, 3)

    categoria = session.get(Category, atualizada.category_id)
    assert categoria.name == "Alimentação"


def test_atualizar_despesa_com_valor_e_data(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")

    atualizada = atualizar_despesa(
        session, despesa.id, 12345, {"amount_cents": 3500, "expense_date": date(2026, 9, 1)}
    )

    assert atualizada.amount_cents == 3500
    assert atualizada.expense_date == date(2026, 9, 1)


def test_atualizar_sem_campos_nao_muda_nada(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")
    atualizada = atualizar_despesa(session, despesa.id, 12345, {})
    assert atualizada.amount_cents == 3000
    assert atualizada.merchant == "Fnac"


def test_nao_atualiza_despesa_de_outro_utilizador(session):
    despesa = guardar_despesa(session, 111, fazer_despesa(), "gastei 30 na fnac")
    obter_ou_criar_utilizador(session, 222)

    assert atualizar_despesa(session, despesa.id, 222, {"merchant": "Continente"}) is None
    assert session.get(Expense, despesa.id).merchant == "Fnac"


def test_atualizar_despesa_que_nao_existe(session):
    obter_ou_criar_utilizador(session, 12345)
    assert atualizar_despesa(session, 999, 12345, {"merchant": "Continente"}) is None


def fazer_correcao(**campos):
    base = {
        "kind": "expense",
        "amount_cents": None,
        "currency": None,
        "category": None,
        "subcategory": None,
        "merchant": None,
        "description": None,
        "date": None,
        "payment_method": None,
        "confidence": 0.9,
        "needs_confirmation": False,
    }
    base.update(campos)

    return RespostaIA(
        e_despesa=True,
        e_correcao=True,
        despesas=[DespesaDaIA(**base)],
        resposta="Corrigido!",
    )


def fazer_mensagem_com_varias(*valores):
    despesas = []
    for valor, comerciante in valores:
        despesas.append(
            DespesaDaIA(
                kind="expense",
                amount_cents=valor,
                currency="EUR",
                category="Alimentação",
                subcategory=None,
                merchant=comerciante,
                description=None,
                date="2026-09-03",
                payment_method=None,
                confidence=0.9,
                needs_confirmation=False,
            )
        )

    return RespostaIA(
        e_despesa=True, e_correcao=False, despesas=despesas, resposta="Anotado as duas!"
    )


def test_guardar_varias_despesas_da_mesma_mensagem(session):
    texto = "gastei 10 no café e 20 no almoço"
    resultado = fazer_mensagem_com_varias((1000, "Café"), (2000, "Tasca"))

    for despesa in construir_despesas_novas(resultado, "Europe/Lisbon"):
        guardar_despesa(session, 12345, despesa, texto)

    despesas = session.scalars(select(Expense).order_by(Expense.id)).all()

    assert len(despesas) == 2
    assert despesas[0].amount_cents == 1000
    assert despesas[0].merchant == "Café"
    assert despesas[1].amount_cents == 2000
    assert despesas[1].merchant == "Tasca"
    assert despesas[0].raw_message == texto
    assert despesas[1].raw_message == texto


def test_obter_despesas_por_ids(session):
    resultado = fazer_mensagem_com_varias((1000, "Café"), (2000, "Tasca"))
    ids = []
    for despesa in construir_despesas_novas(resultado, "Europe/Lisbon"):
        ids.append(guardar_despesa(session, 12345, despesa, "duas de uma vez").id)

    resumos = obter_despesas_por_ids(session, 12345, ids)

    assert len(resumos) == 2
    assert resumos[0]["amount_cents"] == 1000
    assert resumos[0]["merchant"] == "Café"
    assert resumos[1]["amount_cents"] == 2000
    assert resumos[0]["category"] == "Alimentação"


def test_obter_despesas_por_ids_ignora_as_que_ja_nao_existem(session):
    despesa = guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")

    resumos = obter_despesas_por_ids(session, 12345, [despesa.id, 9999])

    assert len(resumos) == 1
    assert resumos[0]["id"] == despesa.id


def test_obter_despesas_por_ids_nao_traz_de_outro_utilizador(session):
    do_outro = guardar_despesa(session, 999, fazer_despesa(), "gastei 30 na fnac")

    assert obter_despesas_por_ids(session, 12345, [do_outro.id]) == []
    assert obter_despesas_por_ids(session, 12345, []) == []


def test_correcao_depois_de_varias_apanha_a_ultima(session):
    resultado = fazer_mensagem_com_varias((1000, "Café"), (2000, "Tasca"))
    for despesa in construir_despesas_novas(resultado, "Europe/Lisbon"):
        guardar_despesa(session, 12345, despesa, "gastei 10 no café e 20 no almoço")

    ultima = obter_ultima_despesa(session, 12345)

    assert ultima["amount_cents"] == 2000
    assert ultima["merchant"] == "Tasca"


def test_correcao_por_texto_atualiza_a_ultima_despesa(session):
    guardar_despesa(session, 12345, fazer_despesa(), "gastei 30 na fnac")

    ultima = obter_ultima_despesa(session, 12345)
    resultado = fazer_correcao(merchant="Continente", category="Alimentação")
    atualizada = atualizar_despesa(session, ultima["id"], 12345, campos_da_correcao(resultado))

    assert len(session.scalars(select(Expense)).all()) == 1
    assert atualizada.merchant == "Continente"
    assert atualizada.amount_cents == 3000
    assert session.get(Category, atualizada.category_id).name == "Alimentação"


def test_converter_valor_para_centimos():
    assert converter_valor_para_centimos("35") == 3500
    assert converter_valor_para_centimos("35,50") == 3550
    assert converter_valor_para_centimos("35.50") == 3550
    assert converter_valor_para_centimos(" 35,50 € ") == 3550
    assert converter_valor_para_centimos("12 euros") == 1200
    assert converter_valor_para_centimos("0,05") == 5


def test_converter_valor_invalido():
    assert converter_valor_para_centimos("muito dinheiro") is None
    assert converter_valor_para_centimos("") is None
    assert converter_valor_para_centimos("0") is None
    assert converter_valor_para_centimos("-10") is None


def test_converter_data_escrita():
    assert converter_data_escrita("01/09/2026") == date(2026, 9, 1)
    assert converter_data_escrita("01-09-2026") == date(2026, 9, 1)
    assert converter_data_escrita("2026-09-01") == date(2026, 9, 1)
    assert converter_data_escrita(" 01/09/26 ") == date(2026, 9, 1)


def test_converter_data_invalida():
    assert converter_data_escrita("ontem") is None
    assert converter_data_escrita("32/09/2026") is None
    assert converter_data_escrita("") is None


def test_timezone_por_defeito_sem_utilizador(session):
    assert obter_timezone(session, 12345) == "Europe/Lisbon"


def test_timezone_do_utilizador(session):
    utilizador = obter_ou_criar_utilizador(session, 12345)
    utilizador.timezone = "Pacific/Auckland"
    session.commit()

    assert obter_timezone(session, 12345) == "Pacific/Auckland"
