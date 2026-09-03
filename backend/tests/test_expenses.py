from datetime import date

from sqlalchemy import select

from core.ai_parsing import CATEGORIAS, DespesaNova, RespostaIA, campos_da_correcao
from core.expenses import (
    apagar_despesa,
    atualizar_despesa,
    converter_data_escrita,
    converter_valor_para_centimos,
    garantir_categorias_por_defeito,
    guardar_despesa,
    obter_ou_criar_categoria,
    obter_ou_criar_utilizador,
    obter_timezone,
    obter_ultima_despesa,
)
from core.models import Category, Expense, User


def fazer_despesa(**campos):
    base = {
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


def test_categorias_por_defeito(session):
    garantir_categorias_por_defeito(session)
    garantir_categorias_por_defeito(session)
    nomes = [c.name for c in session.scalars(select(Category)).all()]
    assert sorted(nomes) == sorted(CATEGORIAS)


def test_nao_duplica_categoria(session):
    primeira = obter_ou_criar_categoria(session, "Lazer")
    segunda = obter_ou_criar_categoria(session, "Lazer")
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
    garantir_categorias_por_defeito(session)
    despesa = guardar_despesa(session, 12345, fazer_despesa(category="Ginásio"))
    categoria = session.get(Category, despesa.category_id)
    assert categoria.name == "Outros"


def test_categoria_fora_da_lista_nao_cria_registo_novo(session):
    garantir_categorias_por_defeito(session)
    guardar_despesa(session, 12345, fazer_despesa(category="Ginásio"))
    nomes = [c.name for c in session.scalars(select(Category)).all()]
    assert sorted(nomes) == sorted(CATEGORIAS)


def test_categorias_por_defeito_ficam_marcadas_como_padrao(session):
    garantir_categorias_por_defeito(session)
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
        "e_despesa": True,
        "e_correcao": True,
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
        "resposta": "Corrigido!",
    }
    base.update(campos)
    return RespostaIA(**base)


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
