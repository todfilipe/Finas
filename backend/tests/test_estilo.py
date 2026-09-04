import os
from pathlib import Path

TRAVESSAO = chr(8212)

PASTAS_A_IGNORAR = [".venv", "__pycache__", ".git", "node_modules", ".ruff_cache", ".pytest_cache"]

EXTENSOES = [".py", ".md", ".toml", ".yml", ".yaml", ".example", ".json", ".ts", ".tsx", ".sql"]

FICHEIROS_A_IGNORAR = ["AGENTS.md"]


def ficheiros_do_projeto():
    raiz = Path(__file__).parent.parent.parent
    ficheiros = []

    for pasta_atual, subpastas, nomes in os.walk(raiz):
        subpastas[:] = [nome for nome in subpastas if nome not in PASTAS_A_IGNORAR]

        for nome in nomes:
            caminho = Path(pasta_atual) / nome
            if caminho.suffix not in EXTENSOES:
                continue
            if caminho.name in FICHEIROS_A_IGNORAR:
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
