#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compositor da FisioSync.

Nao existe mais uma pilha fixa de blocos. Cada peca escolhe um entre
cinco layouts, e o layout nasce do conceito definido antes de gerar
a imagem. A foto entra sangrada na borda, esfumada no branco ou solta
sem moldura, nunca dentro de um cartao arredondado por padrao.

Exporta producao (2x) e publicacao, em PNG e JPEG.
"""

import os

from PIL import Image, ImageDraw

import layouts as LY
import marca as M

LOGO = M.LOGO
SELO_GOOGLE = M.SELO_GOOGLE
SELO_APPLE = M.SELO_APPLE
avisos = M.avisos


def _base(formato, escala):
    f = M.FORMATOS[formato]
    Lp, Ap = f["larg"], f["alt"]
    me, mt, md, mb = f["margem"]
    e = escala
    peca = Image.new("RGB", (Lp * e, Ap * e), M.BRANCO)
    geo = {
        "L": Lp * e, "A": Ap * e,
        "x0": me * e, "y0": mt * e, "x1": (Lp - md) * e, "y1": (Ap - mb) * e,
        "Lp": Lp, "Ap": Ap, "e": e,
    }
    geo["larg"] = geo["x1"] - geo["x0"]
    return peca, geo


# --------------------------------------------------------------------------
# Os cinco layouts
# --------------------------------------------------------------------------

def _que_cabe(d, texto, larg, e, tam, negrito, ideal, limite, minimo=0.70):
    """
    Devolve (fonte, linhas, corpo) com o texto inteiro desenhavel.

    Tenta primeiro no numero IDEAL de linhas, diminuindo o corpo. Se nem
    no menor corpo couber, aceita ate LIMITE linhas, de novo do maior
    corpo para o menor. Se ainda assim nao couber, deixa o
    LY.TextoNaoCabe subir: a peca nao sai.

    Nenhum caminho aqui corta texto. O corte silencioso foi o que
    publicou "e deixar claras as condicoes do" em 01/11/2026.
    """
    try:
        return LY.caber(d, texto, larg, ideal, negrito, tam, e, minimo)
    except LY.TextoNaoCabe:
        return LY.caber(d, texto, larg, limite, negrito, tam, e, minimo)


def _calibrado(peca, d, foto, tit, apo, g, story, sobretitulo=""):
    """
    Hierarquia da referencia aprovada: logo centrada, sobretitulo
    discreto, chamada grande em duas cores, apoio curto, ilustracao
    grande e assinatura fechando a leitura.

    Usado na calibracao. Centralizar nao e erro: e o que a referencia
    faz e funciona.
    """
    e = g["e"]
    meio = (g["x0"] + g["x1"]) / 2
    larg = g["larg"]

    y = LY.logo(peca, 0, g["y0"])

    # sobretitulo discreto, em caixa alta espacada
    if sobretitulo:
        f_sob = M.fonte(True, 22 * e)
        esp = int(5 * e)
        y += int(34 * e)
        w = LY.largura_espacada(d, sobretitulo.upper(), f_sob, esp)
        LY.texto_espacado(d, sobretitulo.upper(), meio - w / 2, y,
                          f_sob, M.MARINHO, esp)
        y += int(f_sob.size * 1.3)

    # chamada grande, duas cores
    y += int(40 * e)
    tam = 76 if not story else 70
    f, linhas, tam = _que_cabe(d, tit, larg, e, tam, True, ideal=2, limite=3)
    for i, linha in enumerate(linhas):
        cor = M.CIANO if (len(linhas) > 1 and i == len(linhas) - 1) else M.MARINHO
        w = d.textlength(linha, font=f)
        d.text((meio - w / 2, y), linha, font=f, fill=cor)
        y += int(tam * 1.12 * e)

    # apoio curto
    if apo:
        fa, linhas_ap, _ = _que_cabe(d, apo, larg * 0.94, e,
                                     32 if not story else 31, False,
                                     ideal=2, limite=3)
        y += int(18 * e)
        for linha in linhas_ap:
            w = d.textlength(linha, font=fa)
            d.text((meio - w / 2, y), linha, font=fa, fill=M.MARINHO)
            y += int(fa.size * 1.34)

    topo_rodape = LY.assinatura(peca, d, g["x0"], g["x1"], g["y1"], e,
                                tratamento="pilula", alinhar="centro")

    # ilustracao grande, inteira, sem corte e sem moldura
    folga = int(34 * e)
    topo = y + folga
    alt = topo_rodape - folga - topo
    if alt > int(160 * e) and os.path.exists(foto):
        LY.colocar(peca, foto, (g["x0"], topo, g["x1"], topo + alt),
                   tema=g.get("tema", ""), conceito=g.get("conceito", ""))


def _tipografico(peca, d, foto, tit, apo, g, story, sobretitulo=""):
    """
    Peca sem ilustracao: a tipografia e o elemento visual.

    Serve aos stories extras do dia, que nao precisam de imagem nova.
    Custo de geracao: zero. E uma das familias de composicao previstas
    (composicao editorial), nao um remendo.
    """
    import efeitos as EF
    e = g["e"]
    meio = (g["x0"] + g["x1"]) / 2
    larg = g["larg"]

    y = LY.logo(peca, 0, g["y0"])

    if sobretitulo:
        f_sob = M.fonte(True, 23 * e)
        esp = int(5 * e)
        y += int(40 * e)
        w = LY.largura_espacada(d, sobretitulo.upper(), f_sob, esp)
        LY.texto_espacado(d, sobretitulo.upper(), meio - w / 2, y,
                          f_sob, M.MARINHO, esp)
        y += int(f_sob.size * 1.3)

    topo_rodape = LY.assinatura(peca, d, g["x0"], g["x1"], g["y1"], e,
                                tratamento="pilula", alinhar="centro")

    # a mancha em ciano entra atras do texto, dando corpo a peca
    miolo_topo = y + int(40 * e)
    miolo_base = topo_rodape - int(40 * e)
    EF.forma_organica(peca, (g["x0"], miolo_topo, g["x1"], miolo_base),
                      forca=0.22, semente=len(tit))

    # chamada bem grande, ocupando o miolo
    tam = 104 if story else 92
    f = M.fonte(True, tam * e)
    linhas = LY.quebrar(tit, f, larg, d)
    while (len(linhas) > 4 or
           len(linhas) * tam * 1.14 * e > (miolo_base - miolo_topo) * 0.66) \
            and tam > 52:
        tam -= 6
        f = M.fonte(True, tam * e)
        linhas = LY.quebrar(tit, f, larg, d)

    if apo:
        fa, linhas_ap, _ = _que_cabe(d, apo, larg * 0.92, e,
                                     max(28, int(tam * 0.40)), False,
                                     ideal=3, limite=4)
    else:
        fa, linhas_ap = M.fonte(False, max(28, int(tam * 0.40)) * e), []

    altura_tit = len(linhas) * int(tam * 1.14 * e)
    altura_ap = (int(tam * 0.30 * e) + len(linhas_ap) * int(fa.size * 1.34)
                 if linhas_ap else 0)
    yy = miolo_topo + ((miolo_base - miolo_topo) - altura_tit - altura_ap) / 2

    for i, linha in enumerate(linhas):
        cor = M.CIANO if (len(linhas) > 1 and i == len(linhas) - 1) else M.MARINHO
        w = d.textlength(linha, font=f)
        d.text((meio - w / 2, yy), linha, font=f, fill=cor)
        yy += int(tam * 1.14 * e)

    if linhas_ap:
        yy += int(tam * 0.30 * e)
        for linha in linhas_ap:
            w = d.textlength(linha, font=fa)
            d.text((meio - w / 2, yy), linha, font=fa, fill=M.MARINHO)
            yy += int(fa.size * 1.34)


def _editorial(peca, d, foto, tit, apo, g, story):
    """Tipografia domina. Foto em faixa sangrada de ponta a ponta."""
    e, x0 = g["e"], g["x0"]
    y = LY.logo(peca, x0, g["y0"], int(58 * e))
    y += int(70 * e)
    y = LY.titulo(d, tit, x0, y, g["larg"], e, 66 if not story else 62)
    y = LY.apoio(d, apo, x0, y, g["larg"], e)

    topo_rodape = LY.assinatura(peca, d, x0, g["x1"], g["y1"], e,
                                tratamento="linha", alinhar="esq")
    folga = int(56 * e)
    alt = topo_rodape - folga - (y + folga)
    if alt > int(200 * e) and os.path.exists(foto):
        LY.colar_sangrado(peca, Image.open(foto).convert("RGB"),
                          (0, y + folga, g["L"], y + folga + alt))


def _lateral(peca, d, foto, tit, apo, g, story):
    """Foto sangra na lateral direita. Texto na coluna da esquerda."""
    e = g["e"]
    corte = int(g["L"] * (0.52 if not story else 0.46))
    if os.path.exists(foto):
        altura = int(g["A"] * (0.70 if not story else 0.60))
        topo = g["y0"] - int(40 * e) if not story else g["y0"] - int(60 * e)
        LY.colar_esfumado(peca, Image.open(foto).convert("RGB"),
                          (corte, max(0, topo), g["L"], max(0, topo) + altura),
                          lados=("esq", "base"), suave=int(110 * e))

    larg_texto = corte - g["x0"] - int(40 * e)
    y = LY.logo(peca, g["x0"], g["y0"], int(54 * e))
    y += int(64 * e)
    y = LY.titulo(d, tit, g["x0"], y, larg_texto, e, 54)
    LY.apoio(d, apo, g["x0"], y, larg_texto, e, tam=29)

    LY.assinatura(peca, d, g["x0"], g["x1"], g["y1"], e,
                  tratamento="pilula", alinhar="esq")


def _objeto(peca, d, foto, tit, apo, g, story):
    """Objeto solto sobre o branco, sem moldura nenhuma."""
    e, x0 = g["e"], g["x0"]
    y = LY.logo(peca, x0, g["y0"], int(56 * e))
    y += int(66 * e)
    y = LY.titulo(d, tit, x0, y, g["larg"], e, 60)
    y = LY.apoio(d, apo, x0, y, g["larg"], e)

    topo_rodape = LY.assinatura(peca, d, x0, g["x1"], g["y1"], e,
                                tratamento="solto", alinhar="centro")
    folga = int(40 * e)
    alt = topo_rodape - folga - (y + folga)
    if alt > int(200 * e) and os.path.exists(foto):
        larg = int(g["larg"] * 1.08)
        cx = (g["x0"] + g["x1"]) / 2
        LY.colocar(peca, foto, (int(cx - larg / 2), y + folga,
                                int(cx + larg / 2), y + folga + alt),
                   tema=g.get("tema", ""), conceito=g.get("conceito", ""))


def _detalhe(peca, d, foto, tit, apo, g, story):
    """Recorte aproximado sangrando no topo. Texto embaixo, no branco."""
    e, x0 = g["e"], g["x0"]

    # o rodape vem primeiro, para o texto saber onde parar
    topo_rodape = LY.assinatura(peca, d, x0, g["x1"], g["y1"], e,
                                tratamento="linha", alinhar="esq")

    # quanto o texto precisa, medido antes de escolher a altura da foto
    # medido com o mesmo criterio que o desenho vai usar, senao a conta
    # de espaco mente e o texto estoura o rodape
    n_tit = len(_que_cabe(d, tit, g["larg"], e, 58, True,
                          ideal=3, limite=4)[1])
    n_ap = len(_que_cabe(d, apo, g["larg"], e, 31, False,
                         ideal=2, limite=3)[1]) if apo else 0
    preciso = (int(50 * e)                      # logo
               + int(50 * e)                    # respiro
               + n_tit * int(58 * 1.18 * e)
               + (int(31 * 0.5 * e) + n_ap * int(31 * 1.38 * e) if n_ap else 0)
               + int(56 * e))                   # folga antes do rodape

    topo = 0 if not story else int(g["A"] * 0.08)
    alt_foto = topo_rodape - int(40 * e) - preciso - topo
    alt_foto = max(int(g["A"] * 0.22), min(alt_foto, int(g["A"] * 0.50)))

    if os.path.exists(foto):
        LY.colar_sangrado(peca, Image.open(foto).convert("RGB"),
                          (0, topo, g["L"], topo + alt_foto))

    y = topo + alt_foto + int(56 * e)
    y = LY.logo(peca, x0, y, int(50 * e))
    y += int(50 * e)
    y = LY.titulo(d, tit, x0, y, g["larg"], e, 58)
    LY.apoio(d, apo, x0, y, g["larg"], e, maximo=3)


def _centro(peca, d, foto, tit, apo, g, story):
    """Centralizado de proposito, quando a mensagem pede simetria."""
    e, x0 = g["e"], g["x0"]
    meio = (g["x0"] + g["x1"]) / 2

    y = LY.logo(peca, 0, g["y0"]) + int(62 * e)

    f, linhas, corpo = _que_cabe(d, tit, g["larg"], e, 58, True,
                                 ideal=3, limite=4)
    for i, linha in enumerate(linhas):
        cor = M.CIANO if (len(linhas) > 1 and i == len(linhas) - 1) else M.MARINHO
        w = d.textlength(linha, font=f)
        d.text((meio - w / 2, y), linha, font=f, fill=cor)
        y += int(corpo * 1.18 * e)

    if apo:
        fa, linhas_ap, _ = _que_cabe(d, apo, g["larg"] * 0.92, e, 30, False,
                                     ideal=3, limite=4)
        y += int(16 * e)
        for linha in linhas_ap:
            w = d.textlength(linha, font=fa)
            d.text((meio - w / 2, y), linha, font=fa, fill=M.MARINHO)
            y += int(30 * 1.38 * e)

    topo_rodape = LY.assinatura(peca, d, x0, g["x1"], g["y1"], e,
                                tratamento="pilula", alinhar="centro")
    folga = int(44 * e)
    alt = topo_rodape - folga - (y + folga)
    if alt > int(200 * e) and os.path.exists(foto):
        LY.colocar(peca, foto, (x0, y + folga, g["x1"], y + folga + alt),
                   tema=g.get("tema", ""), conceito=g.get("conceito", ""))


_MONTADORES = {
    "calibrado": _calibrado,
    "tipografico": _tipografico,
    "editorial": _editorial,
    "lateral": _lateral,
    "objeto": _objeto,
    "detalhe": _detalhe,
    "centro": _centro,
}


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

def montar(caminho_foto, titulo, apoio, destino_base, formato="feed",
           escala=2, layout="calibrado", sobretitulo="", tema="",
           conceito=""):
    """Monta a peca no layout pedido e exporta producao e publicacao."""
    if layout not in _MONTADORES:
        layout = "calibrado"
    # 9:16 nao comporta duas colunas: a coluna de texto fica estreita
    # demais e corta frase. O story ganha composicao propria, como o
    # guia pede, em vez de reaproveitar a do feed.
    if formato == "story" and layout == "lateral":
        layout = "detalhe"
    peca, g = _base(formato, escala)
    d = ImageDraw.Draw(peca)
    g["tema"], g["conceito"] = tema, conceito
    if layout in ("calibrado", "tipografico"):
        _MONTADORES[layout](peca, d, caminho_foto, titulo, apoio, g,
                            formato == "story", sobretitulo)
    else:
        _MONTADORES[layout](peca, d, caminho_foto, titulo, apoio, g,
                            formato == "story")

    L, A = g["L"], g["A"]
    Lp, Ap = g["Lp"], g["Ap"]
    # Dois arquivos, cada um com uma funcao:
    #   producao 2160 em PNG  -> arquivo sem perda, para reaproveitar
    #   publicacao 1080 em JPEG -> o que vai para o Instagram, que so
    #                              aceita JPEG pela API
    # O PNG de 1080 que existia aqui nao era publicado nem arquivado:
    # era so peso em disco.
    prod = f"{destino_base}_{L}x{A}.png"
    pub_jpg = f"{destino_base}_{Lp}x{Ap}.jpg"

    peca.save(prod, "PNG")
    reduzida = peca.resize((Lp, Ap), Image.LANCZOS)
    reduzida.save(pub_jpg, "JPEG", quality=94, optimize=True)
    return pub_jpg


def validar(caminho, formato="feed"):
    f = M.FORMATOS[formato]
    esperado = (f["larg"], f["alt"])
    im = Image.open(caminho)
    if im.size != esperado:
        return False, (f"{im.size[0]}x{im.size[1]} "
                       f"(esperado {esperado[0]}x{esperado[1]})")
    return True, f"{im.size[0]}x{im.size[1]}"
