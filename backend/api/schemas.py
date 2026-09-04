from datetime import date, datetime

from pydantic import BaseModel


class Despesa(BaseModel):
    id: int
    amount_cents: int
    currency: str
    category: str | None
    subcategory: str | None
    merchant: str | None
    description: str | None
    expense_date: date
    payment_method: str | None
    created_at: datetime


class ListaDeDespesas(BaseModel):
    total: int
    total_cents: int
    limit: int
    offset: int
    items: list[Despesa]


class TotalPorCategoria(BaseModel):
    category: str
    total_cents: int
    count: int


class TotalPorComerciante(BaseModel):
    merchant: str
    total_cents: int
    count: int


class TotalPorMes(BaseModel):
    month: str
    total_cents: int


class ResumoDoMes(BaseModel):
    month: str
    total_cents: int
    count: int
    previous_month: str
    previous_total_cents: int
    by_category: list[TotalPorCategoria]
    top_merchants: list[TotalPorComerciante]


class PedidoDeLogin(BaseModel):
    code: str


class Utilizador(BaseModel):
    id: int
    name: str | None
    timezone: str
    currency_default: str
