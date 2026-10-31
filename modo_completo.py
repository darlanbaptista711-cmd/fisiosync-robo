#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODO COMPLETO: a IA desenha a peca inteira, igual ao ChatGPT.

A logo oficial (e os selos, se existirem na pasta) sao enviados como
imagens de referencia pelo endpoint de edicao da OpenAI, que e o mesmo
caminho que o ChatGPT usa quando voce anexa a logo e pede a arte.

Diferenca em relacao ao modo molde:
  - molde.py  -> texto perfeito sempre, layout fixo
  - este aqui -> arte livre e variada, mas o texto pode sair com erro
"""

import base64
import os

import requests

PASTA = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(PASTA, "logo.png")
SELO_GOOGLE = os.path.join(PASTA, "selo_google_play.png")
SELO_APPLE = os.path.join(PASTA, "selo_app_store.png")

MODELOS = [
    "chatgpt-image-latest",      # o mesmo que o ChatGPT usa
    "gpt-image-2.5-sunburst",
    "gpt-image-2.5-flare",
    "gpt-image-2",
]

GUIA = """\
Voce e o diretor de arte da FisioSync, um software de gestao para
fisioterapeutas. Crie UMA peca de Instagram pronta para publicacao.

MARCA
- Nome exato: FisioSync. Tratar no feminino: a FisioSync.
- Publico: fisioterapeutas, gestores de clinica e donos de estudio de Pilates.
- Portugues do Brasil, com acentuacao correta.

IDENTIDADE VISUAL
- Fundo branco puro #FFFFFF.
- Ciano principal #18B7D8.
- Azul-marinho para titulos e textos #0B2948.
- Cinza-claro para bordas e detalhes #E8EEF2.
- Estilo clean, moderno, premium e organizado, com muito espaco em branco.
- Tipografia sans-serif, titulo forte e textos de apoio legiveis no celular.
- Sem brilhos, neon, confete, faixas promocionais, precos ou descontos.

LOGO
- A primeira imagem de referencia e a LOGO OFICIAL da FisioSync.
- Reproduza a logo exatamente como esta: simbolo, lettering, a assinatura
  "Gestao Inteligente", as cores e as proporcoes.
- Nao redesenhe, nao recolore, nao deforme e nao corte a logo.
- Aplique sobre o fundo branco, com espaco ao redor.

TEXTOS OBRIGATORIOS (escreva exatamente assim, uma vez cada, bem legiveis)
- Chamada principal: "{titulo}"
- Apoio: "{apoio}"
- "Teste gratis por 7 dias"
- "Disponivel no Google Play e na App Store."
- "app.fisiosync.com.br"

DIRECAO DE ARTE
- Estilo desta peca: {estilo}
- Elemento visual central: {foto}
- Fotografia realista, materiais, luz e sombras naturais.
- Sem pessoas, rostos ou maos.
- Sem celulares, tablets, computadores ou telas de aplicativo.
- O elemento visual apoia a mensagem, sem competir com o titulo.

ESTRUTURA
1. Logo no topo.
2. Chamada principal curta e forte.
3. Texto de apoio breve.
4. Elemento visual.
5. "Teste gratis por 7 dias" em destaque.
6. Rodape com a disponibilidade, os selos das lojas e o site.

FORMATO
{formato}

QUALIDADE
- Todas as letras nitidas, sem erro de ortografia e sem letras deformadas.
- Nada cortado nas bordas.
"""

FORMATO_FEED = (
    "Proporcao 4:5 vertical (retrato), equivalente a 1080x1350. "
    "Margem de seguranca de 80 pixels em todos os lados: nenhum texto, logo "
    "ou selo encostado na borda. Composicao propria para 4:5."
)
FORMATO_STORY = (
    "Proporcao 9:16 vertical (retrato, bem alongado), equivalente a 1080x1920. "
    "Margem lateral de 80 pixels. Deixe os 250 pixels do topo e os 350 "
    "pixels da base vazios, so com fundo branco, porque a interface do "
    "Instagram cobre essas areas. Todo o conteudo fica entre essas faixas. "
    "Reorganize a composicao para este formato, nao apenas estique o feed. "
    "Nao desenhe guias nem marcacoes de margem."
)


def _referencias():
    """Logo primeiro; selos oficiais depois, se existirem na pasta."""
    arquivos = []
    if os.path.exists(LOGO):
        arquivos.append(("image[]", ("logo.png", open(LOGO, "rb"), "image/png")))
    for caminho, nome in ((SELO_GOOGLE, "selo_google_play.png"),
                          (SELO_APPLE, "selo_app_store.png")):
        if os.path.exists(caminho):
            arquivos.append(("image[]", (nome, open(caminho, "rb"),
                                         "image/png")))
    return arquivos


def gerar(chave, titulo, apoio, descricao_foto, formato, destino, log=print,
          estilo="fotografia realista de produto", preferido=None):
    """Gera a peca inteira. formato: 'feed' ou 'story'."""
    prompt = GUIA.format(
        titulo=titulo, apoio=apoio, foto=descricao_foto, estilo=estilo,
        formato=FORMATO_FEED if formato == "feed" else FORMATO_STORY)
    modelos = ([preferido] if preferido else []) + [
        m for m in MODELOS if m != preferido]

    refs = _referencias()
    if refs:
        nomes = [r[1][0] for r in refs]
        log(f"  referencias enviadas: {', '.join(nomes)}")
    else:
        log("  AVISO: nenhuma referencia encontrada (logo.png faltando).")

    for modelo in modelos:
        dados = None
        if refs:
            dados = _editar(chave, modelo, prompt, refs, log)
        if dados is None:
            dados = _criar(chave, modelo, prompt, log)
        if dados:
            with open(destino, "wb") as f:
                f.write(dados)
            log(f"  peca gerada por {modelo} ({len(dados)//1024} KB)")
            return destino
    return None


def _editar(chave, modelo, prompt, refs, log):
    """Endpoint de edicao: usa as imagens de referencia."""
    try:
        r = requests.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {chave}"},
            data={"model": modelo, "prompt": prompt,
                  "size": "1024x1536", "quality": "high", "n": "1",
                  "input_fidelity": "high"},
            files=refs, timeout=600)
        if r.status_code == 200:
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        log(f"  edicao com referencia nao deu: {r.status_code} "
            f"{r.text[:220]}")
    except Exception as e:
        log(f"  edicao falhou: {type(e).__name__}: {e}")
    finally:
        for _, (_, arquivo, _) in refs:
            try:
                arquivo.close()
            except Exception:
                pass
    return None


def _criar(chave, modelo, prompt, log):
    """Sem referencia: o modelo desenha tudo do zero."""
    try:
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {chave}",
                     "Content-Type": "application/json"},
            json={"model": modelo, "prompt": prompt,
                  "size": "1024x1536", "quality": "high", "n": 1},
            timeout=600)
        if r.status_code == 200:
            log("  gerada sem referencia (a logo pode sair imprecisa)")
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        log(f"  geracao nao deu: {r.status_code} {r.text[:220]}")
    except Exception as e:
        log(f"  geracao falhou: {type(e).__name__}: {e}")
    return None
