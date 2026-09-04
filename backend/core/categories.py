from sqlalchemy import func, select

from core.models import Category, Expense

TIPO_DESPESA = "expense"
TIPO_RECEITA = "income"

TIPOS = [TIPO_DESPESA, TIPO_RECEITA]

CATEGORIAS = [
    "Alimentação",
    "Transporte",
    "Casa",
    "Saúde",
    "Lazer",
    "Tecnologia",
    "Vestuário",
    "Educação",
    "Subscrições",
    "Viagens",
    "Outros",
]

CATEGORIAS_RECEITA = [
    "Salário",
    "Freelance",
    "Investimentos",
    "Reembolsos",
    "Presentes",
    "Outros",
]

NOME_DE_RECURSO = "Outros"

TAMANHO_MAXIMO = 100


def categorias_por_defeito(tipo):
    if tipo == TIPO_RECEITA:
        return CATEGORIAS_RECEITA

    return CATEGORIAS


def garantir_categorias_do_utilizador(session, user_id):
    for tipo in TIPOS:
        ja_tem = session.scalar(
            select(Category).where(Category.user_id == user_id, Category.kind == tipo)
        )
        if ja_tem is not None:
            continue

        for nome in categorias_por_defeito(tipo):
            session.add(Category(user_id=user_id, name=nome, kind=tipo, is_default=True))

    session.commit()


def listar_categorias_do_utilizador(session, user_id, tipo=None):
    condicoes = [Category.user_id == user_id]
    if tipo is not None:
        condicoes.append(Category.kind == tipo)

    consulta = select(Category).where(*condicoes).order_by(Category.kind, Category.name)
    return list(session.scalars(consulta).all())


def procurar_por_nome(session, user_id, nome, tipo=TIPO_DESPESA):
    return session.scalar(
        select(Category).where(
            Category.user_id == user_id,
            Category.kind == tipo,
            func.lower(Category.name) == nome.strip().lower(),
        )
    )


def obter_categoria(session, user_id, categoria_id):
    return session.scalar(
        select(Category).where(Category.id == categoria_id, Category.user_id == user_id)
    )


def categoria_de_recurso(session, user_id, tipo=TIPO_DESPESA):
    categoria = procurar_por_nome(session, user_id, NOME_DE_RECURSO, tipo)
    if categoria is not None:
        return categoria

    categorias = listar_categorias_do_utilizador(session, user_id, tipo)
    if categorias:
        return categorias[0]

    categoria = Category(user_id=user_id, name=NOME_DE_RECURSO, kind=tipo, is_default=True)
    session.add(categoria)
    session.commit()
    return categoria


def contar_despesas_da_categoria(session, user_id, categoria_id):
    consulta = (
        select(func.count())
        .select_from(Expense)
        .where(Expense.user_id == user_id, Expense.category_id == categoria_id)
    )
    return session.scalar(consulta) or 0


def listar_categorias_com_totais(session, user_id, tipo=None):
    totais = {}
    consulta = (
        select(Expense.category_id, func.count(Expense.id), func.sum(Expense.amount_cents))
        .where(Expense.user_id == user_id)
        .group_by(Expense.category_id)
    )
    for categoria_id, quantas, total in session.execute(consulta).all():
        totais[categoria_id] = {"count": quantas, "total_cents": total or 0}

    resultado = []
    for categoria in listar_categorias_do_utilizador(session, user_id, tipo):
        uso = totais.get(categoria.id, {"count": 0, "total_cents": 0})
        resultado.append(
            {
                "id": categoria.id,
                "name": categoria.name,
                "kind": categoria.kind,
                "is_default": categoria.is_default,
                "count": uso["count"],
                "total_cents": uso["total_cents"],
            }
        )

    return resultado


def limpar_nome(nome):
    limpo = " ".join(nome.split())
    if limpo == "":
        return None
    if len(limpo) > TAMANHO_MAXIMO:
        return None

    return limpo


def criar_categoria(session, user_id, nome, tipo=TIPO_DESPESA):
    if tipo not in TIPOS:
        return None, "Tipo invalido"

    limpo = limpar_nome(nome)
    if limpo is None:
        return None, "Escreve um nome entre 1 e 100 caracteres"

    if procurar_por_nome(session, user_id, limpo, tipo) is not None:
        return None, "Já tens uma categoria com esse nome"

    categoria = Category(user_id=user_id, name=limpo, kind=tipo, is_default=False)
    session.add(categoria)
    session.commit()
    return categoria, None


def renomear_categoria(session, user_id, categoria_id, nome):
    categoria = obter_categoria(session, user_id, categoria_id)
    if categoria is None:
        return None, "Categoria nao encontrada"

    limpo = limpar_nome(nome)
    if limpo is None:
        return None, "Escreve um nome entre 1 e 100 caracteres"

    repetida = procurar_por_nome(session, user_id, limpo, categoria.kind)
    if repetida is not None and repetida.id != categoria.id:
        return None, "Já tens uma categoria com esse nome. Se querias juntar as duas, usa mesclar"

    categoria.name = limpo
    session.commit()
    return categoria, None


def mesclar_categorias(session, user_id, origem_id, destino_id):
    origem = obter_categoria(session, user_id, origem_id)
    destino = obter_categoria(session, user_id, destino_id)

    if origem is None or destino is None:
        return None, "Categoria nao encontrada"

    if origem.id == destino.id:
        return None, "Escolhe duas categorias diferentes"

    if origem.kind != destino.kind:
        return None, "Não dá para juntar uma categoria de despesas com uma de receitas"

    despesas = session.scalars(
        select(Expense).where(Expense.user_id == user_id, Expense.category_id == origem.id)
    ).all()
    for despesa in despesas:
        despesa.category_id = destino.id

    session.delete(origem)
    session.commit()
    return destino, None


def apagar_categoria(session, user_id, categoria_id):
    categoria = obter_categoria(session, user_id, categoria_id)
    if categoria is None:
        return False, "Categoria nao encontrada"

    if contar_despesas_da_categoria(session, user_id, categoria.id) > 0:
        return False, "Essa categoria ainda tem movimentos. Mescla-a noutra antes de a apagar"

    session.delete(categoria)
    session.commit()
    return True, None
