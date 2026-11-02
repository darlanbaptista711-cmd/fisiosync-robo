#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O relogio do robo.

POR QUE ISTO EXISTE

O agendador do GitHub nao cumpre horario, e o padrao medido aqui mostra
onde ele falha:

  31/10  cron 11:55 -> rodou 15:52      (3h57 de atraso)
  31/10  cron 18:25 -> nunca rodou
  01/11  6 crons entre 09:30 e 13:30 -> ZERO dispararam em 5h30
  01/11  6 crons entre 18:20 e 20:40 -> 3 dispararam, 1h a 3h atrasados

O buraco e de dia: 12h as 17h UTC e o pico da fila do GitHub, e e
exatamente onde cai o nosso meio-dia. De madrugada ele dispara.

A SOLUCAO

A largada vem da madrugada, que funciona, e o robo DORME ate a hora
certa. Como um job do GitHub morre em 6 horas, a espera e dividida em
uma corrente de jobs, cada um esperando um trecho:

  aquecer -> dorme ate 06:30         (so espera, nao publica)
  manha   -> dorme ate 12:00         e publica
  tarde   -> dorme ate 18:00         e publica

Uma largada as 01:00 da manha cobre os DOIS posts do dia. Largada mais
tarde entra no meio da corrente e o resto segue igual.

Decide e escreve no $GITHUB_OUTPUT:  publicar=sim|nao
"""

import argparse
import json
import datetime
import os
import sys
import time

import postador as P

# Alvo de cada etapa, em horario de Brasilia, e ate que hora ainda vale
# publicar atrasado. Etapa com limite None so espera, nao publica.
#
# Os alvos sao proximos de proposito: nenhum trecho passa de 4h, bem
# abaixo do teto de 6h que o GitHub impoe a um job. Dividir em mais
# etapas custa nada e evita o job morrer no meio da espera.
ETAPAS = {
    "madrugada": (datetime.time(5, 0), None),
    "manha_cedo": (datetime.time(9, 0), None),
    "manha": (datetime.time(12, 0), 16),      # publica
    "tarde_cedo": (datetime.time(15, 30), None),
    "tarde": (datetime.time(18, 0), 23),      # publica
    # Reels: monta a partir de 19:50 e publica perto das 20:00. A montagem
    # leva uns 6 minutos (narracao, trilha, render conferido quadro a quadro).
    "reels": (datetime.time(19, 50), 23),     # monta e publica
}

# Teto de sono por job. O limite duro do GitHub e 6h; 5h deixa folga
# para o checkout, o pip e a propria publicacao.
TETO = 5 * 3600


def reels_publicado_hoje(hoje):
    """O Reels tem historico proprio: reels/historico-reels.json."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "reels", "historico-reels.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            hist = json.load(f)
    except (FileNotFoundError, ValueError):
        return False
    return any(h.get("data_brasilia") == hoje for h in hist)


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


def dormir_ate(alvo, agora, rotulo):
    """Dorme ate o alvo, respeitando o teto do job. True se chegou la."""
    espera = (alvo - agora).total_seconds()
    if espera <= 0:
        return True
    if espera > TETO:
        print(f"[relogio] {rotulo}: faltam {espera/3600:.1f}h, mais que o "
              f"teto de {TETO/3600:.1f}h deste job. Dormindo o teto e "
              "passando a vez para a proxima etapa.")
        time.sleep(TETO)
        return False
    print(f"[relogio] {rotulo}: dormindo {espera/60:.0f} min ate as "
          f"{alvo:%H:%M}.")
    time.sleep(espera)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", choices=sorted(ETAPAS), required=True)
    args = ap.parse_args()

    hora_alvo, hora_limite = ETAPAS[args.etapa]
    so_espera = hora_limite is None

    if os.environ.get("FORCAR") == "1":
        if so_espera:
            decidir("nao", "disparo manual: pulando as etapas de espera.")
        decidir("sim", "disparo manual: publicando agora, sem esperar.")

    agora = P.agora_brasilia()
    hoje = agora.date()
    alvo = datetime.datetime.combine(hoje, hora_alvo)

    print(f"[relogio] etapa '{args.etapa}', {agora:%d/%m %H:%M} em "
          f"Brasilia, alvo {hora_alvo:%H:%M}.")

    if so_espera:
        dormir_ate(alvo, agora, args.etapa)
        decidir("nao", "espera cumprida. A proxima etapa assume.")

    feitas = janelas_ja_publicadas(hoje.isoformat())
    if args.etapa == "reels" and reels_publicado_hoje(hoje.isoformat()):
        feitas.add("reels")
    if args.etapa in feitas:
        decidir("nao", f"a janela da {args.etapa} de hoje ja foi "
                       "publicada. Saindo sem gerar nada.")

    limite = datetime.datetime.combine(hoje, datetime.time(hora_limite, 59))
    if agora > limite:
        decidir("nao", f"passou das {hora_limite}h e a janela da "
                       f"{args.etapa} nao vale mais hoje.")

    if not dormir_ate(alvo, agora, args.etapa):
        decidir("nao", "o teto do job acabou antes do alvo. A proxima "
                       "largada pega.")

    # relendo: a corrente pode ter levado horas desde o checkout
    depois = P.agora_brasilia().date().isoformat()
    if args.etapa in janelas_ja_publicadas(depois) or (
            args.etapa == "reels" and reels_publicado_hoje(depois)):
        decidir("nao", f"a janela da {args.etapa} saiu enquanto este job "
                       "esperava. Nao vou duplicar.")

    decidir("sim", f"{hora_alvo:%H:%M}. Publicando a janela da "
                   f"{args.etapa}.")


if __name__ == "__main__":
    main()
