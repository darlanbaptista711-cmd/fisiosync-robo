#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O relogio do robo.

POR QUE ISTO EXISTE

O agendador do GitHub nao cumpre horario. Medido neste repositorio:

  31/10  cron das 11:55 -> rodou 15:52   (3h57 de atraso)
  31/10  cron das 18:25 -> nunca rodou
  01/11  SETE crons entre 11:50 e 13:30 -> nenhum rodou

Ja o workflow_dispatch foi honrado na hora, 4 vezes em 4. Ou seja: o
problema nao e o GitHub estar fora do ar, e a fila de agendamento ser
melhor esforco e ficar no fim da fila.

A SOLUCAO

Parar de pedir ao cron que acerte o minuto. O cron vira so a largada:
dispare a qualquer momento dentro das 2h30 antes do alvo, que este
script DORME ate a hora certa e so entao libera a publicacao. Um cron
que atrasou 40 minutos continua publicando as 12:00 em ponto, porque o
que marca a hora e o sleep, nao o GitHub.

Se o cron atrasar tanto que ja passou do alvo, publica na hora, atrasado
mas publicado. Se nada estiver pendente, encerra em segundos.

Decide e escreve no $GITHUB_OUTPUT:
  publicar=sim|nao
"""

import datetime
import os
import sys
import time

import postador as P

# Alvo de cada janela, em horario de Brasilia.
ALVOS = [
    ("manha", datetime.time(12, 0), 16),
    ("tarde", datetime.time(18, 30), 23),
]

# Quanto tempo o runner aceita ficar dormindo. Acima disso a largada foi
# cedo demais: encerra e deixa para o proximo cron, que vai cair dentro
# da janela. Segura o desperdicio de runner parado.
ESPERA_MAXIMA = 2.5 * 3600


def janelas_ja_publicadas(hoje):
    feitas = set()
    for r in P.ler_historico(limite=40):
        if r.get("status") == "publicado" and r.get("data") == hoje:
            if r.get("janela"):
                feitas.add(r["janela"])
    return feitas


def decidir(valor, motivo):
    print(f"[relogio] {motivo}")
    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a", encoding="utf-8") as f:
            f.write(f"publicar={valor}\n")
    print(f"[relogio] publicar={valor}")
    sys.exit(0)


def main():
    # "Run workflow" no site e ordem direta: publica agora, sem esperar
    # relogio nem janela. Quem clicou quer ver o post sair.
    if os.environ.get("FORCAR") == "1":
        decidir("sim", "disparo manual: publicando agora, sem esperar.")

    agora = P.agora_brasilia()
    hoje = agora.date()
    feitas = janelas_ja_publicadas(hoje.isoformat())
    print(f"[relogio] {agora:%d/%m %H:%M} em Brasilia. "
          f"Janelas ja publicadas hoje: {sorted(feitas) or 'nenhuma'}")

    for nome, hora_alvo, hora_limite in ALVOS:
        if nome in feitas:
            continue

        alvo = datetime.datetime.combine(hoje, hora_alvo)
        limite = datetime.datetime.combine(
            hoje, datetime.time(hora_limite, 59))

        if agora > limite:
            print(f"[relogio] janela da {nome} passou do limite "
                  f"({hora_limite}h). Pulando.")
            continue

        espera = (alvo - agora).total_seconds()

        if espera > ESPERA_MAXIMA:
            decidir("nao", f"largada cedo demais para a {nome}: faltam "
                           f"{espera/3600:.1f}h para as {hora_alvo:%H:%M}. "
                           "O proximo cron pega.")

        if espera > 0:
            print(f"[relogio] janela da {nome} pendente. Dormindo "
                  f"{espera/60:.0f} min ate as {hora_alvo:%H:%M}.")
            time.sleep(espera)
            decidir("sim", f"{hora_alvo:%H:%M} em ponto. Publicando a "
                           f"janela da {nome}.")

        decidir("sim", f"janela da {nome} pendente e o alvo "
                       f"({hora_alvo:%H:%M}) ja passou. Publicando "
                       f"atrasado, que e melhor que nao publicar.")

    decidir("nao", "nenhuma janela pendente. Nada a fazer.")


if __name__ == "__main__":
    main()
