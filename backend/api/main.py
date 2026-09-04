from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ListaDeDespesas,
    PedidoDeLogin,
    ResumoDoMes,
    TotalPorCategoria,
    TotalPorMes,
    Utilizador,
)
from core.auth import criar_sessao, ler_sessao, validar_codigo
from core.config import COOKIE_SECURE, CORS_ORIGINS, SESSION_DAYS
from core.db import get_session
from core.models import User
from core.queries import (
    contar_despesas,
    listar_categorias,
    listar_despesas,
    mes_de,
    primeiro_dia_do_mes,
    resumo_do_mes,
    somar_despesas,
    totais_por_categoria,
    totais_por_mes,
    ultimo_dia_do_mes,
)

COOKIE_SESSAO = "finas_session"

MAX_PEDIDOS_LOGIN = 10
JANELA_LOGIN_SEGUNDOS = 300

pedidos_de_login = {}

app = FastAPI(title="Finas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def limite_de_pedidos_ultrapassado(ip):
    agora = datetime.now(timezone.utc)
    limite = agora - timedelta(seconds=JANELA_LOGIN_SEGUNDOS)

    recentes = []
    for momento in pedidos_de_login.get(ip, []):
        if momento > limite:
            recentes.append(momento)

    recentes.append(agora)
    pedidos_de_login[ip] = recentes

    return len(recentes) > MAX_PEDIDOS_LOGIN


def utilizador_atual(request: Request, session=Depends(get_session)):
    user_id = ler_sessao(request.cookies.get(COOKIE_SESSAO))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada")

    utilizador = session.get(User, user_id)
    if utilizador is None:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada")

    return utilizador


def validar_mes(mes):
    if mes is None:
        return mes_de(date.today())

    partes = mes.split("-")
    if len(partes) != 2:
        raise HTTPException(status_code=400, detail="Mes invalido, usar o formato AAAA-MM")

    try:
        primeiro_dia_do_mes(mes)
    except ValueError:
        raise HTTPException(status_code=400, detail="Mes invalido, usar o formato AAAA-MM")

    return mes


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/verify")
def verificar_codigo(
    pedido: PedidoDeLogin,
    request: Request,
    response: Response,
    session=Depends(get_session),
):
    ip = request.client.host if request.client else "desconhecido"
    if limite_de_pedidos_ultrapassado(ip):
        raise HTTPException(status_code=429, detail="Demasiadas tentativas, tenta daqui a pouco")

    utilizador = validar_codigo(session, pedido.code.strip())
    if utilizador is None:
        raise HTTPException(status_code=401, detail="Codigo invalido ou expirado")

    response.set_cookie(
        key=COOKIE_SESSAO,
        value=criar_sessao(utilizador.id),
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )

    return {"ok": True}


@app.post("/auth/logout")
def terminar_sessao(response: Response):
    response.delete_cookie(COOKIE_SESSAO)
    return {"ok": True}


@app.get("/auth/me", response_model=Utilizador)
def eu(utilizador=Depends(utilizador_atual)):
    return utilizador


@app.get("/categories")
def categorias(utilizador=Depends(utilizador_atual), session=Depends(get_session)):
    return listar_categorias(session, utilizador.id)


@app.get("/expenses", response_model=ListaDeDespesas)
def despesas(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    merchant: str | None = None,
    search: str | None = None,
    min_cents: int | None = None,
    max_cents: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    filtros = {
        "data_inicio": start_date,
        "data_fim": end_date,
        "categoria": category,
        "comerciante": merchant,
        "texto": search,
        "valor_min": min_cents,
        "valor_max": max_cents,
    }

    return {
        "total": contar_despesas(session, utilizador.id, filtros),
        "total_cents": somar_despesas(session, utilizador.id, filtros),
        "limit": limit,
        "offset": offset,
        "items": listar_despesas(session, utilizador.id, filtros, limit, offset),
    }


@app.get("/stats/summary", response_model=ResumoDoMes)
def resumo(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    month: str | None = None,
):
    return resumo_do_mes(session, utilizador.id, validar_mes(month))


@app.get("/stats/by-category", response_model=list[TotalPorCategoria])
def por_categoria(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    month: str | None = None,
):
    mes = validar_mes(month)
    return totais_por_categoria(
        session, utilizador.id, primeiro_dia_do_mes(mes), ultimo_dia_do_mes(mes)
    )


@app.get("/stats/monthly", response_model=list[TotalPorMes])
def por_mes(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    month: str | None = None,
    months: int = Query(6, ge=1, le=24),
):
    return totais_por_mes(session, utilizador.id, validar_mes(month), months)
