#!/usr/bin/env python3
"""
Conta quadros que "somem e voltam" num video. Sai com codigo 1 se achar.

Um quadro pisca quando ele e diferente dos dois vizinhos, mas os dois
vizinhos sao praticamente iguais entre si: o quadro do meio saiu
quebrado (texto faltando, bloco branco) e o seguinte voltou ao normal.
Movimento de verdade, como a varredura ciano, nao cai nisso: nela os
vizinhos tambem sao diferentes entre si.

Uso: python3 reels/piscadas.py video.mp4
"""
import subprocess
import sys

import numpy as np

L, A = 135, 240


def quadros(video):
    bruto = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={L}:{A}",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(bruto, dtype=np.uint8).reshape(-1, A, L).astype(np.int16)


def main():
    q = quadros(sys.argv[1])
    dif = lambda a, b: float(np.mean(np.abs(q[a] - q[b])))
    ruins = [i for i in range(1, len(q) - 1)
             if dif(i - 1, i) > 3 and dif(i, i + 1) > 3 and dif(i - 1, i + 1) < 0.5]
    parados = sum(1 for i in range(1, len(q)) if dif(i - 1, i) == 0)
    print(f"[piscadas] {len(q)} quadros | parados {parados} | piscadas {len(ruins)}")
    for i in ruins:
        print(f"[piscadas]   quadro {i} ({i / 30:.2f}s) saiu quebrado")
    sys.exit(1 if ruins else 0)


if __name__ == "__main__":
    main()
