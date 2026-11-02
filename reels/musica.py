#!/usr/bin/env python3
"""
Trilha e efeitos sonoros dos Reels, gerados por codigo.

POR QUE GERAR E NAO BAIXAR UMA MUSICA

Musica de terceiro em Reel de empresa e problema: o Instagram silencia
ou derruba, e o uso comercial exige licenca. Gerando aqui, a trilha e
nossa por construcao: sem direito autoral, sem licenca, sem custo, e
sempre do tamanho exato do video.

O que sai, em remotion/public/audio/:
  musica.mp3   batida pop animada, 124 BPM, do tamanho do video
  whoosh.mp3   passagem de ar, para as transicoes
  pop.mp3      estalo curto, para o numero e a chamada

Le a duracao em remotion/public/dados-reel.json, que o narrar.mjs grava.
"""

import json
import os
import subprocess

import numpy as np
from scipy.signal import butter, lfilter

TAXA = 44100
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(RAIZ, "remotion", "public")
SAIDA = os.path.join(PUB, "audio")

BPM = 124
BATIDA = 60 / BPM
RNG = np.random.default_rng(7)   # semente fixa: mesma trilha toda vez


def t_de(seg):
    return np.arange(int(seg * TAXA)) / TAXA


def passa_baixa(x, corte, ordem=2):
    b, a = butter(ordem, corte / (TAXA / 2), btype="low")
    return lfilter(b, a, x)


def passa_alta(x, corte, ordem=2):
    b, a = butter(ordem, corte / (TAXA / 2), btype="high")
    return lfilter(b, a, x)


def nota(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# ------------------------------ instrumentos ------------------------------

def bumbo():
    t = t_de(0.32)
    freq = 48 + 110 * np.exp(-t * 32)            # queda de tom, o "tum"
    fase = 2 * np.pi * np.cumsum(freq) / TAXA
    return np.sin(fase) * np.exp(-t * 9)


def chimbal():
    t = t_de(0.06)
    ruido = passa_alta(RNG.standard_normal(len(t)), 7000)
    return ruido * np.exp(-t * 70) * 0.35


def palma():
    t = t_de(0.16)
    ruido = passa_alta(RNG.standard_normal(len(t)), 1200)
    env = np.exp(-t * 28) * (1 + 0.6 * (np.sin(t * 2 * np.pi * 90) > 0))
    return ruido * env * 0.42


def dedilhado(freq, dur):
    """Pluck brilhante: fundamental + harmonicos, decaimento rapido."""
    t = t_de(dur)
    s = (np.sin(2 * np.pi * freq * t)
         + 0.45 * np.sin(2 * np.pi * freq * 2 * t)
         + 0.2 * np.sin(2 * np.pi * freq * 3 * t))
    return s * np.exp(-t * 11) * 0.22


def colchao(freqs, dur):
    """Acorde sustentado, macio, por baixo de tudo."""
    t = t_de(dur)
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t)
            for f in freqs)
    ataque = np.minimum(1, t / 0.08)
    return passa_baixa(s * ataque, 2400) * 0.07


def baixo(freq, dur):
    t = t_de(dur)
    s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sign(np.sin(2 * np.pi * freq * t))
    return passa_baixa(s * np.exp(-t * 2.2), 600) * 0.32


def somar(destino, som, inicio):
    i = int(inicio * TAXA)
    if i >= len(destino):
        return
    f = min(len(destino), i + len(som))
    destino[i:f] += som[: f - i]


# --------------------------------- trilha ---------------------------------

def trilha(duracao):
    total = np.zeros(int((duracao + 0.5) * TAXA))
    batidas = int(duracao / BATIDA) + 2

    # I - V - vi - IV em do maior: a progressao mais "pra cima" que existe
    acordes = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    fundamentais = [36, 31, 33, 29]

    kick = bumbo()
    duck = np.ones_like(total)   # sidechain: o resto "respira" com o bumbo

    for b in range(batidas):
        ini = b * BATIDA
        somar(total, kick, ini)
        k0 = int(ini * TAXA)
        janela = np.minimum(1, np.arange(int(0.18 * TAXA)) / (0.18 * TAXA))
        f = min(len(duck), k0 + len(janela))
        duck[k0:f] = np.minimum(duck[k0:f], 0.45 + 0.55 * janela[: f - k0])

        somar(total, chimbal(), ini + BATIDA / 2)
        if b % 2 == 1:
            somar(total, palma(), ini)

    melodico = np.zeros_like(total)
    compasso = 4 * BATIDA
    for c in range(int(duracao / compasso) + 2):
        acorde = acordes[c % 4]
        ini = c * compasso
        somar(melodico, colchao([nota(m) for m in acorde], compasso), ini)
        somar(melodico, baixo(nota(fundamentais[c % 4]), compasso), ini)
        # arpejo em semicolcheias, uma oitava acima
        tons = [nota(m + 12) for m in acorde] + [nota(acorde[0] + 24)]
        for i in range(16):
            somar(melodico, dedilhado(tons[i % 4], BATIDA * 0.9),
                  ini + i * BATIDA / 4)

    total += melodico * duck
    total = total[: int(duracao * TAXA)]

    # entra rapido, sai suave no ultimo segundo
    n = len(total)
    env = np.ones(n)
    env[: int(0.25 * TAXA)] = np.linspace(0, 1, int(0.25 * TAXA))
    fim = int(1.0 * TAXA)
    env[-fim:] = np.linspace(1, 0, fim)
    total *= env
    return total / (np.max(np.abs(total)) + 1e-9) * 0.85


# --------------------------------- efeitos --------------------------------

def whoosh():
    dur = 0.5
    t = t_de(dur)
    ruido = RNG.standard_normal(len(t))
    # filtro que abre e fecha: o ar passando
    saida = np.zeros_like(ruido)
    estado = 0.0
    for i, x in enumerate(ruido):
        corte = 300 + 5200 * np.sin(np.pi * t[i] / dur) ** 2
        alfa = 1 - np.exp(-2 * np.pi * corte / TAXA)
        estado += alfa * (x - estado)
        saida[i] = estado
    env = np.sin(np.pi * t / dur) ** 1.6
    s = saida * env
    return s / (np.max(np.abs(s)) + 1e-9) * 0.7


def pop():
    t = t_de(0.12)
    freq = 700 + 900 * (1 - np.exp(-t * 40))
    fase = 2 * np.pi * np.cumsum(freq) / TAXA
    s = np.sin(fase) * np.exp(-t * 38)
    clique = np.zeros_like(s)
    clique[:40] = np.linspace(1, 0, 40)
    s = s + 0.3 * clique
    return s / (np.max(np.abs(s)) + 1e-9) * 0.8


# ---------------------------------- saida ---------------------------------

def gravar(sinal, nome):
    wav = os.path.join(SAIDA, nome.replace(".mp3", ".wav"))
    mp3 = os.path.join(SAIDA, nome)
    pcm = np.clip(sinal, -1, 1)
    import wave
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes((pcm * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav,
                    "-b:a", "160k", mp3], check=True)
    os.remove(wav)
    print(f"[musica] {nome}: {len(sinal) / TAXA:.1f}s")


def main():
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(PUB, "dados-reel.json"), encoding="utf-8") as f:
        duracao = float(json.load(f)["duracaoTotal"])
    gravar(trilha(duracao), "musica.mp3")
    gravar(whoosh(), "whoosh.mp3")
    gravar(pop(), "pop.mp3")


if __name__ == "__main__":
    main()
