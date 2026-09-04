import time


def momentos_recentes(momentos, agora, janela_segundos):
    recentes = []
    for momento in momentos:
        if agora - momento < janela_segundos:
            recentes.append(momento)

    return recentes


def ultrapassou_o_limite(registos, chave, maximo, janela_segundos):
    agora = time.time()
    recentes = momentos_recentes(registos.get(chave, []), agora, janela_segundos)

    if len(recentes) >= maximo:
        registos[chave] = recentes
        return True

    recentes.append(agora)
    registos[chave] = recentes
    return False
