#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regras FIXAS da marca FisioSync.

Separado de proposito: aqui fica so o que nunca muda.
O que muda de peca para peca mora em layouts.py.
"""

import os

from PIL import ImageFont

PASTA = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(PASTA, "logo.png")
SELO_GOOGLE = os.path.join(PASTA, "selo_google_play.png")
SELO_APPLE = os.path.join(PASTA, "selo_app_store.png")

CIANO = (24, 183, 216)      # #18B7D8
MARINHO = (11, 41, 72)      # #0B2948
CINZA = (232, 238, 242)     # #E8EEF2
BRANCO = (255, 255, 255)    # #FFFFFF

CTA = "Teste grátis por 7 dias"
DISPONIBILIDADE = "Disponível no Google Play e na App Store."
SITE = "app.fisiosync.com.br"

# Medidas de publicacao e areas reservadas
FORMATOS = {
    "feed":  {"larg": 1080, "alt": 1350,
              "margem": (80, 80, 80, 80)},          # esq, topo, dir, base
    "story": {"larg": 1080, "alt": 1920,
              "margem": (80, 250, 80, 350)},
}

FONTES_BOLD = [
    os.path.join(PASTA, "fontes", "bold.otf"),
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONTES_NORMAL = [
    os.path.join(PASTA, "fontes", "regular.otf"),
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

avisos = []


def aviso(msg):
    if msg not in avisos:
        avisos.append(msg)


def fonte(bold, tamanho):
    for caminho in (FONTES_BOLD if bold else FONTES_NORMAL):
        if os.path.exists(caminho):
            try:
                return ImageFont.truetype(caminho, int(tamanho))
            except Exception:
                continue
    return ImageFont.load_default()
