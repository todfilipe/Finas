from datetime import date, datetime

from pydantic import BaseModel


class Despesa(BaseModel):
    id: int
    kind: str
    amount_cents: int
    currency: str
    category: str | None
    subcategory: str | None
    merchant: str | None
    description: str | None
    expense_date: date
    payment_method: str | None
    created_at: datetime


class AtualizacaoDeDespesa(BaseModel):
    amount_cents: int | None = None
    currency: str | None = None
    category: str | None = None
    subcategory: str | None = None
    merchant: str | None = None
    description: str | None = None
    expense_date: date | None = None
    payment_method: str | None = None


class ListaDeDespesas(BaseModel):
    total: int
    total_cents: int
    expense_cents: int
    income_cents: int
    limit: int
    offset: int
    items: list[Despesa]


class Categoria(BaseModel):
    id: int
    name: str
    kind: str
    is_default: bool
    count: int
    total_cents: int


class NomeDeCategoria(BaseModel):
    name: str
    kind: str = "expense"


class Mesclagem(BaseModel):
    target_id: int


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
    income_cents: int
    income_count: int
    balance_cents: int
    previous_month: str
    previous_total_cents: int
    previous_income_cents: int
    previous_balance_cents: int
    by_category: list[TotalPorCategoria]
    income_by_category: list[TotalPorCategoria]
    top_merchants: list[TotalPorComerciante]


class PedidoDeLogin(BaseModel):
    code: str


class Utilizador(BaseModel):
    id: int
    name: str | None
    timezone: str
    currency_default: str
