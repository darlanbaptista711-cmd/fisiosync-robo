#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de composicao da FisioSync.

Cinco layouts de verdade diferentes, nao um template com variacoes
de cor. A escolha do layout nasce do conceito da peca, e cada um
distribui titulo, imagem e assinatura de um jeito proprio.

Nenhum deles usa cartao arredondado por padrao. A foto entra
sangrada na borda, integrada ao branco com borda esfumada, ou
solta sobre o fundo branco sem moldura nenhuma.
"""

from PIL import Image, ImageDraw, ImageFilter

import marca as M

# PADRAO TRAVADO em 31/10/2026, a pedido do Darlan.
#
# So estes dois entram no sorteio automatico. Os dois colocam a LOGO
# PRIMEIRO e CENTRALIZADA, e seguem a mesma ordem de leitura das
# referencias aprovadas 02 e 03.
#
# Os outros continuam funcionando no molde.py, mas ficam fora da
# escolha automatica porque quebram essa ordem: o "detalhe", por
# exemplo, poe a foto antes da logo.
LAYOUTS = [
    "calibrado",     # com ilustracao
    "tipografico",   # sem ilustracao, so tipografia
]

LAYOUTS_EXTRAS = ["editorial", "lateral", "objeto", "detalhe", "centro"]

# Onde cada layout precisa de espaco vazio na foto gerada.
# Isso vai dentro do pedido feito a IA, antes de gerar a imagem.
ESPACO_NEGATIVO = {
    "tipografico": "",
    "calibrado": "one single horizontal scene, subject filling the frame "
                 "edge to edge, no empty margins around it",
    "editorial": "leave the upper third of the frame almost empty",
    "lateral": "place the subject on the right side, leave the left half empty",
    "objeto": "single subject centred on a seamless pure white background, "
              "generous empty space all around",
    "detalhe": "tight close-up of the subject filling the frame",
    "centro": "subject centred with even empty space around it",
}


# --------------------------------------------------------------------------
# Auxiliares
# --------------------------------------------------------------------------

def quebrar(texto, fonte, largura, d):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if d.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def encaixar(img, larg, alt):
    """Corta no centro para a proporcao pedida. Nunca deforma."""
    alvo, atual = larg / alt, img.width / img.height
    if atual > alvo:
        nova = int(img.height * alvo)
        x = (img.width - nova) // 2
        img = img.crop((x, 0, x + nova, img.height))
    elif atual < alvo:
        nova = int(img.width / alvo)
        y = (img.height - nova) // 2
        img = img.crop((0, y, img.width, y + nova))
    return img.resize((larg, alt), Image.LANCZOS)


def colar_sangrado(peca, foto, caixa):
    """Foto ocupando a caixa inteira, encostando nas bordas. Sem moldura."""
    x0, y0, x1, y1 = caixa
    peca.paste(encaixar(foto, x1 - x0, y1 - y0), (x0, y0))


def colar_esfumado(peca, foto, caixa, lados=("esq", "dir", "topo", "base"),
                   suave=60):
    """
    Foto integrada ao branco: as bordas escolhidas desaparecem em degrade.
    E isto que elimina a aparencia de cartao colado.
    """
    x0, y0, x1, y1 = caixa
    larg, alt = x1 - x0, y1 - y0
    img = encaixar(foto, larg, alt)
    # o degrade nunca pode comer mais que 12% do lado: era o que
    # estava lavando a ilustracao e tirando a presenca dela
    suave = max(10, min(int(suave), int(min(larg, alt) * 0.12)))

    mascara = Image.new("L", (larg, alt), 255)
    d = ImageDraw.Draw(mascara)
    if "esq" in lados:
        for i in range(suave):
            d.line([(i, 0), (i, alt)], fill=int(255 * i / suave))
    if "dir" in lados:
        for i in range(suave):
            d.line([(larg - 1 - i, 0), (larg - 1 - i, alt)],
                   fill=int(255 * i / suave))
    if "topo" in lados:
        for i in range(suave):
            d.line([(0, i), (larg, i)], fill=int(255 * i / suave))
    if "base" in lados:
        for i in range(suave):
            d.line([(0, alt - 1 - i), (larg, alt - 1 - i)],
                   fill=int(255 * i / suave))
    mascara = mascara.filter(ImageFilter.GaussianBlur(suave / 6))
    peca.paste(img, (x0, y0), mascara)


def recortar_conteudo(img, tolerancia=14, folga=0.03):
    """
    Corta a moldura vazia que o gerador deixa em volta do desenho.
    Sem isto, o desenho chega pequeno dentro de um arquivo quase todo
    branco, e o compositor acaba exibindo o vazio em vez da ilustracao.
    """
    from PIL import ImageChops
    rgb = img.convert("RGB")
    canto = rgb.getpixel((2, 2))
    fundo = Image.new("RGB", rgb.size, canto)
    dif = ImageChops.difference(rgb, fundo).convert("L")
    caixa = dif.point(lambda p: 255 if p > tolerancia else 0).getbbox()
    if not caixa:
        return img
    fx = int(img.width * folga)
    fy = int(img.height * folga)
    return img.crop((max(0, caixa[0] - fx), max(0, caixa[1] - fy),
                     min(img.width, caixa[2] + fx),
                     min(img.height, caixa[3] + fy)))


def normalizar_branco(img, alvo=(255, 255, 255)):
    """
    O gerador entrega fundo 'quase branco' (247,246,244). Colado numa
    peca de fundo #FFFFFF, isso vira um retangulo cinza visivel, que e
    exatamente a aparencia de imagem colada dentro de um cartao.
    Aqui o fundo e puxado para branco puro, sem lavar o desenho.
    """
    canto = img.getpixel((2, 2))
    if min(canto) < 215:            # fundo escuro de proposito: nao mexe
        return img
    escalas = [min(2.0, alvo[i] / max(1, canto[i])) for i in range(3)]
    if max(escalas) < 1.004:
        return img
    tabelas = []
    for i in range(3):
        k = escalas[i]
        tabelas += [min(255, int(v * k)) for v in range(256)]
    return img.point(tabelas)


def colocar(peca, foto, caixa, recortar=True, tema="", conceito="",
            efeitos_ciano=True):
    """
    Coloca a ilustracao dentro da caixa SEM CORTAR nada: ela e reduzida
    ate caber inteira e centralizada no espaco. O fundo da peca ja e
    branco, entao nao precisa de mascara nem de esfumado.

    Devolve a area realmente ocupada.
    """
    x0, y0, x1, y1 = caixa
    larg, alt = x1 - x0, y1 - y0
    img = foto if isinstance(foto, Image.Image) else Image.open(foto)
    img = img.convert("RGB")
    if recortar:
        img = recortar_conteudo(img)
    img = normalizar_branco(img)

    fator = min(larg / img.width, alt / img.height)
    nova = (max(1, int(img.width * fator)), max(1, int(img.height * fator)))
    img = img.resize(nova, Image.LANCZOS)
    px = x0 + (larg - nova[0]) // 2
    py = y0 + (alt - nova[1]) // 2

    if efeitos_ciano:
        import efeitos as EF
        # os efeitos ficam ATRAS: desenha primeiro, depois a ilustracao
        # com o fundo branco transparente
        EF.aplicar(peca, (px, py, px + nova[0], py + nova[1]),
                   tema, conceito, semente=len(tema) + len(conceito))
        recortada = EF.mascara_sem_fundo(img)
        peca.paste(recortada, (px, py), recortada)
    else:
        peca.paste(img, (px, py))
    return (px, py, px + nova[0], py + nova[1])


def texto_espacado(d, texto, x, y, fonte, cor, espaco):
    """Linha com entreletra, para sobretitulo em caixa alta."""
    for ch in texto:
        d.text((x, y), ch, font=fonte, fill=cor)
        x += d.textlength(ch, font=fonte) + espaco
    return x


def largura_espacada(d, texto, fonte, espaco):
    return sum(d.textlength(c, font=fonte) + espaco for c in texto) - espaco


def colar_solto(peca, foto, caixa):
    """Objeto sobre fundo branco, sem moldura e sem corte."""
    return colocar(peca, foto, caixa)


# --------------------------------------------------------------------------
# Assinatura da marca (rodape), com tres tratamentos
# --------------------------------------------------------------------------

def _selo(caminho, altura, nome):
    import os
    if os.path.exists(caminho):
        try:
            s = Image.open(caminho).convert("RGBA")
            return s.resize((int(s.width * altura / s.height), altura),
                            Image.LANCZOS)
        except Exception:
            pass
    M.aviso(f"FALTA O SELO OFICIAL DA {nome}. Peca reprovada.")
    return None


def assinatura(peca, d, x0, x1, base_y, e, tratamento="pilula",
               alinhar="centro"):
    """
    Desenha CTA, selos, disponibilidade e site de baixo para cima.
    Devolve o Y do topo da assinatura.
    'tratamento' muda a cara do teste gratis: pilula, linha ou solto.
    """
    f_cta = M.fonte(True, 34 * e)
    f_peq = M.fonte(False, 26 * e)
    f_site = M.fonte(True, 30 * e)
    L = peca.width
    meio = (x0 + x1) / 2

    def pos(largura):
        if alinhar == "esq":
            return x0
        if alinhar == "dir":
            return x1 - largura
        return meio - largura / 2

    y = base_y

    # site
    alt_site = int(f_site.size * 1.3)
    y -= alt_site
    w = d.textlength(M.SITE, font=f_site)
    d.text((pos(w), y), M.SITE, font=f_site, fill=M.CIANO)

    # disponibilidade
    y -= int(14 * e)
    alt_disp = int(f_peq.size * 1.3)
    y -= alt_disp
    w = d.textlength(M.DISPONIBILIDADE, font=f_peq)
    d.text((pos(w), y), M.DISPONIBILIDADE, font=f_peq, fill=M.MARINHO)

    # selos oficiais
    y -= int(20 * e)
    alt_selo = int(54 * e)
    y -= alt_selo
    g = _selo(M.SELO_GOOGLE, alt_selo, "Google Play")
    a = _selo(M.SELO_APPLE, alt_selo, "App Store")
    vao = int(24 * e)
    if g and a:
        total = g.width + vao + a.width
        x = int(pos(total))
        peca.paste(g, (x, y), g)
        peca.paste(a, (x + g.width + vao, y), a)

    # teste gratis
    y -= int(26 * e)
    if tratamento == "pilula":
        alt_cta = int(76 * e)
        y -= alt_cta
        w = d.textlength(M.CTA, font=f_cta) + int(76 * e)
        x = pos(w)
        d.rounded_rectangle([x, y, x + w, y + alt_cta],
                            radius=alt_cta // 2, fill=M.CIANO)
        d.text((x + int(38 * e), y + (alt_cta - f_cta.size * 1.3) / 2),
               M.CTA, font=f_cta, fill=M.BRANCO)
    elif tratamento == "linha":
        alt_cta = int(f_cta.size * 1.4)
        y -= alt_cta
        w = d.textlength(M.CTA, font=f_cta)
        x = pos(w)
        d.text((x, y), M.CTA, font=f_cta, fill=M.MARINHO)
        d.rectangle([x, y + alt_cta - int(6 * e), x + w,
                     y + alt_cta - int(2 * e)], fill=M.CIANO)
    else:  # solto
        f_big = M.fonte(True, 40 * e)
        alt_cta = int(f_big.size * 1.3)
        y -= alt_cta
        w = d.textlength(M.CTA, font=f_big)
        d.text((pos(w), y), M.CTA, font=f_big, fill=M.CIANO)

    return y


# A logo e SEMPRE centralizada no topo, nunca no canto.
# Largura entre 35% e 42% da largura total da arte.
LOGO_LARGURA = 0.38


def logo(peca, x, y, altura=None, largura_rel=LOGO_LARGURA):
    """
    Logo centralizada horizontalmente na arte inteira, medida pelo
    CONTEUDO VISIVEL: as margens transparentes do arquivo sao cortadas
    antes, senao a centralizacao sai torta.

    Os parametros x e altura ficam por compatibilidade e sao ignorados:
    a posicao horizontal e sempre o centro da peca.
    """
    import os
    if not os.path.exists(M.LOGO):
        M.aviso("FALTA O ARQUIVO logo.png.")
        return y + (altura or 0)

    lg = Image.open(M.LOGO).convert("RGBA")
    caixa = lg.split()[3].getbbox()          # conteudo visivel
    if caixa:
        lg = lg.crop(caixa)

    alvo = int(peca.width * largura_rel)
    nova_alt = max(1, int(lg.height * alvo / lg.width))
    lg = lg.resize((alvo, nova_alt), Image.LANCZOS)

    px = int((peca.width - alvo) / 2)
    peca.paste(lg, (px, int(y)), lg)
    return y + nova_alt


def titulo(d, texto, x, y, largura, e, tam, destaque=True):
    """Titulo em duas cores, destacando por significado e nao por regra."""
    f = M.fonte(True, tam * e)
    linhas = quebrar(texto, f, largura, d)[:4]
    passo = int(tam * 1.18 * e)
    # so pinta de ciano se a ultima linha tiver pelo menos duas palavras
    pintar = destaque and len(linhas) > 1 and len(linhas[-1].split()) >= 2
    for i, linha in enumerate(linhas):
        cor = M.CIANO if (pintar and i == len(linhas) - 1) else M.MARINHO
        d.text((x, y), linha, font=f, fill=cor)
        y += passo
    return y


def apoio(d, texto, x, y, largura, e, tam=31, maximo=3):
    if not texto:
        return y
    f = M.fonte(False, tam * e)
    y += int(tam * 0.5 * e)
    for linha in quebrar(texto, f, largura, d)[:maximo]:
        d.text((x, y), linha, font=f, fill=M.MARINHO)
        y += int(tam * 1.38 * e)
    return y
