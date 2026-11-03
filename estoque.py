#!/usr/bin/env python3
"""
Quantos dias de conteudo conferido ainda existem.

  feed  : pautas de conhecimento livres (2 por dia), sem as que o
          Reels ja cobriu
  reels : roteiros da fila ainda nao publicados (1 por dia), sem os
          que o feed ja cobriu

Sai com codigo 2 quando algum dos dois tem menos de LIMITE_DIAS: o
workflow abre um aviso (issue), que chega por e-mail.
"""
import glob
import json
import os
import sys

import pautas as PT

LIMITE_DIAS = 10
RAIZ = os.path.dirname(os.path.abspath(__file__))


def main():
    reels_titulos = PT.temas_dos_reels()
    livres = [p for p in PT.carregar()["pautas"]
              if PT._usavel(p) and p.get("status", "livre") == "livre"
              and not PT.assunto_repetido(p["tema"], reels_titulos)]
    dias_feed = len(livres) // 2

    try:
        feitos = {h.get("titulo") for h in json.load(
            open(os.path.join(RAIZ, "reels", "historico-reels.json"), encoding="utf-8"))}
    except (FileNotFoundError, json.JSONDecodeError):
        feitos = set()
    do_feed = PT.temas_do_feed()
    fila = []
    for c in sorted(glob.glob(os.path.join(RAIZ, "reels", "fila", "*.json"))):
        r = json.load(open(c, encoding="utf-8"))
        if r.get("titulo") in feitos or not (r.get("fato") and r.get("fonte")):
            continue
        if r.get("interesse") != "alto":
            continue
        if PT.assunto_repetido(r.get("titulo", ""), do_feed):
            continue
        fila.append(r)
    dias_reels = len(fila)

    linhas = [f"Feed: {len(livres)} pautas conferidas livres = {dias_feed} dias (2 carrosseis/dia)",
              f"Reels: {len(fila)} roteiros conferidos na fila = {dias_reels} dias (1 por dia)"]
    print("\n".join(linhas))
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
        f.write(f"resumo={' | '.join(linhas)}\n")
    if min(dias_feed, dias_reels) < LIMITE_DIAS:
        print(f"ESTOQUE BAIXO: menos de {LIMITE_DIAS} dias.")
        sys.exit(2)


if __name__ == "__main__":
    main()
