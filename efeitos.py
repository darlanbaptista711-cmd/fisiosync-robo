#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Efeitos discretos em ciano, desenhados ATRAS da ilustracao.

Para a forma organica aparecer por tras do objeto, a ilustracao precisa
ser colada com o fundo branco transparente. Quem faz isso e a funcao
mascara_sem_fundo, aqui embaixo.

Regra: escolher dois ou tres recursos que conversem com o tema. Nunca
aplicar todos, nunca atravessar texto, logo ou selos.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

CIANO = (24, 183, 216)


# --------------------------------------------------------------------------
# Fundo transparente na ilustracao
# --------------------------------------------------------------------------

def mascara_sem_fundo(img, tolerancia=52, suave=2):
    """
    Devolve a ilustracao em RGBA com o fundo transparente.

    Nao usa limiar simples: o gerador entrega um fundo com degrade leve,
    e qualquer limiar fixo deixa um RETANGULO claro visivel por tras do
    objeto. Aqui o fundo e removido por preenchimento a partir das
    quatro bordas, entao so sai o que esta ligado a borda. O objeto
    fica inteiro, mesmo tendo partes claras.
    """
    base = img.convert("RGB")
    larg, alt = base.size

    marca = (255, 0, 255)
    trabalho = base.copy()
    cantos = [(1, 1), (larg - 2, 1), (1, alt - 2), (larg - 2, alt - 2),
              (larg // 2, 1), (larg // 2, alt - 2),
              (1, alt // 2), (larg - 2, alt // 2)]
    for ponto in cantos:
        if trabalho.getpixel(ponto) == marca:
            continue
        try:
            ImageDraw.floodfill(trabalho, ponto, marca, thresh=tolerancia)
        except Exception:
            pass

    tp = trabalho.load()
    alfa = Image.new("L", base.size, 255)
    ap = alfa.load()
    for y in range(alt):
        for x in range(larg):
            if tp[x, y] == marca:
                ap[x, y] = 0
    if suave:
        alfa = alfa.filter(ImageFilter.GaussianBlur(suave))
        ap = alfa.load()
        for y in range(alt):            # recupera o miolo do objeto
            for x in range(larg):
                if ap[x, y] > 128:
                    ap[x, y] = 255

    saida = base.convert("RGBA")
    saida.putalpha(alfa)
    return saida


# --------------------------------------------------------------------------
# Recursos
# --------------------------------------------------------------------------

def forma_organica(peca, caixa, forca=0.30, semente=0):
    """Mancha suave em ciano muito claro, dissolvendo no branco."""
    x0, y0, x1, y1 = [int(v) for v in caixa]
    larg, alt = x1 - x0, y1 - y0
    if larg < 10 or alt < 10:
        return
    rnd = random.Random(semente)
    camada = Image.new("L", (larg, alt), 0)
    d = ImageDraw.Draw(camada)

    # a mancha precisa caber FOLGADA na caixa: se encostar na borda,
    # o desfoque e cortado e ela vira um retangulo
    cx, cy = larg / 2, alt / 2
    rx, ry = larg * 0.36, alt * 0.34
    pontos = []
    for i in range(14):
        ang = 2 * math.pi * i / 14
        v = 1 + rnd.uniform(-0.16, 0.16)
        pontos.append((cx + math.cos(ang) * rx * v,
                       cy + math.sin(ang) * ry * v))
    d.polygon(pontos, fill=int(255 * forca))
    camada = camada.filter(ImageFilter.GaussianBlur(min(larg, alt) * 0.17))

    cor = Image.new("RGB", (larg, alt), CIANO)
    peca.paste(cor, (x0, y0), camada)


def ondas(peca, centro, raio, quantas=3, forca=0.5, abertura=70,
          direcao=0, espessura=None):
    """
    Arcos finos em ciano, como ondas saindo de um ponto.
    Use so quando o tema tiver relacao com som ou emissao.
    """
    cx, cy = [int(v) for v in centro]
    camada = Image.new("L", peca.size, 0)
    d = ImageDraw.Draw(camada)
    esp = espessura or max(2, int(raio * 0.012))
    for i in range(quantas):
        r = int(raio * (0.62 + 0.19 * i))
        alfa = int(255 * forca * (1 - i * 0.22))
        d.arc([cx - r, cy - r, cx + r, cy + r],
              direcao - abertura / 2, direcao + abertura / 2,
              fill=alfa, width=esp)
    camada = camada.filter(ImageFilter.GaussianBlur(esp * 0.5))
    cor = Image.new("RGB", peca.size, CIANO)
    peca.paste(cor, (0, 0), camada)


def brilho_radial(peca, centro, raio, forca=0.10):
    """Halo muito suave sob o objeto, para dar profundidade."""
    cx, cy = [int(v) for v in centro]
    r = int(raio)
    camada = Image.new("L", peca.size, 0)
    ImageDraw.Draw(camada).ellipse([cx - r, cy - r, cx + r, cy + r],
                                   fill=int(255 * forca))
    camada = camada.filter(ImageFilter.GaussianBlur(r * 0.45))
    cor = Image.new("RGB", peca.size, CIANO)
    peca.paste(cor, (0, 0), camada)


def linha_curva(peca, caixa, forca=0.30, espessura=None, altura=0.25):
    """Curva fina atravessando a area da ilustracao."""
    x0, y0, x1, y1 = [int(v) for v in caixa]
    larg = x1 - x0
    esp = espessura or max(2, int(larg * 0.004))
    camada = Image.new("L", peca.size, 0)
    d = ImageDraw.Draw(camada)
    meio = (y0 + y1) / 2
    amp = (y1 - y0) * altura
    pontos = [(x0 + larg * t / 60,
               meio + math.sin(t / 60 * math.pi * 1.4) * amp)
              for t in range(61)]
    d.line(pontos, fill=int(255 * forca), width=esp, joint="curve")
    camada = camada.filter(ImageFilter.GaussianBlur(esp * 0.6))
    cor = Image.new("RGB", peca.size, CIANO)
    peca.paste(cor, (0, 0), camada)


# --------------------------------------------------------------------------
# Escolha por tema
# --------------------------------------------------------------------------

PALAVRAS_SOM = ("audio", "áudio", "voz", "fala", "som", "grava", "ditar",
                "transcri", "escuta")


def aplicar(peca, caixa, tema="", conceito="", semente=0):
    """
    Desenha dois ou tres recursos coerentes com o tema, dentro da caixa
    da ilustracao. Chamar ANTES de colar a ilustracao.
    """
    x0, y0, x1, y1 = [int(v) for v in caixa]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    texto = f"{tema} {conceito}".lower()
    usados = []

    # 1. a mancha organica entra sempre: e ela que integra o objeto
    forma_organica(peca, (x0, y0, x1, y1), semente=semente)
    usados.append("forma orgânica")

    # 2. halo de profundidade sob o objeto
    brilho_radial(peca, (cx, cy + (y1 - y0) * 0.26), (x1 - x0) * 0.34,
                  forca=0.13)
    usados.append("halo de profundidade")

    # 3. o terceiro recurso depende do assunto
    if any(p in texto for p in PALAVRAS_SOM):
        larg = x1 - x0
        ondas(peca, (x0 + larg * 0.30, y0 + (y1 - y0) * 0.34), larg * 0.34,
              quantas=3, forca=0.75, direcao=180, abertura=96)
        usados.append("ondas sonoras")
    else:
        linha_curva(peca, (x0, y0, x1, y1), forca=0.22)
        usados.append("linha curva")

    return usados
