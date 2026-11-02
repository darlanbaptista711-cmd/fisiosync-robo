#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slides de texto do carrossel da FisioSync.

O carrossel e o formato que mais gera salvamento: a pessoa le ate o fim
e guarda para consultar. A estrutura e sempre a mesma:

  1. capa       -> a arte normal do molde, sem assinatura, com "arraste"
  2..n-1 texto  -> um passo do fato por slide, letra grande, fundo branco
  n. fechamento -> pedido de salvar/mandar + teste gratis, selos e site

Este modulo desenha os slides 2..n. A capa vem do molde.py.

Mesma regra do resto do robo: texto que nao cabe NAO e cortado. Sobe
TextoNaoCabe e o post nao sai.
"""

import os

from PIL import Image, ImageDraw

import layouts as LY
import marca as M

ESCALA = 2
LARG, ALT = 1080, 1350
MARGEM = 90


def _base():
    e = ESCALA
    peca = Image.new("RGB", (LARG * e, ALT * e), M.BRANCO)
    return peca, ImageDraw.Draw(peca), e


def _cabecalho(peca, d, e, n, total):
    """Logo pequena centralizada e o contador 2/6 no canto."""
    y = LY.logo(peca, 0, int(60 * e), largura_rel=0.24)
    f = M.fonte(True, 24 * e)
    txt = f"{n}/{total}"
    w = d.textlength(txt, font=f)
    x1 = (LARG - MARGEM) * e
    d.text((x1 - w, int(70 * e)), txt, font=f, fill=M.CIANO)
    return y


def _rodape_fonte(d, e, fonte):
    if not fonte:
        return (ALT - 70) * e
    f = M.fonte(False, 22 * e)
    larg = (LARG - 2 * MARGEM) * e
    fo, linhas, _ = LY.caber(d, f"Fonte: {fonte}", larg, 2, False, 22, e,
                             0.80)
    y = (ALT - 70) * e - len(linhas) * int(fo.size * 1.3)
    topo = y
    for linha in linhas:
        w = d.textlength(linha, font=fo)
        d.text(((LARG * e - w) / 2, y), linha, font=fo, fill=(110, 125, 140))
        y += int(fo.size * 1.3)
    return topo


def slide_texto(titulo, texto, n, total, fonte=""):
    peca, d, e = _base()
    topo = _cabecalho(peca, d, e, n, total)
    base = _rodape_fonte(d, e, fonte) - int(40 * e)
    x0 = MARGEM * e
    larg = (LARG - 2 * MARGEM) * e

    # bloco de titulo + texto, centralizado na vertical entre logo e fonte
    ft, lt, _ = LY.caber(d, titulo, larg, 3, True, 70, e, 0.70)
    fb, lb, _ = LY.caber(d, texto, larg, 9, False, 48, e, 0.70)
    alt_t = len(lt) * int(ft.size * 1.15)
    alt_b = len(lb) * int(fb.size * 1.42)
    barra = int(10 * e)
    total_alt = barra + int(36 * e) + alt_t + int(34 * e) + alt_b
    livre = base - topo
    if total_alt > livre:
        raise LY.TextoNaoCabe(f"slide {n}: o texto nao cabe ({titulo})")
    y = topo + (livre - total_alt) / 2

    d.rounded_rectangle([x0, y, x0 + int(110 * e), y + barra],
                        radius=barra // 2, fill=M.CIANO)
    y += barra + int(36 * e)
    for linha in lt:
        d.text((x0, y), linha, font=ft, fill=M.MARINHO)
        y += int(ft.size * 1.15)
    y += int(34 * e)
    for linha in lb:
        d.text((x0, y), linha, font=fb, fill=M.MARINHO)
        y += int(fb.size * 1.42)
    return peca


def slide_final(chamada, n, total):
    """Fechamento: pedido de salvar/mandar e, abaixo, a assinatura."""
    peca, d, e = _base()
    topo = LY.logo(peca, 0, int(150 * e), largura_rel=0.42)
    x0, x1 = MARGEM * e, (LARG - MARGEM) * e
    rodape = LY.assinatura(peca, d, x0, x1, (ALT - 90) * e, e,
                           tratamento="pilula", alinhar="centro")
    larg = x1 - x0
    fc, lc, _ = LY.caber(d, chamada, larg, 4, True, 60, e, 0.70)
    alt = len(lc) * int(fc.size * 1.2)
    y = topo + (rodape - topo - alt) / 2
    for i, linha in enumerate(lc):
        w = d.textlength(linha, font=fc)
        cor = M.CIANO if i == len(lc) - 1 and len(lc) > 1 else M.MARINHO
        d.text(((LARG * e - w) / 2, y), linha, font=fc, fill=cor)
        y += int(fc.size * 1.2)
    f = M.fonte(True, 24 * e)
    txt = f"{n}/{total}"
    d.text((x1 - d.textlength(txt, font=f), int(70 * e)), txt, font=f,
           fill=M.CIANO)
    return peca


def _salvar(peca, destino):
    pub = peca.resize((LARG, ALT), Image.LANCZOS)
    pub.save(destino, "JPEG", quality=94, optimize=True)
    return destino


def montar(slides, chamada_final, fonte, destino_base, primeiro_numero=2,
           total=None):
    """
    slides: lista de {"titulo", "texto"}. Devolve a lista de JPEGs dos
    slides 2..n, ja no tamanho de publicacao (1080x1350).
    """
    total = total or (len(slides) + primeiro_numero)
    saida = []
    for i, s in enumerate(slides):
        n = primeiro_numero + i
        # a fonte vai so no ultimo slide de texto, onde o fato fecha
        f = fonte if i == len(slides) - 1 else ""
        peca = slide_texto(s["titulo"].strip(), s["texto"].strip(), n,
                           total, f)
        saida.append(_salvar(peca, f"{destino_base}_slide{n}.jpg"))
    n = primeiro_numero + len(slides)
    saida.append(_salvar(slide_final(chamada_final, n, total),
                         f"{destino_base}_slide{n}.jpg"))
    return saida
