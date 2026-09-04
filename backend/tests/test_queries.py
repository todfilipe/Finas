from datetime import date

from core.expenses import guardar_despesa
from core.queries import (
    contar_despesas,
    listar_categorias,
    listar_despesas,
    mes_anterior,
    obter_utilizador_por_telegram,
    primeiro_dia_do_mes,
    resumo_do_mes,
    somar_despesas,
    totais_por_categoria,
    totais_por_comerciante,
    totais_por_mes,
    ultimo_dia_do_mes,
    ultimos_meses,
)
from tests.test_expenses import fazer_despesa


def preparar_dados(session):
    guardar_despesa(
        session,
        111,
        fazer_despesa(
            amount_cents=3000,
            category="Tecnologia",
            merchant="Fnac",
            expense_date=date(2026, 9, 2),
        ),
        raw_message="gastei 30 euros na fnac",
    )
    guardar_despesa(
        session,
        111,
        fazer_despesa(
            amount_cents=1250,
            category="Alimentação",
            merchant="Pingo Doce",
            description="almoço",
            expense_date=date(2026, 9, 10),
        ),
    )
    guardar_despesa(
        session,
        111,
        fazer_despesa(
            amount_cents=500,
            category="Alimentação",
            merchant="Cafe Central",
            expense_date=date(2026, 8, 20),
        ),
    )
    guardar_despesa(
        session,
        222,
        fazer_despesa(amount_cents=9999, merchant="Outro", expense_date=date(2026, 9, 5)),
    )

    return obter_utilizador_por_telegram(session, 111)


def test_primeiro_e_ultimo_dia_do_mes():
    assert primeiro_dia_do_mes("2026-09") == date(2026, 9, 1)
    assert ultimo_dia_do_mes("2026-09") == date(2026, 9, 30)
    assert ultimo_dia_do_mes("2026-02") == date(2026, 2, 28)
    assert ultimo_dia_do_mes("2026-12") == date(2026, 12, 31)


def test_mes_anterior():
    assert mes_anterior("2026-09") == "2026-08"
    assert mes_anterior("2026-01") == "2025-12"


def test_ultimos_meses():
    assert ultimos_meses("2026-02", 3) == ["2025-12", "2026-01", "2026-02"]


def test_lista_so_as_despesas_do_utilizador(session):
    utilizador = preparar_dados(session)

    despesas = listar_despesas(session, utilizador.id, {})

    assert len(despesas) == 3
    assert despesas[0]["expense_date"] == date(2026, 9, 10)
    assert despesas[0]["category"] == "Alimentação"


def test_filtra_por_periodo(session):
    utilizador = preparar_dados(session)

    filtros = {"data_inicio": date(2026, 9, 1), "data_fim": date(2026, 9, 30)}

    assert contar_despesas(session, utilizador.id, filtros) == 2
    assert somar_despesas(session, utilizador.id, filtros) == 4250


def test_filtra_por_categoria(session):
    utilizador = preparar_dados(session)

    despesas = listar_despesas(session, utilizador.id, {"categoria": "Alimentação"})

    assert len(despesas) == 2


def test_filtra_por_comerciante(session):
    utilizador = preparar_dados(session)

    despesas = listar_despesas(session, utilizador.id, {"comerciante": "fnac"})

    assert len(despesas) == 1
    assert despesas[0]["merchant"] == "Fnac"


def test_filtra_por_texto_livre(session):
    utilizador = preparar_dados(session)

    assert len(listar_despesas(session, utilizador.id, {"texto": "almoço"})) == 1
    assert len(listar_despesas(session, utilizador.id, {"texto": "euros na fnac"})) == 1


def test_filtra_por_intervalo_de_valores(session):
    utilizador = preparar_dados(session)

    filtros = {"valor_min": 1000, "valor_max": 5000}

    assert contar_despesas(session, utilizador.id, filtros) == 2


def test_limite_e_salto(session):
    utilizador = preparar_dados(session)

    pagina = listar_despesas(session, utilizador.id, {}, 1, 1)

    assert len(pagina) == 1
    assert pagina[0]["expense_date"] == date(2026, 9, 2)


def test_totais_por_categoria(session):
    utilizador = preparar_dados(session)

    totais = totais_por_categoria(session, utilizador.id, date(2026, 9, 1), date(2026, 9, 30))

    assert totais[0]["category"] == "Tecnologia"
    assert totais[0]["total_cents"] == 3000
    assert totais[1]["category"] == "Alimentação"
    assert totais[1]["count"] == 1


def test_totais_por_comerciante(session):
    utilizador = preparar_dados(session)

    totais = totais_por_comerciante(session, utilizador.id, date(2026, 8, 1), date(2026, 9, 30))

    assert totais[0]["merchant"] == "Fnac"
    assert len(totais) == 3


def test_totais_por_mes(session):
    utilizador = preparar_dados(session)

    totais = totais_por_mes(session, utilizador.id, "2026-09", 3)

    assert totais == [
        {"month": "2026-07", "total_cents": 0},
        {"month": "2026-08", "total_cents": 500},
        {"month": "2026-09", "total_cents": 4250},
    ]


def test_resumo_do_mes(session):
    utilizador = preparar_dados(session)

    resumo = resumo_do_mes(session, utilizador.id, "2026-09")

    assert resumo["month"] == "2026-09"
    assert resumo["total_cents"] == 4250
    assert resumo["count"] == 2
    assert resumo["previous_month"] == "2026-08"
    assert resumo["previous_total_cents"] == 500
    assert len(resumo["by_category"]) == 2


def test_lista_categorias(session):
    utilizador = preparar_dados(session)

    categorias = listar_categorias(session, utilizador.id)

    assert "Alimentação" in categorias
    assert categorias == sorted(categorias)
