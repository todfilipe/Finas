from datetime import datetime

from sqlalchemy import select

from core.ai_parsing import CATEGORIAS
from core.config import DEFAULT_CURRENCY, DEFAULT_TIMEZONE
from core.models import Category, Expense, User


def obter_ou_criar_utilizador(session, telegram_user_id, nome=None):
    utilizador = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if utilizador is not None:
        return utilizador

    utilizador = User(
        telegram_user_id=telegram_user_id,
        name=nome,
        timezone=DEFAULT_TIMEZONE,
        currency_default=DEFAULT_CURRENCY,
    )
    session.add(utilizador)
    session.commit()
    return utilizador


def garantir_categorias_por_defeito(session):
    for nome in CATEGORIAS:
        existe = session.scalar(
            select(Category).where(Category.name == nome, Category.is_default.is_(True))
        )
        if existe is None:
            session.add(Category(name=nome, is_default=True))

    session.commit()


def obter_ou_criar_categoria(session, nome):
    if nome not in CATEGORIAS:
        nome = "Outros"

    categoria = session.scalar(
        select(Category).where(Category.name == nome, Category.is_default.is_(True))
    )
    if categoria is not None:
        return categoria

    categoria = Category(name=nome, is_default=True)
    session.add(categoria)
    session.commit()
    return categoria


def guardar_despesa(session, telegram_user_id, despesa, raw_message=None, nome=None):
    utilizador = obter_ou_criar_utilizador(session, telegram_user_id, nome)
    categoria = obter_ou_criar_categoria(session, despesa.category)

    nova = Expense(
        user_id=utilizador.id,
        amount_cents=despesa.amount_cents,
        currency=despesa.currency,
        category_id=categoria.id,
        subcategory=despesa.subcategory,
        merchant=despesa.merchant,
        description=despesa.description,
        expense_date=despesa.expense_date,
        payment_method=despesa.payment_method,
        raw_message=raw_message,
        ai_confidence=despesa.confidence,
    )
    session.add(nova)
    session.commit()
    return nova


def apagar_despesa(session, despesa_id, telegram_user_id):
    utilizador = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if utilizador is None:
        return False

    despesa = session.scalar(
        select(Expense).where(Expense.id == despesa_id, Expense.user_id == utilizador.id)
    )
    if despesa is None:
        return False

    session.delete(despesa)
    session.commit()
    return True


def obter_timezone(session, telegram_user_id):
    utilizador = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if utilizador is None:
        return DEFAULT_TIMEZONE

    return utilizador.timezone


def obter_ultima_despesa(session, telegram_user_id):
    utilizador = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if utilizador is None:
        return None

    despesa = session.scalar(
        select(Expense).where(Expense.user_id == utilizador.id).order_by(Expense.id.desc())
    )
    if despesa is None:
        return None

    categoria = session.get(Category, despesa.category_id)

    return {
        "id": despesa.id,
        "amount_cents": despesa.amount_cents,
        "currency": despesa.currency,
        "category": categoria.name if categoria is not None else None,
        "merchant": despesa.merchant,
        "date": despesa.expense_date.isoformat(),
    }


def atualizar_despesa(session, despesa_id, telegram_user_id, campos):
    utilizador = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if utilizador is None:
        return None

    despesa = session.scalar(
        select(Expense).where(Expense.id == despesa_id, Expense.user_id == utilizador.id)
    )
    if despesa is None:
        return None

    if "amount_cents" in campos:
        despesa.amount_cents = campos["amount_cents"]
    if "currency" in campos:
        despesa.currency = campos["currency"]
    if "category" in campos:
        categoria = obter_ou_criar_categoria(session, campos["category"])
        despesa.category_id = categoria.id
    if "subcategory" in campos:
        despesa.subcategory = campos["subcategory"]
    if "merchant" in campos:
        despesa.merchant = campos["merchant"]
    if "description" in campos:
        despesa.description = campos["description"]
    if "payment_method" in campos:
        despesa.payment_method = campos["payment_method"]
    if "expense_date" in campos:
        despesa.expense_date = campos["expense_date"]

    session.commit()
    return despesa


def converter_valor_para_centimos(texto):
    limpo = texto.strip().lower().replace("€", "").replace("euros", "").replace("euro", "")
    limpo = limpo.replace(",", ".").strip()

    try:
        valor = float(limpo)
    except ValueError:
        return None

    if valor <= 0:
        return None

    return round(valor * 100)


def converter_data_escrita(texto):
    limpo = texto.strip()

    for formato in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]:
        try:
            return datetime.strptime(limpo, formato).date()
        except ValueError:
            pass

    return None
