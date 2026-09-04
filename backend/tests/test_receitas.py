from datetime import date

from sqlalchemy import select

from core.ai_parsing import (
    CATEGORIAS_RECEITA,
    construir_despesas_novas,
    montar_prompt,
    normalizar_categoria,
)
from core.categories import (
    TIPO_DESPESA,
    TIPO_RECEITA,
    criar_categoria,
    listar_categorias_com_totais,
    mesclar_categorias,
    procurar_por_nome,
)
from core.expenses import guardar_despesa, obter_ou_criar_utilizador, obter_ultima_despesa
from core.models import Expense
from core.queries import listar_categorias, listar_despesas, resumo_do_mes, somar_despesas
from tests.test_ai_parsing import fazer_despesa_da_ia, fazer_resposta
from tests.test_expenses import fazer_despesa


def preparar(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    guardar_despesa(
        session,
        111,
        fazer_despesa(amount_cents=3000, category="Tecnologia", expense_date=date(2026, 9, 2)),
    )
    guardar_despesa(
        session,
        111,
        fazer_despesa(amount_cents=1250, category="Alimentação", expense_date=date(2026, 9, 10)),
    )
    guardar_despesa(
        session,
        111,
        fazer_despesa(
            kind=TIPO_RECEITA,
            amount_cents=120000,
            category="Salário",
            merchant=None,
            expense_date=date(2026, 9, 1),
        ),
    )

    return utilizador


def test_utilizador_novo_tem_categorias_de_receita(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    nomes = listar_categorias(session, utilizador.id, TIPO_RECEITA)

    assert sorted(nomes) == sorted(CATEGORIAS_RECEITA)


def test_categorias_de_despesa_e_receita_nao_se_misturam(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    de_despesa = listar_categorias(session, utilizador.id, TIPO_DESPESA)
    de_receita = listar_categorias(session, utilizador.id, TIPO_RECEITA)

    assert "Alimentação" in de_despesa
    assert "Alimentação" not in de_receita
    assert "Salário" in de_receita
    assert "Salário" not in de_despesa


def test_outros_existe_nos_dois_tipos(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    de_despesa = procurar_por_nome(session, utilizador.id, "Outros", TIPO_DESPESA)
    de_receita = procurar_por_nome(session, utilizador.id, "Outros", TIPO_RECEITA)

    assert de_despesa is not None
    assert de_receita is not None
    assert de_despesa.id != de_receita.id


def test_pode_criar_categorias_com_o_mesmo_nome_em_tipos_diferentes(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    primeira, erro_uma = criar_categoria(session, utilizador.id, "Extras", TIPO_DESPESA)
    segunda, erro_outra = criar_categoria(session, utilizador.id, "Extras", TIPO_RECEITA)

    assert erro_uma is None
    assert erro_outra is None
    assert primeira.id != segunda.id


def test_nao_mescla_categorias_de_tipos_diferentes(session):
    utilizador = preparar(session)
    despesa = procurar_por_nome(session, utilizador.id, "Tecnologia", TIPO_DESPESA)
    receita = procurar_por_nome(session, utilizador.id, "Salário", TIPO_RECEITA)

    destino, erro = mesclar_categorias(session, utilizador.id, despesa.id, receita.id)

    assert destino is None
    assert erro is not None


def test_guardar_receita_usa_a_categoria_de_receita(session):
    utilizador = preparar(session)
    salario = procurar_por_nome(session, utilizador.id, "Salário", TIPO_RECEITA)

    receita = session.scalar(select(Expense).where(Expense.kind == TIPO_RECEITA))

    assert receita.amount_cents == 120000
    assert receita.category_id == salario.id
    assert utilizador.id == receita.user_id


def test_receita_com_categoria_de_despesa_cai_na_de_recurso(session):
    utilizador = preparar(session)

    guardada = guardar_despesa(
        session, 111, fazer_despesa(kind=TIPO_RECEITA, amount_cents=5000, category="Alimentação")
    )

    recurso = procurar_por_nome(session, utilizador.id, "Outros", TIPO_RECEITA)
    assert guardada.category_id == recurso.id


def test_somar_separa_despesas_de_receitas(session):
    utilizador = preparar(session)

    despesas = somar_despesas(session, utilizador.id, {"tipo": TIPO_DESPESA})
    receitas = somar_despesas(session, utilizador.id, {"tipo": TIPO_RECEITA})
    tudo = somar_despesas(session, utilizador.id, {})

    assert despesas == 4250
    assert receitas == 120000
    assert tudo == 124250


def test_listar_despesas_filtra_por_tipo(session):
    utilizador = preparar(session)

    so_receitas = listar_despesas(session, utilizador.id, {"tipo": TIPO_RECEITA})
    tudo = listar_despesas(session, utilizador.id, {})

    assert len(so_receitas) == 1
    assert so_receitas[0]["kind"] == TIPO_RECEITA
    assert len(tudo) == 3


def test_resumo_do_mes_traz_saldo(session):
    utilizador = preparar(session)

    resumo = resumo_do_mes(session, utilizador.id, "2026-09")

    assert resumo["total_cents"] == 4250
    assert resumo["count"] == 2
    assert resumo["income_cents"] == 120000
    assert resumo["income_count"] == 1
    assert resumo["balance_cents"] == 115750


def test_resumo_por_categoria_nao_mistura_receitas(session):
    utilizador = preparar(session)

    resumo = resumo_do_mes(session, utilizador.id, "2026-09")

    nomes = [linha["category"] for linha in resumo["by_category"]]
    nomes_receita = [linha["category"] for linha in resumo["income_by_category"]]

    assert "Salário" not in nomes
    assert nomes_receita == ["Salário"]


def test_totais_da_pagina_de_categorias_contam_as_receitas(session):
    utilizador = preparar(session)

    totais = {}
    for categoria in listar_categorias_com_totais(session, utilizador.id):
        totais[(categoria["name"], categoria["kind"])] = categoria

    assert totais[("Salário", TIPO_RECEITA)]["total_cents"] == 120000
    assert totais[("Tecnologia", TIPO_DESPESA)]["total_cents"] == 3000


def test_ultima_despesa_mostra_o_tipo(session):
    preparar(session)

    ultima = obter_ultima_despesa(session, 111)

    assert ultima["kind"] == TIPO_RECEITA


def test_prompt_tem_as_duas_listas_de_categorias():
    prompt = montar_prompt("Europe/Lisbon", None, ["Alimentação", "Outros"], ["Salário", "Outros"])

    assert "Categorias válidas para despesas" in prompt
    assert "Categorias válidas para receitas" in prompt
    assert "Salário" in prompt
    assert "income" in prompt


def test_categoria_de_receita_invalida_vai_para_a_de_recurso_de_receita():
    resultado = normalizar_categoria(
        fazer_resposta(despesas=[fazer_despesa_da_ia(kind=TIPO_RECEITA, category="Alimentação")]),
        ["Alimentação", "Outros"],
        ["Salário", "Outros"],
    )

    assert resultado.despesas[0].category == "Outros"


def test_kind_invalido_da_ia_vira_despesa():
    resultado = normalizar_categoria(fazer_resposta(kind="qualquer coisa"))

    assert resultado.despesas[0].kind == TIPO_DESPESA


def test_construir_mistura_de_despesa_e_receita():
    resultado = fazer_resposta(
        despesas=[
            fazer_despesa_da_ia(amount_cents=3000, category="Tecnologia"),
            fazer_despesa_da_ia(kind=TIPO_RECEITA, amount_cents=120000, category="Salário"),
        ]
    )

    novas = construir_despesas_novas(resultado)

    assert novas[0].kind == TIPO_DESPESA
    assert novas[1].kind == TIPO_RECEITA
    assert novas[1].amount_cents == 120000
