import pytest
from fastapi.testclient import TestClient

from api.main import app, pedidos_de_login
from core.auth import criar_codigo_de_acesso
from core.db import get_session
from core.queries import obter_utilizador_por_telegram
from tests.test_queries import preparar_dados


@pytest.fixture
def cliente(session):
    preparar_dados(session)
    pedidos_de_login.clear()

    def sessao_de_teste():
        yield session

    app.dependency_overrides[get_session] = sessao_de_teste
    yield TestClient(app)
    app.dependency_overrides.clear()


def entrar(cliente, session, telegram_user_id=111):
    utilizador = obter_utilizador_por_telegram(session, telegram_user_id)
    codigo = criar_codigo_de_acesso(session, utilizador.id)
    resposta = cliente.post("/auth/verify", json={"code": codigo})
    assert resposta.status_code == 200
    return resposta


def test_health(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_sem_sessao_nao_deixa_ver_despesas(cliente):
    resposta = cliente.get("/expenses")

    assert resposta.status_code == 401


def test_codigo_errado(cliente):
    resposta = cliente.post("/auth/verify", json={"code": "000000"})

    assert resposta.status_code == 401


def test_login_com_codigo_valido(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/auth/me")

    assert resposta.status_code == 200
    assert resposta.json()["timezone"] == "Europe/Lisbon"


def test_codigo_nao_serve_duas_vezes(cliente, session):
    utilizador = obter_utilizador_por_telegram(session, 111)
    codigo = criar_codigo_de_acesso(session, utilizador.id)

    assert cliente.post("/auth/verify", json={"code": codigo}).status_code == 200
    assert cliente.post("/auth/verify", json={"code": codigo}).status_code == 401


def test_logout(cliente, session):
    entrar(cliente, session)

    cliente.post("/auth/logout")

    assert cliente.get("/auth/me").status_code == 401


def test_demasiadas_tentativas(cliente):
    for _ in range(10):
        cliente.post("/auth/verify", json={"code": "000000"})

    resposta = cliente.post("/auth/verify", json={"code": "000000"})

    assert resposta.status_code == 429


def test_lista_despesas(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/expenses")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 3
    assert dados["total_cents"] == 4750
    assert len(dados["items"]) == 3
    assert dados["items"][0]["expense_date"] == "2026-09-10"


def test_cada_utilizador_ve_so_as_suas_despesas(cliente, session):
    entrar(cliente, session, 222)

    dados = cliente.get("/expenses").json()

    assert dados["total"] == 1
    assert dados["total_cents"] == 9999


def test_lista_despesas_com_filtros(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get(
        "/expenses",
        params={
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "category": "Tecnologia",
        },
    )

    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["items"][0]["merchant"] == "Fnac"


def test_lista_despesas_com_paginacao(cliente, session):
    entrar(cliente, session)

    dados = cliente.get("/expenses", params={"limit": 2, "offset": 2}).json()

    assert dados["total"] == 3
    assert len(dados["items"]) == 1


def test_resumo(cliente, session):
    entrar(cliente, session)

    dados = cliente.get("/stats/summary", params={"month": "2026-09"}).json()

    assert dados["total_cents"] == 4250
    assert dados["previous_total_cents"] == 500
    assert dados["top_merchants"][0]["merchant"] == "Fnac"


def test_totais_por_categoria(cliente, session):
    entrar(cliente, session)

    dados = cliente.get("/stats/by-category", params={"month": "2026-09"}).json()

    assert dados[0]["category"] == "Tecnologia"
    assert dados[0]["total_cents"] == 3000


def test_totais_por_mes(cliente, session):
    entrar(cliente, session)

    dados = cliente.get("/stats/monthly", params={"month": "2026-09", "months": 2}).json()

    assert dados == [
        {"month": "2026-08", "total_cents": 500},
        {"month": "2026-09", "total_cents": 4250},
    ]


def test_mes_invalido(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/stats/summary", params={"month": "setembro"})

    assert resposta.status_code == 400


def test_categorias(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/categories")

    assert resposta.status_code == 200
    assert "Alimentação" in resposta.json()
