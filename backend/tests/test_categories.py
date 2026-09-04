from sqlalchemy import select

from core.ai_parsing import montar_prompt, nome_de_recurso, normalizar_categoria
from core.categories import (
    apagar_categoria,
    categoria_de_recurso,
    criar_categoria,
    listar_categorias_com_totais,
    mesclar_categorias,
    procurar_por_nome,
    renomear_categoria,
)
from core.expenses import guardar_despesa, obter_ou_criar_utilizador
from core.models import Expense
from tests.test_ai_parsing import fazer_resposta
from tests.test_expenses import fazer_despesa


def preparar(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    guardar_despesa(session, 111, fazer_despesa(category="Tecnologia", amount_cents=3000))
    guardar_despesa(session, 111, fazer_despesa(category="Tecnologia", amount_cents=1000))
    guardar_despesa(session, 111, fazer_despesa(category="Lazer", amount_cents=500))
    return utilizador


def test_criar_categoria_nova(session):
    utilizador = preparar(session)

    categoria, erro = criar_categoria(session, utilizador.id, "Ginásio")

    assert erro is None
    assert categoria.name == "Ginásio"
    assert categoria.is_default is False
    assert categoria.user_id == utilizador.id


def test_nome_com_espacos_a_mais_fica_limpo(session):
    utilizador = preparar(session)

    categoria, erro = criar_categoria(session, utilizador.id, "  Compras   online  ")

    assert erro is None
    assert categoria.name == "Compras online"


def test_nao_cria_categoria_repetida_com_outra_capitalizacao(session):
    utilizador = preparar(session)

    categoria, erro = criar_categoria(session, utilizador.id, "lAZER")

    assert categoria is None
    assert erro is not None


def test_renomear_categoria(session):
    utilizador = preparar(session)
    lazer = procurar_por_nome(session, utilizador.id, "Lazer")

    categoria, erro = renomear_categoria(session, utilizador.id, lazer.id, "Saídas")

    assert erro is None
    assert categoria.name == "Saídas"
    assert procurar_por_nome(session, utilizador.id, "Lazer") is None


def test_renomear_mantem_as_despesas(session):
    utilizador = preparar(session)
    tecnologia = procurar_por_nome(session, utilizador.id, "Tecnologia")

    renomear_categoria(session, utilizador.id, tecnologia.id, "Gadgets")

    despesas = session.scalars(select(Expense).where(Expense.category_id == tecnologia.id)).all()
    assert len(despesas) == 2


def test_mesclar_move_as_despesas(session):
    utilizador = preparar(session)
    tecnologia = procurar_por_nome(session, utilizador.id, "Tecnologia")
    lazer = procurar_por_nome(session, utilizador.id, "Lazer")

    destino, erro = mesclar_categorias(session, utilizador.id, tecnologia.id, lazer.id)

    assert erro is None
    assert destino.id == lazer.id
    assert procurar_por_nome(session, utilizador.id, "Tecnologia") is None

    despesas = session.scalars(select(Expense).where(Expense.category_id == lazer.id)).all()
    assert len(despesas) == 3


def test_apagar_categoria_com_despesas_nao_deixa(session):
    utilizador = preparar(session)
    tecnologia = procurar_por_nome(session, utilizador.id, "Tecnologia")

    apagou, erro = apagar_categoria(session, utilizador.id, tecnologia.id)

    assert apagou is False
    assert erro is not None
    assert procurar_por_nome(session, utilizador.id, "Tecnologia") is not None


def test_apagar_categoria_vazia(session):
    utilizador = preparar(session)
    casa = procurar_por_nome(session, utilizador.id, "Casa")

    apagou, erro = apagar_categoria(session, utilizador.id, casa.id)

    assert apagou is True
    assert erro is None
    assert procurar_por_nome(session, utilizador.id, "Casa") is None


def test_totais_por_categoria(session):
    utilizador = preparar(session)

    totais = {}
    for categoria in listar_categorias_com_totais(session, utilizador.id):
        totais[categoria["name"]] = categoria

    assert totais["Tecnologia"]["count"] == 2
    assert totais["Tecnologia"]["total_cents"] == 4000
    assert totais["Casa"]["count"] == 0
    assert totais["Casa"]["total_cents"] == 0


def test_categoria_de_recurso_e_outros(session):
    utilizador = preparar(session)

    assert categoria_de_recurso(session, utilizador.id).name == "Outros"


def test_categoria_de_recurso_quando_outros_foi_renomeada(session):
    utilizador = preparar(session)
    outros = procurar_por_nome(session, utilizador.id, "Outros")
    renomear_categoria(session, utilizador.id, outros.id, "Diversos")

    recurso = categoria_de_recurso(session, utilizador.id)

    assert recurso.name == "Alimentação"


def test_despesa_com_categoria_criada_pelo_utilizador(session):
    utilizador = preparar(session)
    criar_categoria(session, utilizador.id, "Ginásio")

    despesa = guardar_despesa(session, 111, fazer_despesa(category="Ginásio"))

    ginasio = procurar_por_nome(session, utilizador.id, "Ginásio")
    assert despesa.category_id == ginasio.id


def linha_das_categorias(prompt):
    for linha in prompt.splitlines():
        if linha.startswith("Categorias válidas"):
            return linha

    return ""


def test_prompt_leva_as_categorias_do_utilizador():
    prompt = montar_prompt("Europe/Lisbon", None, ["Alimentação", "Ginásio", "Outros"])
    linha = linha_das_categorias(prompt)

    assert "Ginásio" in linha
    assert "Tecnologia" not in linha


def test_prompt_sem_lista_usa_as_categorias_por_defeito():
    linha = linha_das_categorias(montar_prompt("Europe/Lisbon", None))

    assert "Tecnologia" in linha


def test_categoria_fora_da_lista_do_utilizador_vai_para_a_de_recurso():
    resultado = normalizar_categoria(
        fazer_resposta(category="Tecnologia"), ["Alimentação", "Ginásio", "Outros"]
    )

    assert resultado.despesas[0].category == "Outros"


def test_nome_de_recurso_sem_outros():
    assert nome_de_recurso(["Alimentação", "Ginásio"]) == "Alimentação"


def test_categoria_de_recurso_cria_a_outros_quando_nao_ha_nenhuma(session):
    categoria = categoria_de_recurso(session, 999)

    assert categoria.name == "Outros"
    assert categoria.user_id == 999
    assert categoria.id is not None


def test_criar_categoria_com_tipo_invalido(session):
    utilizador = preparar(session)

    categoria, erro = criar_categoria(session, utilizador.id, "Poupança", "poupanca")

    assert categoria is None
    assert erro == "Tipo invalido"


def test_renomear_para_um_nome_vazio(session):
    utilizador = preparar(session)
    lazer = procurar_por_nome(session, utilizador.id, "Lazer")

    categoria, erro = renomear_categoria(session, utilizador.id, lazer.id, "   ")

    assert categoria is None
    assert erro == "Escreve um nome entre 1 e 100 caracteres"
    assert procurar_por_nome(session, utilizador.id, "Lazer") is not None


def test_mesclar_a_partir_de_uma_categoria_que_nao_existe(session):
    utilizador = preparar(session)
    casa = procurar_por_nome(session, utilizador.id, "Casa")

    categoria, erro = mesclar_categorias(session, utilizador.id, 9999, casa.id)

    assert categoria is None
    assert erro == "Categoria nao encontrada"
