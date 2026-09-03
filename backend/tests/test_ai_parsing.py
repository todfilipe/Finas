from datetime import date

from core.ai_parsing import (
    CATEGORIAS,
    FRASES_DE_RECURSO,
    RespostaIA,
    aplicar_limiar_confianca,
    campos_da_correcao,
    construir_despesa_nova,
    converter_data,
    descrever_ultima_despesa,
    falta_valor,
    frase_de_recurso,
    hoje_do_utilizador,
    limitar_ao_dia_de_hoje,
    limpar_moeda,
    montar_prompt,
    normalizar_categoria,
    resolver_data,
)


def test_prompt_tem_categorias_e_data():
    prompt = montar_prompt("Europe/Lisbon", None)
    for categoria in CATEGORIAS:
        assert categoria in prompt
    assert "AAAA-MM-DD" in prompt
    assert "ainda não tem nenhuma despesa" in prompt


def test_prompt_com_ultima_despesa():
    ultima_despesa = {
        "amount_cents": 3000,
        "currency": "EUR",
        "category": "Tecnologia",
        "merchant": "Fnac",
        "date": "2026-09-01",
    }
    prompt = montar_prompt("Europe/Lisbon", ultima_despesa)
    assert "30.00 EUR" in prompt
    assert "Fnac" in prompt
    assert "e_correcao" in prompt


def test_descrever_sem_despesa():
    assert "ainda não tem" in descrever_ultima_despesa(None)


def test_resposta_ia_aceita_campos_nulos():
    resposta = RespostaIA(
        e_despesa=False,
        e_correcao=False,
        amount_cents=None,
        currency=None,
        category=None,
        subcategory=None,
        merchant=None,
        description=None,
        date=None,
        payment_method=None,
        confidence=None,
        needs_confirmation=False,
        resposta="Bom dia!",
    )
    assert resposta.e_despesa is False
    assert resposta.resposta == "Bom dia!"


def fazer_resposta(**campos):
    base = {
        "e_despesa": True,
        "e_correcao": False,
        "amount_cents": 3000,
        "currency": "EUR",
        "category": "Tecnologia",
        "subcategory": None,
        "merchant": "Fnac",
        "description": None,
        "date": "2026-09-03",
        "payment_method": None,
        "confidence": 0.9,
        "needs_confirmation": False,
        "resposta": "Anotado!",
    }
    base.update(campos)
    return RespostaIA(**base)


def test_categoria_invalida_vira_outros():
    resultado = normalizar_categoria(fazer_resposta(category="Ginásio"))
    assert resultado.category == "Outros"


def test_despesa_nova_sem_categoria_vira_outros():
    resultado = normalizar_categoria(fazer_resposta(category=None))
    assert resultado.category == "Outros"


def test_correcao_sem_categoria_fica_a_null():
    resultado = normalizar_categoria(fazer_resposta(e_correcao=True, category=None))
    assert resultado.category is None


def test_nao_despesa_fica_a_null():
    resultado = normalizar_categoria(fazer_resposta(e_despesa=False, category=None))
    assert resultado.category is None


def test_converter_data_valida():
    assert converter_data("2026-09-03") == date(2026, 9, 3)


def test_converter_data_invalida_ou_vazia():
    assert converter_data("ontem") is None
    assert converter_data(None) is None


def test_limpar_moeda():
    assert limpar_moeda("usd") == "USD"
    assert limpar_moeda(None) == "EUR"
    assert limpar_moeda("euros") == "EUR"


def test_confianca_baixa_pede_confirmacao():
    resultado = aplicar_limiar_confianca(fazer_resposta(confidence=0.4))
    assert resultado.needs_confirmation is True


def test_confianca_alta_nao_mexe():
    resultado = aplicar_limiar_confianca(fazer_resposta(confidence=0.9))
    assert resultado.needs_confirmation is False


def test_falta_valor():
    assert falta_valor(fazer_resposta(amount_cents=None)) is True
    assert falta_valor(fazer_resposta(amount_cents=0)) is True
    assert falta_valor(fazer_resposta(amount_cents=3000)) is False
    assert falta_valor(fazer_resposta(e_despesa=False, amount_cents=None)) is False
    assert falta_valor(fazer_resposta(e_correcao=True, amount_cents=None)) is False


def test_construir_despesa_nova():
    despesa = construir_despesa_nova(fazer_resposta())
    assert despesa.amount_cents == 3000
    assert despesa.currency == "EUR"
    assert despesa.category == "Tecnologia"
    assert despesa.expense_date == date(2026, 9, 3)


def test_construir_despesa_nova_sem_data_usa_hoje():
    despesa = construir_despesa_nova(fazer_resposta(date=None), "Europe/Lisbon")
    assert despesa.expense_date == hoje_do_utilizador("Europe/Lisbon")


def test_construir_despesa_nova_devolve_none_quando_falta_valor():
    assert construir_despesa_nova(fazer_resposta(amount_cents=None)) is None
    assert construir_despesa_nova(fazer_resposta(e_despesa=False)) is None
    assert construir_despesa_nova(fazer_resposta(e_correcao=True)) is None


def test_campos_da_correcao_so_traz_o_que_mudou():
    resultado = fazer_resposta(
        e_correcao=True,
        amount_cents=None,
        currency=None,
        category="Lazer",
        merchant=None,
        date=None,
    )
    assert campos_da_correcao(resultado) == {"category": "Lazer"}


def test_campos_da_correcao_com_valor_e_data():
    resultado = fazer_resposta(
        e_correcao=True,
        amount_cents=3500,
        currency=None,
        category=None,
        merchant=None,
        date="2026-08-31",
    )
    campos = campos_da_correcao(resultado)
    assert campos == {"amount_cents": 3500, "expense_date": date(2026, 8, 31)}


def test_campos_da_correcao_vazio_se_nao_for_correcao():
    assert campos_da_correcao(fazer_resposta()) == {}


def test_frase_de_recurso_vem_da_lista():
    assert frase_de_recurso() in FRASES_DE_RECURSO


def fazer_resposta(**campos):
    base = {
        "e_despesa": True,
        "e_correcao": False,
        "amount_cents": 3000,
        "currency": "EUR",
        "category": "Tecnologia",
        "subcategory": None,
        "merchant": "Fnac",
        "description": None,
        "date": None,
        "payment_method": None,
        "confidence": 0.9,
        "needs_confirmation": False,
        "resposta": "Anotado!",
    }
    base.update(campos)
    return RespostaIA(**base)


def test_prompt_explica_datas_relativas():
    prompt = montar_prompt("Europe/Lisbon", None)
    assert "ontem" in prompt
    assert "há 3 dias" in prompt
    assert "nunca pode ser no futuro" in prompt
    assert "mês anterior" in prompt


def test_resolver_data_usa_a_data_da_ia():
    assert resolver_data("2026-08-30", "Europe/Lisbon") == date(2026, 8, 30)


def test_resolver_data_sem_data_e_hoje():
    hoje = hoje_do_utilizador("Europe/Lisbon")
    assert resolver_data(None, "Europe/Lisbon") == hoje
    assert resolver_data("", "Europe/Lisbon") == hoje
    assert resolver_data("ontem", "Europe/Lisbon") == hoje


def test_resolver_data_no_futuro_fica_hoje():
    hoje = hoje_do_utilizador("Europe/Lisbon")
    assert resolver_data("2099-01-01", "Europe/Lisbon") == hoje


def test_limitar_ao_dia_de_hoje():
    hoje = hoje_do_utilizador("Europe/Lisbon")
    assert limitar_ao_dia_de_hoje(date(2020, 1, 1), "Europe/Lisbon") == date(2020, 1, 1)
    assert limitar_ao_dia_de_hoje(hoje, "Europe/Lisbon") == hoje
    assert limitar_ao_dia_de_hoje(date(2099, 1, 1), "Europe/Lisbon") == hoje


def test_despesa_nova_com_data_relativa_ja_resolvida():
    despesa = construir_despesa_nova(fazer_resposta(date="2026-08-31"), "Europe/Lisbon")
    assert despesa.expense_date == date(2026, 8, 31)


def test_despesa_nova_sem_data_fica_com_hoje():
    despesa = construir_despesa_nova(fazer_resposta(date=None), "Europe/Lisbon")
    assert despesa.expense_date == hoje_do_utilizador("Europe/Lisbon")


def test_despesa_nova_com_data_no_futuro_fica_com_hoje():
    despesa = construir_despesa_nova(fazer_resposta(date="2099-05-05"), "Europe/Lisbon")
    assert despesa.expense_date == hoje_do_utilizador("Europe/Lisbon")


def test_correcao_com_data_no_futuro_fica_com_hoje():
    resultado = fazer_resposta(e_correcao=True, date="2099-05-05")
    campos = campos_da_correcao(resultado, "Europe/Lisbon")
    assert campos["expense_date"] == hoje_do_utilizador("Europe/Lisbon")


def test_correcao_sem_data_nao_mexe_na_data():
    campos = campos_da_correcao(fazer_resposta(e_correcao=True, date=None), "Europe/Lisbon")
    assert "expense_date" not in campos


def test_timezone_do_utilizador_muda_o_hoje():
    lisboa = hoje_do_utilizador("Europe/Lisbon")
    auckland = hoje_do_utilizador("Pacific/Auckland")
    assert (auckland - lisboa).days in [0, 1]


def test_lista_de_categorias_por_defeito():
    assert CATEGORIAS == [
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


def test_categoria_invalida_da_ia_vira_outros():
    resultado = normalizar_categoria(fazer_resposta(category="Ginásio"))
    assert resultado.category == "Outros"


def test_categoria_valida_da_ia_mantem_se():
    resultado = normalizar_categoria(fazer_resposta(category="Lazer"))
    assert resultado.category == "Lazer"


def test_nao_ha_travessoes_nas_frases_de_recurso():
    for frase in FRASES_DE_RECURSO:
        assert chr(8212) not in frase


def test_prompt_nao_tem_travessoes():
    assert chr(8212) not in montar_prompt("Europe/Lisbon", None)


def test_prompt_proibe_travessoes_a_ia():
    assert "travessões" in montar_prompt("Europe/Lisbon", None)
