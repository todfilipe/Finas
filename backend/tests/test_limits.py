from core.db import opcoes_de_ligacao
from core.limits import momentos_recentes, ultrapassou_o_limite


def test_deixa_passar_ate_ao_maximo():
    registos = {}

    for _ in range(3):
        assert ultrapassou_o_limite(registos, "filipe", 3, 60) is False


def test_trava_a_seguir_ao_maximo():
    registos = {}
    for _ in range(3):
        ultrapassou_o_limite(registos, "filipe", 3, 60)

    assert ultrapassou_o_limite(registos, "filipe", 3, 60) is True


def test_cada_chave_tem_o_seu_contador():
    registos = {}
    for _ in range(3):
        ultrapassou_o_limite(registos, "filipe", 3, 60)

    assert ultrapassou_o_limite(registos, "filipe", 3, 60) is True
    assert ultrapassou_o_limite(registos, "outra pessoa", 3, 60) is False


def test_tentativa_travada_nao_estica_o_castigo():
    registos = {}
    for _ in range(3):
        ultrapassou_o_limite(registos, "filipe", 3, 60)

    ultrapassou_o_limite(registos, "filipe", 3, 60)

    assert len(registos["filipe"]) == 3


def test_momentos_antigos_saem_da_janela():
    registos = {"filipe": [100.0, 200.0, 300.0]}

    assert momentos_recentes(registos["filipe"], 350.0, 60) == [300.0]


def test_volta_a_deixar_passar_quando_a_janela_expira():
    registos = {}
    for _ in range(3):
        ultrapassou_o_limite(registos, "filipe", 3, 60)

    registos["filipe"] = [momento - 120 for momento in registos["filipe"]]

    assert ultrapassou_o_limite(registos, "filipe", 3, 60) is False


def test_postgres_leva_timeout_de_ligacao(monkeypatch):
    monkeypatch.setattr("core.db.DATABASE_URL", "postgresql+psycopg://finas@db:5432/finas")
    monkeypatch.setattr("core.db.DB_CONNECT_SECONDS", 5)

    assert opcoes_de_ligacao() == {"connect_timeout": 5}


def test_sqlite_nao_leva_timeout_de_ligacao(monkeypatch):
    monkeypatch.setattr("core.db.DATABASE_URL", "sqlite:///finas.db")

    assert opcoes_de_ligacao() == {}


def test_sem_database_url_nao_rebenta(monkeypatch):
    monkeypatch.setattr("core.db.DATABASE_URL", None)

    assert opcoes_de_ligacao() == {}
