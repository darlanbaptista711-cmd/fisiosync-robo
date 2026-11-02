#!/usr/bin/env python3
"""
Escolhe o proximo Reels da fila e copia para reels/roteiro-hoje.json.

A fila e reels/fila/NN-*.json, em ordem. Pula o que ja esta em
reels/historico-reels.json. So entra roteiro com fato E fonte: tema sem
fato conferido nunca vira video (regra em reels/temas/REGRAS.md).

Saida:
  0  roteiro escolhido
  3  fila vazia: hora de conferir fatos novos
"""
import glob
import json
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILA = os.path.join(RAIZ, "reels", "fila")
HIST = os.path.join(RAIZ, "reels", "historico-reels.json")
HOJE = os.path.join(RAIZ, "reels", "roteiro-hoje.json")
AVISAR_COM = 6   # roteiros restantes que ja merecem aviso (3 dias a 2 por dia)


def main():
    try:
        feitos = {h.get("titulo") for h in json.load(open(HIST, encoding="utf-8"))}
    except (FileNotFoundError, json.JSONDecodeError):
        feitos = set()

    prontos = []
    for caminho in sorted(glob.glob(os.path.join(FILA, "*.json"))):
        r = json.load(open(caminho, encoding="utf-8"))
        if r.get("titulo") in feitos:
            continue
        if not (r.get("fato") and r.get("fonte")):
            print(f"[proximo] pulando {os.path.basename(caminho)}: sem fato ou fonte")
            continue
        prontos.append(caminho)

    if not prontos:
        print("[proximo] FILA VAZIA: nenhum roteiro conferido sobrando.")
        sys.exit(3)

    escolhido = prontos[0]
    shutil.copyfile(escolhido, HOJE)
    nome = os.path.splitext(os.path.basename(escolhido))[0]
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
        f.write(f"nome={nome}\n")
    print(f"[proximo] hoje: {os.path.basename(escolhido)}")
    print(f"[proximo] restam {len(prontos) - 1} roteiros prontos depois deste")
    if len(prontos) - 1 < AVISAR_COM:
        print(f"[proximo] AVISO: menos de {AVISAR_COM} dias de fila.")
        with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
            f.write("fila_baixa=sim\n")


if __name__ == "__main__":
    main()
