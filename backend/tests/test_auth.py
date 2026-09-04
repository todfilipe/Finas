from datetime import timedelta

from core.auth import (
    agora_utc,
    criar_codigo_de_acesso,
    criar_sessao,
    gerar_codigo,
    ler_sessao,
    limpar_codigos_antigos,
    validar_codigo,
)
from core.config import MAX_LOGIN_ATTEMPTS
from core.expenses import obter_ou_criar_utilizador
from core.models import LoginToken


def test_codigo_tem_seis_digitos():
    for _ in range(50):
        codigo = gerar_codigo()
        assert len(codigo) == 6
        assert codigo.isdigit()


def test_criar_codigo_guarda_token(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    codigo = criar_codigo_de_acesso(session, utilizador.id)

    token = session.query(LoginToken).one()
    assert token.code == codigo
    assert token.user_id == utilizador.id
    assert token.used_at is None
    assert token.attempts == 0


def test_codigo_valido_devolve_utilizador(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    codigo = criar_codigo_de_acesso(session, utilizador.id)

    encontrado = validar_codigo(session, codigo)

    assert encontrado is not None
    assert encontrado.id == utilizador.id


def test_codigo_so_serve_uma_vez(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    codigo = criar_codigo_de_acesso(session, utilizador.id)

    assert validar_codigo(session, codigo) is not None
    assert validar_codigo(session, codigo) is None


def test_codigo_expirado_nao_serve(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    codigo = criar_codigo_de_acesso(session, utilizador.id)

    token = session.query(LoginToken).one()
    token.expires_at = agora_utc() - timedelta(minutes=1)
    session.commit()

    assert validar_codigo(session, codigo) is None


def test_codigo_errado_nao_serve(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    criar_codigo_de_acesso(session, utilizador.id)

    assert validar_codigo(session, "000000") is None
    assert validar_codigo(session, "abc") is None
    assert validar_codigo(session, None) is None


def test_tentativas_erradas_invalidam_o_codigo(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    codigo = criar_codigo_de_acesso(session, utilizador.id)

    for _ in range(MAX_LOGIN_ATTEMPTS):
        validar_codigo(session, "000000")

    assert session.query(LoginToken).one().attempts == MAX_LOGIN_ATTEMPTS
    assert validar_codigo(session, codigo) is None


def test_cada_pedido_gera_o_seu_codigo(session):
    utilizador = obter_ou_criar_utilizador(session, 111)

    primeiro = criar_codigo_de_acesso(session, utilizador.id)
    segundo = criar_codigo_de_acesso(session, utilizador.id)

    assert validar_codigo(session, primeiro) is not None
    assert validar_codigo(session, segundo) is not None


def test_sessao_guarda_o_utilizador():
    token = criar_sessao(42)

    assert ler_sessao(token) == 42


def test_sessao_invalida():
    assert ler_sessao(None) is None
    assert ler_sessao("") is None
    assert ler_sessao("isto-nao-e-um-token") is None


def test_limpar_codigos_antigos(session):
    utilizador = obter_ou_criar_utilizador(session, 111)
    criar_codigo_de_acesso(session, utilizador.id)
    criar_codigo_de_acesso(session, utilizador.id)

    antigo = session.query(LoginToken).first()
    antigo.created_at = agora_utc() - timedelta(days=2)
    session.commit()

    limpar_codigos_antigos(session)

    assert session.query(LoginToken).count() == 1
