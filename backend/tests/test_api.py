import logging
from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import COOKIE_SESSAO, app, pedidos_de_login, pedidos_por_utilizador
from core.auth import criar_codigo_de_acesso, criar_sessao
from core.db import get_session
from core.queries import obter_utilizador_por_telegram
from tests.test_queries import preparar_dados


@pytest.fixture
def cliente(session):
    preparar_dados(session)
    pedidos_de_login.clear()
    pedidos_por_utilizador.clear()

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


def nomes_das_categorias(cliente):
    nomes = []
    for categoria in cliente.get("/categories").json():
        nomes.append(categoria["name"])

    return nomes


def categoria_chamada(cliente, nome):
    for categoria in cliente.get("/categories").json():
        if categoria["name"] == nome:
            return categoria

    return None


def test_categorias(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/categories")

    assert resposta.status_code == 200
    assert "Alimentação" in nomes_das_categorias(cliente)


def test_categorias_trazem_totais(cliente, session):
    entrar(cliente, session)

    alimentacao = categoria_chamada(cliente, "Alimentação")
    casa = categoria_chamada(cliente, "Casa")

    assert alimentacao["count"] == 2
    assert alimentacao["total_cents"] == 1750
    assert casa["count"] == 0
    assert casa["total_cents"] == 0


def test_criar_categoria(cliente, session):
    entrar(cliente, session)

    resposta = cliente.post("/categories", json={"name": "  Ginásio  "})

    assert resposta.status_code == 201
    assert resposta.json()["name"] == "Ginásio"
    assert resposta.json()["is_default"] is False
    assert "Ginásio" in nomes_das_categorias(cliente)


def test_criar_categoria_repetida(cliente, session):
    entrar(cliente, session)

    resposta = cliente.post("/categories", json={"name": "alimentação"})

    assert resposta.status_code == 400


def test_criar_categoria_sem_nome(cliente, session):
    entrar(cliente, session)

    assert cliente.post("/categories", json={"name": "   "}).status_code == 400
    assert cliente.post("/categories", json={"name": "a" * 101}).status_code == 400


def test_renomear_categoria(cliente, session):
    entrar(cliente, session)
    lazer = categoria_chamada(cliente, "Lazer")

    resposta = cliente.patch("/categories/" + str(lazer["id"]), json={"name": "Saídas"})

    assert resposta.status_code == 200
    assert resposta.json()["name"] == "Saídas"
    assert "Lazer" not in nomes_das_categorias(cliente)


def test_renomear_para_um_nome_que_ja_existe(cliente, session):
    entrar(cliente, session)
    lazer = categoria_chamada(cliente, "Lazer")

    resposta = cliente.patch("/categories/" + str(lazer["id"]), json={"name": "Casa"})

    assert resposta.status_code == 400


def test_mesclar_categorias(cliente, session):
    entrar(cliente, session)
    tecnologia = categoria_chamada(cliente, "Tecnologia")
    casa = categoria_chamada(cliente, "Casa")

    resposta = cliente.post(
        "/categories/" + str(tecnologia["id"]) + "/merge", json={"target_id": casa["id"]}
    )

    assert resposta.status_code == 200
    assert resposta.json()["name"] == "Casa"
    assert resposta.json()["count"] == 1
    assert resposta.json()["total_cents"] == 3000
    assert "Tecnologia" not in nomes_das_categorias(cliente)


def test_mesclar_uma_categoria_consigo_mesma(cliente, session):
    entrar(cliente, session)
    casa = categoria_chamada(cliente, "Casa")

    resposta = cliente.post(
        "/categories/" + str(casa["id"]) + "/merge", json={"target_id": casa["id"]}
    )

    assert resposta.status_code == 400


def test_apagar_categoria_sem_despesas(cliente, session):
    entrar(cliente, session)
    casa = categoria_chamada(cliente, "Casa")

    resposta = cliente.delete("/categories/" + str(casa["id"]))

    assert resposta.status_code == 200
    assert "Casa" not in nomes_das_categorias(cliente)


def test_nao_apaga_categoria_com_despesas(cliente, session):
    entrar(cliente, session)
    tecnologia = categoria_chamada(cliente, "Tecnologia")

    resposta = cliente.delete("/categories/" + str(tecnologia["id"]))

    assert resposta.status_code == 400
    assert "Tecnologia" in nomes_das_categorias(cliente)


def test_nao_deixa_mexer_em_categoria_de_outro(cliente, session):
    entrar(cliente, session, telegram_user_id=222)
    do_outro = cliente.get("/categories").json()[0]

    cliente.post("/auth/logout")
    entrar(cliente, session, telegram_user_id=111)

    caminho = "/categories/" + str(do_outro["id"])
    assert cliente.patch(caminho, json={"name": "Roubada"}).status_code == 404
    assert cliente.delete(caminho).status_code == 404


def test_categorias_sem_sessao(cliente):
    assert cliente.get("/categories").status_code == 401
    assert cliente.post("/categories", json={"name": "Ginásio"}).status_code == 401


def primeira_despesa(cliente):
    return cliente.get("/expenses").json()["items"][0]


def test_ver_uma_despesa(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.get("/expenses/" + str(despesa["id"]))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == despesa["id"]


def test_editar_despesa(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch(
        "/expenses/" + str(despesa["id"]),
        json={
            "amount_cents": 1500,
            "category": "Lazer",
            "merchant": "Cinema",
            "description": "bilhete",
            "expense_date": "2026-09-11",
        },
    )

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["amount_cents"] == 1500
    assert dados["category"] == "Lazer"
    assert dados["merchant"] == "Cinema"
    assert dados["description"] == "bilhete"
    assert dados["expense_date"] == "2026-09-11"


def test_editar_so_um_campo_nao_mexe_no_resto(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    dados = cliente.patch(
        "/expenses/" + str(despesa["id"]), json={"description": "nova descrição"}
    ).json()

    assert dados["description"] == "nova descrição"
    assert dados["amount_cents"] == despesa["amount_cents"]
    assert dados["category"] == despesa["category"]


def test_editar_texto_vazio_fica_a_nulo(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    dados = cliente.patch("/expenses/" + str(despesa["id"]), json={"merchant": "   "}).json()

    assert dados["merchant"] is None


def test_editar_com_valor_negativo(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={"amount_cents": -100})

    assert resposta.status_code == 400


def test_editar_com_categoria_invalida(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={"category": "Criptomoedas"})

    assert resposta.status_code == 400


def test_editar_sem_campos(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={})

    assert resposta.status_code == 400


def test_apagar_despesa(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)
    quantas = cliente.get("/expenses").json()["total"]

    resposta = cliente.delete("/expenses/" + str(despesa["id"]))

    assert resposta.status_code == 200
    assert cliente.get("/expenses").json()["total"] == quantas - 1
    assert cliente.get("/expenses/" + str(despesa["id"])).status_code == 404


def test_nao_deixa_mexer_em_despesa_de_outro(cliente, session):
    entrar(cliente, session, telegram_user_id=222)
    despesa_do_outro = cliente.get("/expenses").json()["items"][0]

    cliente.post("/auth/logout")
    entrar(cliente, session, telegram_user_id=111)

    assert cliente.get("/expenses/" + str(despesa_do_outro["id"])).status_code == 404
    assert (
        cliente.patch(
            "/expenses/" + str(despesa_do_outro["id"]), json={"amount_cents": 1}
        ).status_code
        == 404
    )
    assert cliente.delete("/expenses/" + str(despesa_do_outro["id"])).status_code == 404


def test_apagar_sem_sessao(cliente, session):
    despesa_id = 1

    assert cliente.delete("/expenses/" + str(despesa_id)).status_code == 401
    assert cliente.patch("/expenses/" + str(despesa_id), json={"merchant": "x"}).status_code == 401


def test_sessao_de_utilizador_que_ja_nao_existe(cliente):
    cliente.cookies.set(COOKIE_SESSAO, criar_sessao(9999))

    assert cliente.get("/auth/me").status_code == 401


def test_resumo_sem_mes_usa_o_mes_de_hoje(cliente, session):
    entrar(cliente, session)

    resposta = cliente.get("/stats/summary")

    assert resposta.status_code == 200
    assert resposta.json()["month"] == date.today().strftime("%Y-%m")


def test_resumo_com_mes_sem_o_traco(cliente, session):
    entrar(cliente, session)

    assert cliente.get("/stats/summary", params={"month": "2026"}).status_code == 400


def test_resumo_com_mes_que_nao_existe(cliente, session):
    entrar(cliente, session)

    assert cliente.get("/stats/summary", params={"month": "2026-13"}).status_code == 400


def test_categorias_com_tipo_invalido(cliente, session):
    entrar(cliente, session)

    assert cliente.get("/categories", params={"kind": "poupanca"}).status_code == 400


def test_despesas_filtradas_por_tipo_zeram_o_outro_tipo(cliente, session):
    entrar(cliente, session)

    dados = cliente.get("/expenses", params={"kind": "expense"}).json()

    assert dados["expense_cents"] == dados["total_cents"]
    assert dados["income_cents"] == 0


def test_editar_data_a_nulo(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={"expense_date": None})

    assert resposta.status_code == 400


def test_editar_moeda_a_nulo(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={"currency": None})

    assert resposta.status_code == 400


def test_editar_moeda_com_tamanho_errado(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    resposta = cliente.patch("/expenses/" + str(despesa["id"]), json={"currency": "euros"})

    assert resposta.status_code == 400


def test_editar_moeda_fica_em_maiusculas(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    dados = cliente.patch("/expenses/" + str(despesa["id"]), json={"currency": " usd "}).json()

    assert dados["currency"] == "USD"


def test_editar_comerciante_a_nulo(cliente, session):
    entrar(cliente, session)
    despesa = primeira_despesa(cliente)

    dados = cliente.patch("/expenses/" + str(despesa["id"]), json={"merchant": None}).json()

    assert dados["merchant"] is None


def test_editar_despesa_de_outro_utilizador(cliente, session):
    entrar(cliente, session, telegram_user_id=222)
    do_outro = primeira_despesa(cliente)
    cliente.post("/auth/logout")
    entrar(cliente, session, telegram_user_id=111)

    resposta = cliente.patch("/expenses/" + str(do_outro["id"]), json={"merchant": "Roubada"})

    assert resposta.status_code == 404


@pytest.fixture
def cliente_com_erros(session):
    preparar_dados(session)
    pedidos_de_login.clear()
    pedidos_por_utilizador.clear()

    def sessao_de_teste():
        yield session

    app.dependency_overrides[get_session] = sessao_de_teste
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def rebentar(*args, **kwargs):
    raise RuntimeError("a base de dados foi abaixo")


def test_pedido_fica_no_log(cliente, caplog):
    with caplog.at_level(logging.INFO, logger="api.main"):
        cliente.get("/health")

    assert "GET /health 200" in caplog.text


def test_erro_nao_previsto_devolve_500(cliente_com_erros, session, monkeypatch):
    entrar(cliente_com_erros, session)
    monkeypatch.setattr("api.main.listar_categorias_com_totais", rebentar)

    resposta = cliente_com_erros.get("/categories")

    assert resposta.status_code == 500
    assert resposta.json() == {"detail": "Erro interno"}


def test_erro_nao_previsto_nao_mostra_detalhes_ao_utilizador(
    cliente_com_erros, session, monkeypatch
):
    entrar(cliente_com_erros, session)
    monkeypatch.setattr("api.main.listar_categorias_com_totais", rebentar)

    resposta = cliente_com_erros.get("/categories")

    assert "base de dados foi abaixo" not in resposta.text
    assert "Traceback" not in resposta.text


def test_erro_nao_previsto_avisa_o_admin(cliente_com_erros, session, monkeypatch):
    entrar(cliente_com_erros, session)
    avisos = []
    monkeypatch.setattr(
        "api.main.avisar_erro",
        lambda servico, onde, erro: avisos.append((servico, onde, str(erro))),
    )
    monkeypatch.setattr("api.main.listar_categorias_com_totais", rebentar)

    cliente_com_erros.get("/categories")

    assert avisos == [("na API", "GET /categories", "a base de dados foi abaixo")]


def test_erro_nao_previsto_fica_no_log_com_traceback(
    cliente_com_erros, session, monkeypatch, caplog
):
    entrar(cliente_com_erros, session)
    monkeypatch.setattr("api.main.avisar_erro", lambda servico, onde, erro: False)
    monkeypatch.setattr("api.main.listar_categorias_com_totais", rebentar)

    with caplog.at_level(logging.ERROR, logger="api.main"):
        cliente_com_erros.get("/categories")

    assert "GET /categories" in caplog.text
    assert "a base de dados foi abaixo" in caplog.text
    assert "Traceback" in caplog.text


def test_erro_previsto_nao_avisa_o_admin(cliente_com_erros, session, monkeypatch):
    entrar(cliente_com_erros, session)
    avisos = []
    monkeypatch.setattr("api.main.avisar_erro", lambda servico, onde, erro: avisos.append(onde))

    resposta = cliente_com_erros.get("/expenses/99999")

    assert resposta.status_code == 404
    assert avisos == []


def test_limite_de_pedidos_por_utilizador(cliente, session, monkeypatch):
    entrar(cliente, session)
    monkeypatch.setattr("api.main.API_MAX_REQUESTS", 3)

    for _ in range(3):
        assert cliente.get("/expenses").status_code == 200

    resposta = cliente.get("/expenses")

    assert resposta.status_code == 429
    assert resposta.json()["detail"] == "Demasiados pedidos, tenta daqui a pouco"


def test_limite_da_api_e_por_utilizador(cliente, session, monkeypatch):
    monkeypatch.setattr("api.main.API_MAX_REQUESTS", 2)
    entrar(cliente, session, telegram_user_id=111)
    cliente.get("/expenses")
    cliente.get("/expenses")
    assert cliente.get("/expenses").status_code == 429

    cliente.post("/auth/logout")
    entrar(cliente, session, telegram_user_id=222)

    assert cliente.get("/expenses").status_code == 200


def test_limite_da_api_fica_no_log(cliente, session, monkeypatch, caplog):
    entrar(cliente, session)
    monkeypatch.setattr("api.main.API_MAX_REQUESTS", 1)
    cliente.get("/expenses")

    with caplog.at_level(logging.WARNING, logger="api.main"):
        cliente.get("/expenses")

    assert "passou o limite de pedidos da API" in caplog.text


def test_login_travado_ao_fim_de_muitas_tentativas(cliente, monkeypatch):
    monkeypatch.setattr("api.main.MAX_PEDIDOS_LOGIN", 3)

    for _ in range(3):
        assert cliente.post("/auth/verify", json={"code": "000000"}).status_code == 401

    resposta = cliente.post("/auth/verify", json={"code": "000000"})

    assert resposta.status_code == 429


def test_login_travado_fica_no_log(cliente, monkeypatch, caplog):
    monkeypatch.setattr("api.main.MAX_PEDIDOS_LOGIN", 1)
    cliente.post("/auth/verify", json={"code": "000000"})

    with caplog.at_level(logging.WARNING, logger="api.main"):
        cliente.post("/auth/verify", json={"code": "000000"})

    assert "Demasiadas tentativas de login" in caplog.text


def test_health_nao_conta_para_o_limite(cliente, session, monkeypatch):
    entrar(cliente, session)
    monkeypatch.setattr("api.main.API_MAX_REQUESTS", 1)
    cliente.get("/expenses")

    for _ in range(5):
        assert cliente.get("/health").status_code == 200
