import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

from openai import OpenAI
from pydantic import BaseModel, Field

from core.config import DEFAULT_CURRENCY, DEFAULT_TIMEZONE, OPENAI_API_KEY, OPENAI_MODEL

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

LIMIAR_CONFIANCA = 0.6

FRASES_DE_RECURSO = [
    "Não apanhei bem essa. Dizes outra vez?",
    "Hmm, não percebi. Podes escrever de outra forma?",
    "Essa fugiu-me 😅 repete lá?",
    "Não consegui tirar daí uma despesa. Diz-me o valor e onde foi?",
]


class RespostaIA(BaseModel):
    e_despesa: bool
    e_correcao: bool
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
    resposta: str


class DespesaNova(BaseModel):
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


def descrever_ultima_despesa(ultima_despesa):
    if not ultima_despesa:
        return "O utilizador ainda não tem nenhuma despesa registada."

    valor = ultima_despesa.get("amount_cents", 0) / 100
    return (
        "Última despesa registada por este utilizador:\n"
        f"- valor: {valor:.2f} {ultima_despesa.get('currency', DEFAULT_CURRENCY)}\n"
        f"- categoria: {ultima_despesa.get('category')}\n"
        f"- comerciante: {ultima_despesa.get('merchant')}\n"
        f"- data: {ultima_despesa.get('date')}\n"
        "Se a mensagem nova for uma correção a esta despesa, marca e_correcao a true."
    )


def montar_prompt(timezone_utilizador, ultima_despesa):
    agora = datetime.now(ZoneInfo(timezone_utilizador))
    categorias = ", ".join(CATEGORIAS)

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

Categorias válidas (o campo category tem de ser exatamente uma destas): {categorias}

Regras:
- Valores sempre em cêntimos, inteiros (30 euros são 3000).
- Se não disserem a moeda, assume {DEFAULT_CURRENCY}.
- Se a mensagem não for uma despesa (um bom dia, uma pergunta, conversa), e_despesa é false, todos os campos da despesa ficam a null e o resposta é só uma reação curta e natural.
- Se a mensagem for uma correção à última despesa registada, e_correcao é true e preenches só os campos que mudam, os restantes ficam a null.
- Se não houver pista nenhuma sobre a categoria, usa "Outros" e needs_confirmation a true.
- Se a confiança for baixa (confidence abaixo de 0.6), needs_confirmation é true e o resposta vem em forma de pergunta.
- Se não conseguires identificar um valor, e_despesa é false e o resposta pede para reformular, sem falar de erros técnicos.
- Se a mensagem tiver mais do que uma despesa, anota só a primeira e avisa no resposta que por agora só consegues anotar uma de cada vez.

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

Exemplo de correção:
- Utilizador: "não foi na fnac, foi no continente"
- Resposta: "Ah, faz sentido! Corrigido: Continente (Alimentação), 30€."

{descrever_ultima_despesa(ultima_despesa)}"""


def normalizar_categoria(resultado):
    if resultado.category is not None and resultado.category not in CATEGORIAS:
        resultado.category = "Outros"

    if resultado.e_despesa and not resultado.e_correcao and resultado.category is None:
        resultado.category = "Outros"

    return resultado


def parse_mensagem(texto, timezone_utilizador=DEFAULT_TIMEZONE, ultima_despesa=None):
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY no .env")

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": montar_prompt(timezone_utilizador, ultima_despesa)},
            {"role": "user", "content": texto},
        ],
        response_format=RespostaIA,
    )

    resultado = completion.choices[0].message.parsed
    if resultado is None:
        raise RuntimeError("A IA não devolveu um JSON válido")

    return aplicar_limiar_confianca(normalizar_categoria(resultado))


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
    if resultado.confidence is not None and resultado.confidence < LIMIAR_CONFIANCA:
        resultado.needs_confirmation = True

    return resultado


def falta_valor(resultado):
    if not resultado.e_despesa or resultado.e_correcao:
        return False

    return resultado.amount_cents is None or resultado.amount_cents <= 0


def construir_despesa_nova(resultado, timezone_utilizador=DEFAULT_TIMEZONE):
    if not resultado.e_despesa or resultado.e_correcao:
        return None

    if falta_valor(resultado):
        return None

    return DespesaNova(
        amount_cents=resultado.amount_cents,
        currency=limpar_moeda(resultado.currency),
        category=resultado.category or "Outros",
        subcategory=resultado.subcategory,
        merchant=resultado.merchant,
        description=resultado.description,
        expense_date=resolver_data(resultado.date, timezone_utilizador),
        payment_method=resultado.payment_method,
        confidence=resultado.confidence,
        needs_confirmation=resultado.needs_confirmation,
    )


def campos_da_correcao(resultado, timezone_utilizador=DEFAULT_TIMEZONE):
    if not resultado.e_correcao:
        return {}

    campos = {}
    if resultado.amount_cents is not None and resultado.amount_cents > 0:
        campos["amount_cents"] = resultado.amount_cents
    if resultado.currency is not None:
        campos["currency"] = limpar_moeda(resultado.currency)
    if resultado.category is not None:
        campos["category"] = resultado.category
    if resultado.subcategory is not None:
        campos["subcategory"] = resultado.subcategory
    if resultado.merchant is not None:
        campos["merchant"] = resultado.merchant
    if resultado.description is not None:
        campos["description"] = resultado.description
    if resultado.payment_method is not None:
        campos["payment_method"] = resultado.payment_method

    data = converter_data(resultado.date)
    if data is not None:
        campos["expense_date"] = limitar_ao_dia_de_hoje(data, timezone_utilizador)

    return campos


def frase_de_recurso():
    return random.choice(FRASES_DE_RECURSO)
