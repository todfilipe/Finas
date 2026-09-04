from datetime import date, timedelta

from sqlalchemy import func, or_, select

from core.models import Category, Expense, User


def obter_utilizador_por_telegram(session, telegram_user_id):
    return session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))


def primeiro_dia_do_mes(mes):
    ano, numero = mes.split("-")
    return date(int(ano), int(numero), 1)


def ultimo_dia_do_mes(mes):
    inicio = primeiro_dia_do_mes(mes)
    if inicio.month == 12:
        return date(inicio.year, 12, 31)
    return date(inicio.year, inicio.month + 1, 1) - timedelta(days=1)


def mes_anterior(mes):
    inicio = primeiro_dia_do_mes(mes)
    if inicio.month == 1:
        return f"{inicio.year - 1}-12"
    return f"{inicio.year}-{inicio.month - 1:02d}"


def mes_de(data_qualquer):
    return f"{data_qualquer.year}-{data_qualquer.month:02d}"


def ultimos_meses(mes_final, quantos):
    meses = [mes_final]
    for _ in range(quantos - 1):
        meses.append(mes_anterior(meses[-1]))
    meses.reverse()
    return meses


def construir_condicoes(user_id, filtros):
    condicoes = [Expense.user_id == user_id]

    if filtros.get("data_inicio") is not None:
        condicoes.append(Expense.expense_date >= filtros["data_inicio"])
    if filtros.get("data_fim") is not None:
        condicoes.append(Expense.expense_date <= filtros["data_fim"])
    if filtros.get("categoria"):
        subconsulta = select(Category.id).where(Category.name == filtros["categoria"])
        condicoes.append(Expense.category_id.in_(subconsulta))
    if filtros.get("comerciante"):
        condicoes.append(Expense.merchant.ilike("%" + filtros["comerciante"] + "%"))
    if filtros.get("texto"):
        procura = "%" + filtros["texto"] + "%"
        condicoes.append(
            or_(
                Expense.description.ilike(procura),
                Expense.merchant.ilike(procura),
                Expense.raw_message.ilike(procura),
            )
        )
    if filtros.get("valor_min") is not None:
        condicoes.append(Expense.amount_cents >= filtros["valor_min"])
    if filtros.get("valor_max") is not None:
        condicoes.append(Expense.amount_cents <= filtros["valor_max"])

    return condicoes


def montar_despesa(despesa, nome_categoria):
    return {
        "id": despesa.id,
        "amount_cents": despesa.amount_cents,
        "currency": despesa.currency,
        "category": nome_categoria,
        "subcategory": despesa.subcategory,
        "merchant": despesa.merchant,
        "description": despesa.description,
        "expense_date": despesa.expense_date,
        "payment_method": despesa.payment_method,
        "created_at": despesa.created_at,
    }


def listar_despesas(session, user_id, filtros, limite=50, salto=0):
    consulta = (
        select(Expense, Category.name)
        .select_from(Expense)
        .join(Category, Expense.category_id == Category.id, isouter=True)
        .where(*construir_condicoes(user_id, filtros))
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(limite)
        .offset(salto)
    )

    despesas = []
    for despesa, nome_categoria in session.execute(consulta).all():
        despesas.append(montar_despesa(despesa, nome_categoria))

    return despesas


def contar_despesas(session, user_id, filtros):
    consulta = (
        select(func.count()).select_from(Expense).where(*construir_condicoes(user_id, filtros))
    )
    return session.scalar(consulta) or 0


def somar_despesas(session, user_id, filtros):
    consulta = (
        select(func.sum(Expense.amount_cents))
        .select_from(Expense)
        .where(*construir_condicoes(user_id, filtros))
    )
    return session.scalar(consulta) or 0


def totais_por_categoria(session, user_id, data_inicio, data_fim):
    filtros = {"data_inicio": data_inicio, "data_fim": data_fim}
    consulta = (
        select(Category.name, func.sum(Expense.amount_cents), func.count(Expense.id))
        .select_from(Expense)
        .join(Category, Expense.category_id == Category.id, isouter=True)
        .where(*construir_condicoes(user_id, filtros))
        .group_by(Category.name)
        .order_by(func.sum(Expense.amount_cents).desc())
    )

    totais = []
    for nome, total, quantos in session.execute(consulta).all():
        totais.append(
            {
                "category": nome if nome is not None else "Sem categoria",
                "total_cents": total or 0,
                "count": quantos,
            }
        )

    return totais


def totais_por_comerciante(session, user_id, data_inicio, data_fim, limite=5):
    filtros = {"data_inicio": data_inicio, "data_fim": data_fim}
    consulta = (
        select(Expense.merchant, func.sum(Expense.amount_cents), func.count(Expense.id))
        .select_from(Expense)
        .where(*construir_condicoes(user_id, filtros), Expense.merchant.is_not(None))
        .group_by(Expense.merchant)
        .order_by(func.sum(Expense.amount_cents).desc())
        .limit(limite)
    )

    totais = []
    for nome, total, quantos in session.execute(consulta).all():
        totais.append({"merchant": nome, "total_cents": total or 0, "count": quantos})

    return totais


def totais_por_mes(session, user_id, mes_final, quantos_meses):
    meses = ultimos_meses(mes_final, quantos_meses)

    consulta = select(Expense.expense_date, Expense.amount_cents).where(
        Expense.user_id == user_id,
        Expense.expense_date >= primeiro_dia_do_mes(meses[0]),
        Expense.expense_date <= ultimo_dia_do_mes(meses[-1]),
    )

    totais = {}
    for mes in meses:
        totais[mes] = 0

    for data_despesa, valor in session.execute(consulta).all():
        chave = mes_de(data_despesa)
        if chave in totais:
            totais[chave] = totais[chave] + valor

    resultado = []
    for mes in meses:
        resultado.append({"month": mes, "total_cents": totais[mes]})

    return resultado


def resumo_do_mes(session, user_id, mes):
    inicio = primeiro_dia_do_mes(mes)
    fim = ultimo_dia_do_mes(mes)
    anterior = mes_anterior(mes)

    filtros = {"data_inicio": inicio, "data_fim": fim}
    filtros_anterior = {
        "data_inicio": primeiro_dia_do_mes(anterior),
        "data_fim": ultimo_dia_do_mes(anterior),
    }

    return {
        "month": mes,
        "total_cents": somar_despesas(session, user_id, filtros),
        "count": contar_despesas(session, user_id, filtros),
        "previous_month": anterior,
        "previous_total_cents": somar_despesas(session, user_id, filtros_anterior),
        "by_category": totais_por_categoria(session, user_id, inicio, fim),
        "top_merchants": totais_por_comerciante(session, user_id, inicio, fim),
    }


def listar_categorias(session, user_id):
    consulta = (
        select(Category.name)
        .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
        .order_by(Category.name)
    )
    return list(session.scalars(consulta).all())
