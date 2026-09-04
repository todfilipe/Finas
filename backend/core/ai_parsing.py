import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

from openai import OpenAI
from pydantic import BaseModel, Field

from core.categories import (
    CATEGORIAS,
    NOME_DE_RECURSO,
    CATEGORIAS_RECEITA,
    TIPO_DESPESA,
    TIPO_RECEITA,
    TIPOS,
)
from core.config import DEFAULT_CURRENCY, DEFAULT_TIMEZONE, OPENAI_API_KEY, OPENAI_MODEL

LIMIAR_CONFIANCA = 0.6

MAX_DESPESAS = 5

FRASES_DE_RECURSO = [
    "Não apanhei bem essa. Dizes outra vez?",
    "Hmm, não percebi. Podes escrever de outra forma?",
    "Essa fugiu-me 😅 repete lá?",
    "Não consegui tirar daí uma despesa. Diz-me o valor e onde foi?",
]


class DespesaDaIA(BaseModel):
    kind: str
    amount_cents: int | None
    currency: str | None
    category: str | None
    subcategory: str | None
    merchant: str | None
    description: str | None
    date: str | None
    payment_method: str | None
    confidence: float | None
    needs_confirmation: bool


class RespostaIA(BaseModel):
    e_despesa: bool
    e_correcao: bool
    despesas: list[DespesaDaIA]
    resposta: str


class DespesaNova(BaseModel):
    kind: str
    amount_cents: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category: str
    subcategory: str | None
    merchant: str | None
    description: str | None
    expense_date: date
    payment_method: str | None
    confidence: float | None
    needs_confirmation: bool


def descrever_uma_despesa(despesa):
    valor = despesa.get("amount_cents", 0) / 100
    return (
        f"- {valor:.2f} {despesa.get('currency', DEFAULT_CURRENCY)}"
        f", categoria {despesa.get('category')}"
        f", comerciante {despesa.get('merchant')}"
        f", data {despesa.get('date')}"
    )


def descrever_ultimas_despesas(ultimas_despesas):
    if not ultimas_despesas:
        return "O utilizador ainda não tem nenhuma despesa registada."

    linhas = []
    for despesa in ultimas_despesas:
        linhas.append(descrever_uma_despesa(despesa))

    if len(linhas) == 1:
        titulo = "Última despesa registada por este utilizador:"
        fim = "Se a mensagem nova for uma correção a esta despesa, marca e_correcao a true."
    else:
        titulo = "Últimas despesas registadas por este utilizador, todas da mesma mensagem:"
        fim = (
            "Se a mensagem nova for uma correção a alguma destas, marca e_correcao a true."
            " Não tentes adivinhar a qual, é o bot que pergunta ao utilizador."
        )

    return titulo + "\n" + "\n".join(linhas) + "\n" + fim


def nome_de_recurso(lista_de_categorias):
    if "Outros" in lista_de_categorias:
        return "Outros"

    return lista_de_categorias[0]


def categorias_do_tipo(despesas, receitas, tipo):
    if tipo == TIPO_RECEITA:
        return receitas or CATEGORIAS_RECEITA

    return despesas or CATEGORIAS


def montar_prompt(
    timezone_utilizador,
    ultimas_despesas,
    lista_de_categorias=None,
    lista_de_categorias_receita=None,
):
    de_despesa = categorias_do_tipo(lista_de_categorias, None, TIPO_DESPESA)
    de_receita = categorias_do_tipo(None, lista_de_categorias_receita, TIPO_RECEITA)

    agora = datetime.now(ZoneInfo(timezone_utilizador))
    categorias = ", ".join(de_despesa)
    categorias_receita = ", ".join(de_receita)
    recurso = nome_de_recurso(de_despesa)
    recurso_receita = nome_de_recurso(de_receita)

    return f"""És o Finas, um bot de Telegram que ajuda a anotar despesas pessoais.

Recebes uma mensagem escrita em português de Portugal, informal, e devolves sempre um JSON com os campos do schema.

Data e hora atuais do utilizador: {agora.strftime("%Y-%m-%d %H:%M")} ({timezone_utilizador}).
Usa esta data para resolver expressões como "hoje", "ontem", "anteontem", "há 3 dias", "na sexta passada", "no dia 15".
O campo date é sempre uma data absoluta no formato AAAA-MM-DD.

Regras para a data:
- Se não disserem nada sobre a data, foi hoje.
- Se falarem de um dia do mês que ainda não chegou (ex: "no dia 15" e hoje é dia 3), foi no mês anterior.
- Se falarem de um dia da semana (ex: "na segunda"), foi o mais recente que já passou.
- A data nunca pode ser no futuro. Se não perceberes a data, usa o dia de hoje.

Cada movimento tem um campo kind:
- "expense" quando é dinheiro que saiu: gastei, paguei, comprei, custou, gastámos.
- "income" quando é dinheiro que entrou: recebi, ganhei, entrou, caiu, pagaram-me, o salário, um reembolso, uma devolução, um presente em dinheiro.
- Na dúvida, é uma despesa.

Categorias válidas para despesas (kind expense): {categorias}
Categorias válidas para receitas (kind income): {categorias_receita}
O campo category tem de ser exatamente uma da lista do respetivo kind.

O campo despesas é uma lista:
- Se a mensagem não for uma despesa, a lista vem vazia.
- Se a mensagem tiver uma despesa, a lista leva um item.
- Se a mensagem tiver várias despesas, a lista leva um item por cada uma, pela ordem em que aparecem na frase.
- Se for uma correção à última despesa, a lista leva um item só, com os campos que mudam preenchidos e os restantes a null.
- No máximo {MAX_DESPESAS} despesas por mensagem. Se a pessoa disser mais do que isso, anota as primeiras {MAX_DESPESAS} e avisa no resposta que as outras ficaram de fora.

Regras:
- Valores sempre em cêntimos, inteiros (30 euros são 3000).
- Se não disserem a moeda, assume {DEFAULT_CURRENCY}.
- Se a mensagem não for uma despesa (um bom dia, uma pergunta, conversa), e_despesa é false, a lista despesas vem vazia e o resposta é só uma reação curta e natural.
- Se a mensagem for uma correção à última despesa registada, e_correcao é true.
- Cada despesa é independente: se só disserem o sítio de uma delas, não copies o comerciante de uma para a outra.
- Se a data valer para todas ("ontem gastei 10 no café e 20 no almoço"), repete a mesma data em todas.
- Se não houver pista nenhuma sobre a categoria, usa "{recurso}" nas despesas e "{recurso_receita}" nas receitas, com needs_confirmation a true.
- Se a confiança for baixa (confidence abaixo de 0.6), needs_confirmation é true e o resposta vem em forma de pergunta.
- Se não conseguires identificar um valor, deixa essa despesa de fora da lista. Se ficares sem nenhuma, e_despesa é false e o resposta pede para reformular, sem falar de erros técnicos.

Tom do campo resposta:
- PT-PT informal, como um amigo a responder por mensagem, nunca como um recibo, um formulário ou um call center.
- Frases curtas. Emojis com moderação, só onde dão calor à mensagem.
- Nunca uses travessões (o traço longo) nas frases. Usa vírgulas, dois pontos ou pontos finais.
- Confirma sempre o valor e a categoria, mas dito de forma natural.
- Nunca julgues nem comentes os hábitos de gasto do utilizador.
- Varia sempre a forma de confirmar, nunca repitas a mesma frase duas vezes seguidas.

Exemplos de confirmação (varia entre estas e outras parecidas):
- "Anotado! 30€ na Fnac, categoria Tecnologia."
- "Boa, já tenho isso guardado: 30 paus na Fnac 👍"
- "Registei: 30€, Fnac (Tecnologia)."
- "Tá guardado! Fnac, 30€."

Exemplo de receita:
- Utilizador: "recebi o ordenado, 1200"
- Resposta: "Boa! 1200€ de salário anotados 🙌"

Exemplos com várias despesas (confirma as duas, sem parecer uma lista de compras):
- "Anotado! 10€ no café e 20€ no almoço, as duas em Alimentação."
- "Boa, guardei as duas: 10 paus no café e 20 no almoço 👍"

Exemplo de correção:
- Utilizador: "não foi na fnac, foi no continente"
- Resposta: "Ah, faz sentido! Corrigido: Continente (Alimentação), 30€."

{descrever_ultimas_despesas(ultimas_despesas)}"""


def normalizar_categoria(resultado, lista_de_categorias=None, lista_de_categorias_receita=None):
    for despesa in resultado.despesas:
        if despesa.kind not in TIPOS:
            despesa.kind = TIPO_DESPESA

        validas = categorias_do_tipo(lista_de_categorias, lista_de_categorias_receita, despesa.kind)
        recurso = nome_de_recurso(validas)

        if despesa.category is not None and despesa.category not in validas:
            despesa.category = recurso

        if resultado.e_despesa and not resultado.e_correcao and despesa.category is None:
            despesa.category = recurso

    return resultado


def parse_mensagem(
    texto,
    timezone_utilizador=DEFAULT_TIMEZONE,
    ultimas_despesas=None,
    lista_de_categorias=None,
    lista_de_categorias_receita=None,
):
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY no .env")

    prompt = montar_prompt(
        timezone_utilizador,
        ultimas_despesas,
        lista_de_categorias,
        lista_de_categorias_receita,
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto},
        ],
        response_format=RespostaIA,
    )

    resultado = completion.choices[0].message.parsed
    if resultado is None:
        raise RuntimeError("A IA não devolveu um JSON válido")

    normalizado = normalizar_categoria(resultado, lista_de_categorias, lista_de_categorias_receita)
    return aplicar_limiar_confianca(normalizado)


def converter_data(texto_data):
    if not texto_data:
        return None

    try:
        return date.fromisoformat(texto_data)
    except ValueError:
        return None


def hoje_do_utilizador(timezone_utilizador):
    return datetime.now(ZoneInfo(timezone_utilizador)).date()


def limitar_ao_dia_de_hoje(data, timezone_utilizador):
    hoje = hoje_do_utilizador(timezone_utilizador)
    if data > hoje:
        return hoje

    return data


def resolver_data(texto_data, timezone_utilizador):
    data = converter_data(texto_data)
    if data is None:
        return hoje_do_utilizador(timezone_utilizador)

    return limitar_ao_dia_de_hoje(data, timezone_utilizador)


def limpar_moeda(currency):
    if not currency or len(currency) != 3:
        return DEFAULT_CURRENCY

    return currency.upper()


def aplicar_limiar_confianca(resultado):
    for despesa in resultado.despesas:
        if despesa.confidence is not None and despesa.confidence < LIMIAR_CONFIANCA:
            despesa.needs_confirmation = True

    return resultado


def falta_valor(despesa):
    return despesa.amount_cents is None or despesa.amount_cents <= 0


def construir_despesas_novas(resultado, timezone_utilizador=DEFAULT_TIMEZONE):
    if not resultado.e_despesa or resultado.e_correcao:
        return []

    novas = []
    for despesa in resultado.despesas[:MAX_DESPESAS]:
        if falta_valor(despesa):
            continue

        novas.append(
            DespesaNova(
                kind=despesa.kind,
                amount_cents=despesa.amount_cents,
                currency=limpar_moeda(despesa.currency),
                category=despesa.category or NOME_DE_RECURSO,
                subcategory=despesa.subcategory,
                merchant=despesa.merchant,
                description=despesa.description,
                expense_date=resolver_data(despesa.date, timezone_utilizador),
                payment_method=despesa.payment_method,
                confidence=despesa.confidence,
                needs_confirmation=despesa.needs_confirmation,
            )
        )

    return novas


def campos_da_correcao(resultado, timezone_utilizador=DEFAULT_TIMEZONE):
    if not resultado.e_correcao or not resultado.despesas:
        return {}

    despesa = resultado.despesas[0]

    campos = {}
    if despesa.amount_cents is not None and despesa.amount_cents > 0:
        campos["amount_cents"] = despesa.amount_cents
    if despesa.currency is not None:
        campos["currency"] = limpar_moeda(despesa.currency)
    if despesa.category is not None:
        campos["category"] = despesa.category
    if despesa.subcategory is not None:
        campos["subcategory"] = despesa.subcategory
    if despesa.merchant is not None:
        campos["merchant"] = despesa.merchant
    if despesa.description is not None:
        campos["description"] = despesa.description
    if despesa.payment_method is not None:
        campos["payment_method"] = despesa.payment_method

    data = converter_data(despesa.date)
    if data is not None:
        campos["expense_date"] = limitar_ao_dia_de_hoje(data, timezone_utilizador)

    return campos


def frase_de_recurso():
    return random.choice(FRASES_DE_RECURSO)
