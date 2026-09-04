import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select

from core.config import (
    LOGIN_CODE_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    SESSION_DAYS,
    SESSION_SECRET,
)
from core.models import LoginToken, User


def agora_utc():
    return datetime.now(timezone.utc)


def tornar_utc(momento):
    if momento is None:
        return None
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def gerar_codigo():
    return str(secrets.randbelow(900000) + 100000)


def criar_codigo_de_acesso(session, user_id):
    codigo = gerar_codigo()

    token = LoginToken(
        user_id=user_id,
        code=codigo,
        expires_at=agora_utc() + timedelta(minutes=LOGIN_CODE_MINUTES),
        attempts=0,
    )
    session.add(token)
    session.commit()
    return codigo


def tokens_ativos(session):
    consulta = select(LoginToken).where(LoginToken.used_at.is_(None))

    ativos = []
    for token in session.scalars(consulta).all():
        if tornar_utc(token.expires_at) <= agora_utc():
            continue
        if token.attempts >= MAX_LOGIN_ATTEMPTS:
            continue
        ativos.append(token)

    return ativos


def registar_tentativa_falhada(session):
    for token in tokens_ativos(session):
        token.attempts = token.attempts + 1

    session.commit()


def validar_codigo(session, codigo):
    if codigo is None or len(codigo) != 6 or not codigo.isdigit():
        registar_tentativa_falhada(session)
        return None

    token = None
    for ativo in tokens_ativos(session):
        if ativo.code == codigo:
            token = ativo

    if token is None:
        registar_tentativa_falhada(session)
        return None

    token.used_at = agora_utc()
    session.commit()

    return session.get(User, token.user_id)


def criar_sessao(user_id):
    dados = {
        "user_id": user_id,
        "exp": agora_utc() + timedelta(days=SESSION_DAYS),
    }
    return jwt.encode(dados, SESSION_SECRET, algorithm="HS256")


def ler_sessao(token):
    if not token:
        return None

    try:
        dados = jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    return dados.get("user_id")


def limpar_codigos_antigos(session):
    consulta = select(LoginToken).where(LoginToken.created_at.is_not(None))

    limite = agora_utc() - timedelta(days=1)
    for token in session.scalars(consulta).all():
        if tornar_utc(token.created_at) < limite:
            session.delete(token)

    session.commit()
