#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registra uma peca aprovada como nova referencia do projeto.

Uso:
    python aprovar.py gerado\\fisiosync_tema_feed_1080x1350.png "o que funcionou"

A peca vai para a pasta referencias e entra no REFERENCIAS.md com a sua
descricao. A partir dai ela e enviada nas proximas geracoes, junto das
outras aprovadas.
"""

import datetime
import os
import shutil
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(PASTA, "referencias")
INDICE = os.path.join(REFS, "REFERENCIAS.md")
LIMITE = 4          # quantas referencias o fluxo mantem ativas


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    origem = sys.argv[1]
    descricao = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.exists(origem):
        print(f"[ERRO] Não achei o arquivo: {origem}")
        return

    os.makedirs(REFS, exist_ok=True)
    existentes = [n for n in os.listdir(REFS)
                  if n.lower().startswith("aprovada_")]
    numero = len(existentes) + 1
    apelido = os.path.splitext(os.path.basename(origem))[0][:40]
    nome = f"aprovada_{numero:02d}_{apelido}.png"
    destino = os.path.join(REFS, nome)

    try:
        from PIL import Image
        im = Image.open(origem).convert("RGB")
        larg = 1080
        im = im.resize((larg, int(im.height * larg / im.width)),
                       Image.LANCZOS)
        im.save(destino, "PNG")
    except Exception:
        shutil.copy(origem, destino)

    with open(INDICE, "a", encoding="utf-8") as f:
        f.write(f"\n---\n\n## {nome}\n\n"
                f"**Aprovada em:** "
                f"{datetime.date.today().strftime('%d/%m/%Y')}\n\n"
                f"**O que funcionou:** {descricao or 'PREENCHER'}\n")

    print(f"Registrada como referência: {nome}")

    ativas = sorted(n for n in os.listdir(REFS)
                    if n.lower().startswith("aprovada_"))
    if len(ativas) > LIMITE:
        print(f"\nAtenção: {len(ativas)} referências na pasta. O fluxo envia "
              f"as 2 primeiras em ordem alfabética.")
        print("Apague as antigas que não representam mais o padrão.")


if __name__ == "__main__":
    main()
