#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa os selos oficiais das lojas, em portugues do Brasil, e salva como:
    selo_google_play.png
    selo_app_store.png

Esses selos sao fornecidos pela Google e pela Apple justamente para
divulgar aplicativos publicados nas lojas delas. Nada e desenhado aqui:
sao os arquivos oficiais.
"""

import io
import os
import subprocess
import sys

try:
    import requests
except ImportError:
    print("[ERRO] Falta 'requests'. Rode: pip install requests")
    sys.exit(1)

PASTA = os.path.dirname(os.path.abspath(__file__))
ALVO_GOOGLE = os.path.join(PASTA, "selo_google_play.png")
ALVO_APPLE = os.path.join(PASTA, "selo_app_store.png")

NAVEGADOR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

URLS_GOOGLE = [
    "https://play.google.com/intl/pt-BR/badges/static/images/badges/pt-br_badge_web_generic.png",
    "https://play.google.com/intl/pt_br/badges/static/images/badges/pt-br_badge_web_generic.png",
    "https://play.google.com/intl/en_us/badges/static/images/badges/pt-br_badge_web_generic.png",
]
URLS_APPLE = [
    "https://toolbox.marketingtools.apple.com/api/v2/badges/download-on-the-app-store/black/pt-br",
    "https://toolbox.marketingtools.apple.com/api/v2/badges/download-on-the-app-store/black/pt-BR",
    "https://toolbox.marketingtools.apple.com/api/v2/badges/download-on-the-app-store/black/en-us",
]


def baixar(urls, nome):
    for url in urls:
        try:
            r = requests.get(url, headers=NAVEGADOR, timeout=60)
            if r.status_code == 200 and len(r.content) > 500:
                print(f"  baixado de: {url}")
                return r.content
            print(f"  nao deu ({r.status_code}): {url}")
        except Exception as e:
            print(f"  falhou: {url} -> {e}")
    print(f"[AVISO] Nao consegui baixar o selo da {nome}.")
    return None


def garantir(pacote, importar=None):
    try:
        __import__(importar or pacote)
        return True
    except ImportError:
        print(f"  instalando {pacote}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                            pacote], check=True)
            __import__(importar or pacote)
            return True
        except Exception as e:
            print(f"  nao consegui instalar {pacote}: {e}")
            return False


def svg_para_png(dados_svg, destino, altura=240):
    """Converte o SVG da Apple em PNG, tentando duas bibliotecas."""
    # 1) cairosvg
    if garantir("cairosvg"):
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=dados_svg, write_to=destino,
                             output_height=altura)
            return True
        except Exception as e:
            print(f"  cairosvg nao deu: {e}")

    # 2) svglib + reportlab (funciona melhor no Windows)
    if garantir("svglib") and garantir("reportlab"):
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            desenho = svg2rlg(io.BytesIO(dados_svg))
            if desenho is not None and desenho.height:
                fator = altura / desenho.height
                desenho.width *= fator
                desenho.height = altura
                desenho.scale(fator, fator)
                renderPM.drawToFile(desenho, destino, fmt="PNG",
                                    bg=0xFFFFFF)
                return True
        except Exception as e:
            print(f"  svglib nao deu: {e}")
    return False


def main():
    print("=" * 56)
    print("  BAIXANDO OS SELOS OFICIAIS DAS LOJAS")
    print("=" * 56)

    print("\nGoogle Play:")
    dados = baixar(URLS_GOOGLE, "Google Play")
    if dados:
        with open(ALVO_GOOGLE, "wb") as f:
            f.write(dados)
        print(f"  salvo em {os.path.basename(ALVO_GOOGLE)}")

    print("\nApp Store:")
    dados = baixar(URLS_APPLE, "App Store")
    if dados:
        if dados[:4] == b"\x89PNG":
            with open(ALVO_APPLE, "wb") as f:
                f.write(dados)
            print(f"  salvo em {os.path.basename(ALVO_APPLE)}")
        else:
            print("  veio em SVG, convertendo para PNG...")
            if svg_para_png(dados, ALVO_APPLE):
                print(f"  salvo em {os.path.basename(ALVO_APPLE)}")
            else:
                bruto = os.path.join(PASTA, "selo_app_store.svg")
                with open(bruto, "wb") as f:
                    f.write(dados)
                print(f"  nao consegui converter. O SVG ficou em "
                      f"{os.path.basename(bruto)}.")

    print("\n" + "=" * 56)
    faltam = [n for n, p in (("Google Play", ALVO_GOOGLE),
                             ("App Store", ALVO_APPLE))
              if not os.path.exists(p)]
    if not faltam:
        print("  OS DOIS SELOS ESTAO PRONTOS.")
        print("  Agora rode o PREVIA.bat.")
    else:
        print("  AINDA FALTA: " + ", ".join(faltam))
        print("\n  Baixe manualmente e salve nesta pasta com estes nomes:")
        print("    selo_google_play.png")
        print("      https://play.google.com/intl/pt-BR/badges/")
        print("    selo_app_store.png")
        print("      https://developer.apple.com/app-store/marketing/guidelines/")
    print("=" * 56)


if __name__ == "__main__":
    main()
