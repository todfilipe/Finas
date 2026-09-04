import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    AtualizacaoDeDespesa,
    Categoria,
    Despesa,
    ListaDeDespesas,
    Mesclagem,
    NomeDeCategoria,
    PedidoDeLogin,
    ResumoDoMes,
    TotalPorCategoria,
    TotalPorMes,
    Utilizador,
)
from core.alerts import avisar_erro
from core.auth import criar_sessao, ler_sessao, validar_codigo
from core.categories import (
    TIPO_RECEITA,
    TIPOS,
    apagar_categoria,
    criar_categoria,
    listar_categorias_com_totais,
    mesclar_categorias,
    renomear_categoria,
)
from core.categories import TIPO_DESPESA
from core.config import (
    API_MAX_REQUESTS,
    API_RATE_WINDOW_SECONDS,
    COOKIE_SECURE,
    CORS_ORIGINS,
    SESSION_DAYS,
)
from core.db import get_session
from core.expenses import apagar_despesa_do_utilizador, atualizar_despesa_do_utilizador
from core.limits import ultrapassou_o_limite
from core.logs import configurar_logging
from core.models import User
from core.queries import (
    contar_despesas,
    listar_categorias,
    listar_despesas,
    mes_de,
    obter_despesa,
    primeiro_dia_do_mes,
    resumo_do_mes,
    somar_despesas,
    totais_por_categoria,
    totais_por_mes,
    ultimo_dia_do_mes,
)

configurar_logging("api")
logger = logging.getLogger(__name__)

COOKIE_SESSAO = "finas_session"

MAX_PEDIDOS_LOGIN = 10
JANELA_LOGIN_SEGUNDOS = 300

pedidos_de_login = {}
pedidos_por_utilizador = {}

app = FastAPI(title="Finas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def registar_pedido(request: Request, call_next):
    inicio = time.monotonic()
    resposta = await call_next(request)
    demorou = round((time.monotonic() - inicio) * 1000)

    logger.info(
        "%s %s %s %sms",
        request.method,
        request.url.path,
        resposta.status_code,
        demorou,
    )
    return resposta


@app.exception_handler(Exception)
async def erro_nao_previsto(request: Request, erro: Exception):
    onde = request.method + " " + request.url.path
    logger.error("Erro nao previsto em %s", onde, exc_info=erro)
    await asyncio.to_thread(avisar_erro, "na API", onde, erro)

    return JSONResponse(status_code=500, content={"detail": "Erro interno"})


def limite_de_pedidos_ultrapassado(ip):
    return ultrapassou_o_limite(pedidos_de_login, ip, MAX_PEDIDOS_LOGIN, JANELA_LOGIN_SEGUNDOS)


def utilizador_atual(request: Request, session=Depends(get_session)):
    user_id = ler_sessao(request.cookies.get(COOKIE_SESSAO))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada")

    utilizador = session.get(User, user_id)
    if utilizador is None:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada")

    if ultrapassou_o_limite(
        pedidos_por_utilizador, user_id, API_MAX_REQUESTS, API_RATE_WINDOW_SECONDS
    ):
        logger.warning("Utilizador %s passou o limite de pedidos da API", user_id)
        raise HTTPException(status_code=429, detail="Demasiados pedidos, tenta daqui a pouco")

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
        logger.warning("Demasiadas tentativas de login vindas de %s", ip)
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


def validar_tipo(tipo):
    if tipo is None:
        return None

    if tipo not in TIPOS:
        raise HTTPException(status_code=400, detail="Tipo invalido")

    return tipo


@app.get("/categories", response_model=list[Categoria])
def categorias(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    kind: str | None = None,
):
    return listar_categorias_com_totais(session, utilizador.id, validar_tipo(kind))


def uma_categoria(session, user_id, categoria_id):
    for categoria in listar_categorias_com_totais(session, user_id):
        if categoria["id"] == categoria_id:
            return categoria

    raise HTTPException(status_code=404, detail="Categoria nao encontrada")


def rebentar_se_falhou(erro):
    if erro is None:
        return

    if erro == "Categoria nao encontrada":
        raise HTTPException(status_code=404, detail=erro)

    raise HTTPException(status_code=400, detail=erro)


@app.post("/categories", response_model=Categoria, status_code=201)
def nova_categoria(
    pedido: NomeDeCategoria,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    categoria, erro = criar_categoria(
        session, utilizador.id, pedido.name, validar_tipo(pedido.kind)
    )
    rebentar_se_falhou(erro)

    return uma_categoria(session, utilizador.id, categoria.id)


@app.patch("/categories/{category_id}", response_model=Categoria)
def renomear(
    category_id: int,
    pedido: NomeDeCategoria,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    categoria, erro = renomear_categoria(session, utilizador.id, category_id, pedido.name)
    rebentar_se_falhou(erro)

    return uma_categoria(session, utilizador.id, categoria.id)


@app.post("/categories/{category_id}/merge", response_model=Categoria)
def mesclar(
    category_id: int,
    pedido: Mesclagem,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    destino, erro = mesclar_categorias(session, utilizador.id, category_id, pedido.target_id)
    rebentar_se_falhou(erro)

    return uma_categoria(session, utilizador.id, destino.id)


@app.delete("/categories/{category_id}")
def remover_categoria(
    category_id: int,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    apagou, erro = apagar_categoria(session, utilizador.id, category_id)
    rebentar_se_falhou(erro)

    return {"ok": apagou}


@app.get("/expenses", response_model=ListaDeDespesas)
def despesas(
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
    start_date: date | None = None,
    end_date: date | None = None,
    kind: str | None = None,
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
        "tipo": validar_tipo(kind),
        "categoria": category,
        "comerciante": merchant,
        "texto": search,
        "valor_min": min_cents,
        "valor_max": max_cents,
    }

    def somar_do_tipo(alvo):
        if filtros["tipo"] is not None and filtros["tipo"] != alvo:
            return 0

        so_deste_tipo = dict(filtros)
        so_deste_tipo["tipo"] = alvo
        return somar_despesas(session, utilizador.id, so_deste_tipo)

    return {
        "total": contar_despesas(session, utilizador.id, filtros),
        "total_cents": somar_despesas(session, utilizador.id, filtros),
        "expense_cents": somar_do_tipo(TIPO_DESPESA),
        "income_cents": somar_do_tipo(TIPO_RECEITA),
        "limit": limit,
        "offset": offset,
        "items": listar_despesas(session, utilizador.id, filtros, limit, offset),
    }


TEXTOS_DA_DESPESA = ["subcategory", "merchant", "description", "payment_method"]


def limpar_texto(valor):
    if valor is None:
        return None

    limpo = valor.strip()
    if limpo == "":
        return None

    return limpo


@app.get("/expenses/{expense_id}", response_model=Despesa)
def uma_despesa(
    expense_id: int,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    despesa = obter_despesa(session, utilizador.id, expense_id)
    if despesa is None:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    return despesa


@app.patch("/expenses/{expense_id}", response_model=Despesa)
def editar_despesa(
    expense_id: int,
    pedido: AtualizacaoDeDespesa,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    campos = pedido.model_dump(exclude_unset=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Nao ha nada para mudar")

    atual = obter_despesa(session, utilizador.id, expense_id)
    if atual is None:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    if "amount_cents" in campos:
        if campos["amount_cents"] is None or campos["amount_cents"] <= 0:
            raise HTTPException(status_code=400, detail="O valor tem de ser maior que zero")

    if "expense_date" in campos and campos["expense_date"] is None:
        raise HTTPException(status_code=400, detail="A data e obrigatoria")

    if "currency" in campos:
        if campos["currency"] is None:
            raise HTTPException(status_code=400, detail="A moeda e obrigatoria")
        campos["currency"] = campos["currency"].strip().upper()
        if len(campos["currency"]) != 3:
            raise HTTPException(status_code=400, detail="Moeda invalida")

    if campos.get("category") is not None:
        validas = listar_categorias(session, utilizador.id, atual["kind"])
        if campos["category"] not in validas:
            raise HTTPException(status_code=400, detail="Categoria invalida")

    for nome in TEXTOS_DA_DESPESA:
        if nome in campos:
            campos[nome] = limpar_texto(campos[nome])

    atualizada = atualizar_despesa_do_utilizador(session, expense_id, utilizador.id, campos)
    if atualizada is None:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    return obter_despesa(session, utilizador.id, expense_id)


@app.delete("/expenses/{expense_id}")
def remover_despesa(
    expense_id: int,
    utilizador=Depends(utilizador_atual),
    session=Depends(get_session),
):
    apagou = apagar_despesa_do_utilizador(session, expense_id, utilizador.id)
    if not apagou:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    return {"ok": True}


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
