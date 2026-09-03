from pathlib import Path

TRAVESSAO = chr(8212)

PASTAS_A_IGNORAR = [".venv", "__pycache__", ".git", "node_modules", ".ruff_cache", ".pytest_cache"]

EXTENSOES = [".py", ".md", ".toml", ".yml", ".yaml", ".example", ".json", ".ts", ".tsx", ".sql"]


def ficheiros_do_projeto():
    raiz = Path(__file__).parent.parent.parent
    ficheiros = []

    for caminho in raiz.rglob("*"):
        if not caminho.is_file():
            continue
        if any(pasta in caminho.parts for pasta in PASTAS_A_IGNORAR):
            continue
        if caminho.suffix not in EXTENSOES:
            continue
        ficheiros.append(caminho)

    return ficheiros


def test_encontra_ficheiros_para_verificar():
    assert len(ficheiros_do_projeto()) > 5


def test_nao_ha_travessoes_no_projeto():
    com_travessao = []

    for caminho in ficheiros_do_projeto():
        texto = caminho.read_text(encoding="utf-8")
        if TRAVESSAO in texto:
            com_travessao.append(str(caminho))

    assert com_travessao == []
