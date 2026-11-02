#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Humanizador de legendas, em portugues do Brasil.

Tira a cara de texto gerado por IA antes de publicar:
  1. apaga caracteres invisiveis (marca d'agua de IA)
  2. corrige tipografia (travessao, aspas curvas, reticencias)
  3. troca o vocabulario batido de IA por palavra normal
  4. confere as regras do Instagram: 125 caracteres visiveis,
     uma unica chamada para acao e no maximo 5 hashtags

Estrutura inspirada na skill ig-human de Jake Schincariol (MIT).
O dicionario abaixo e proprio, em portugues, porque o original e em
ingles e corrompia o texto.
"""

import re
import unicodedata

# 1. Caracteres invisiveis que teclado nenhum produz
INVISIVEIS = [
    "​", "‌", "‍", "⁠", "﻿", "­",
    "᠎", "⁡", "⁢", "⁣", "⁤",
]

# 2. Tipografia
TIPOGRAFIA = [
    ("—", ", "),   # travessao longo
    ("–", "-"),    # travessao curto
    ("“", '"'), ("”", '"'),
    ("‘", "'"), ("’", "'"),
    ("…", "..."),
    ("•", "-"),
]

# 3. Vocabulario batido de IA, em portugues
LEXICO = {
    "é crucial": "importa",
    "é fundamental que": "vale",
    "é essencial que": "vale",
    "no mundo de hoje": "",
    "no mundo atual": "",
    "em um mundo cada vez mais acelerado": "",
    "nos dias de hoje": "hoje",
    "cada vez mais": "",
    "solução robusta": "solução",
    "robusto": "sólido",
    "robusta": "sólida",
    "sem costura": "sem travar",
    "potencialize": "melhore",
    "potencializar": "melhorar",
    "otimize seus resultados": "melhore os resultados",
    "alavancar": "usar",
    "alavanque": "use",
    "revolucionar": "mudar",
    "revolucione": "mude",
    "transforme sua rotina": "mude a sua rotina",
    "descubra agora": "veja",
    "não perca tempo": "",
    "não perca mais tempo": "",
    "imperdível": "",
    "incrível": "",
    "simplesmente": "",
    "literalmente": "",
    "de forma eficaz": "",
    "de maneira eficiente": "",
    "vale ressaltar que": "",
    "é importante destacar que": "",
    "em suma": "",
    "por fim": "",
    "mergulhe": "entre",
    "desvende": "entenda",
    "domine": "aprenda",
    "nunca mais": "",
    # chamadas artificiais, proibidas pelo guia da FisioSync
    "comente sim": "",
    "marque três amigos": "",
    "marque um amigo": "",
    "arrasta pra cima": "",
    "link na bio": "",
    "stop scrolling": "",
    "pare de rolar": "",
    "siga para mais": "",
    "curta e compartilhe": "",
}

# 4. Vicios de estrutura, apenas sinalizados
ESTRUTURA = [
    (r"\bnão é apenas .{3,40}, é\b", "formula 'nao e apenas X, e Y'"),
    (r"\bmais do que .{3,40}, é\b", "formula 'mais do que X, e Y'"),
    (r"^\s*(Olá|Oi|E aí|Fala)\b", "legenda começando com saudação"),
    (r"\b(você sabia que)\b", "'você sabia que' é abertura batida"),
    (r"!{2,}", "exclamações repetidas"),
    (r"\b(\w+)\s+\1\b", "palavra repetida em sequência"),
]


def _limpar_invisiveis(texto):
    n = 0
    for c in INVISIVEIS:
        n += texto.count(c)
        texto = texto.replace(c, "")
    # qualquer outro caractere de formatacao Unicode
    saida = []
    for ch in texto:
        if unicodedata.category(ch) == "Cf":
            n += 1
            continue
        saida.append(ch)
    return "".join(saida), n


def _tipografia(texto):
    n = 0
    for de, para in TIPOGRAFIA:
        n += texto.count(de)
        texto = texto.replace(de, para)
    return texto, n


def _lexico(texto):
    """
    So DETECTA. Nao troca.
    Substituir palavra por regex quebra a frase em portugues: vira
    concordancia errada e pontuacao orfa. Quem reescreve e a IA,
    recebendo esta lista.
    """
    achados = []
    for termo, sugestao in LEXICO.items():
        if re.search(re.escape(termo), texto, re.IGNORECASE):
            achados.append(f"{termo}"
                           + (f" (troque por: {sugestao})" if sugestao
                              else " (corte)"))
    return achados


# Ordem importa: o Instagram limita a 5 e corta o que passar.
# Desde 02/11/2026 o perfil e de conhecimento: a serie e a FisioSyncExplica,
# a mesma dos Reels.
HASHTAGS_PROPRIAS = ["#FisioSync", "#FisioSyncExplica"]


def _hashtags(texto):
    """Mantem no maximo 5 hashtags e garante a #FisioSync."""
    tags = re.findall(r"#\w+", texto)
    if not tags:
        return texto, []
    mudancas = []
    escolhidas = []
    for t in tags:
        if t.lower() not in [e.lower() for e in escolhidas]:
            escolhidas.append(t)

    # Hashtags proprias, sempre na frente: a marca e a serie dos posts de
    # gestao. Hashtag nao da alcance (o Instagram disse isso), mas agrupa a
    # serie e vira o lugar onde quem gostou acha os outros posts.
    for propria in reversed(HASHTAGS_PROPRIAS):
        escolhidas = [t for t in escolhidas if t.lower() != propria.lower()]
        escolhidas.insert(0, propria)
    if not any(t.lower() == "#fisiosync" for t in tags):
        mudancas.append("adicionada a #FisioSync")
    if len(escolhidas) > 5:
        cortadas = escolhidas[5:]
        escolhidas = escolhidas[:5]
        mudancas.append(f"{len(cortadas)} hashtag(s) a mais removida(s): "
                        + " ".join(cortadas))

    corpo = re.sub(r"#\w+", "", texto)
    corpo = re.sub(r"[ \t]{2,}", " ", corpo)
    corpo = re.sub(r"\n{3,}", "\n\n", corpo).rstrip()
    return corpo + "\n\n" + " ".join(escolhidas), mudancas


def _arrumar(texto):
    """Limpa a sujeira que as remocoes deixam."""
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r" +([,.!?;:])", r"\1", texto)
    texto = re.sub(r"([,.!?;:]){2,}", r"\1", texto)
    texto = re.sub(r"^[ \t]*[,.;:]+[ \t]*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    linhas = []
    for linha in texto.split("\n"):
        linha = linha.strip()
        if linha:
            linha = linha[0].upper() + linha[1:] if linha[0].isalpha() else linha
        linhas.append(linha)
    return "\n".join(linhas).strip()


def conferir(texto):
    """Regras do Instagram e do guia da FisioSync."""
    avisos = []

    visivel = texto.split("\n")[0]
    if len(visivel) > 125:
        avisos.append(f"a primeira linha tem {len(visivel)} caracteres; "
                      f"o feed corta em 125")
    if visivel[:1] in ("#", "@"):
        avisos.append("a legenda começa com hashtag ou arroba")
    if visivel[:1] and unicodedata.category(visivel[0]) == "So":
        avisos.append("a legenda começa com emoji")

    tags = re.findall(r"#\w+", texto)
    if len(tags) > 5:
        avisos.append(f"{len(tags)} hashtags; o Instagram limita a 5 desde "
                      f"dezembro de 2025")
    if tags and not any(t.lower() == "#fisiosync" for t in tags):
        avisos.append("faltou a hashtag #FisioSync")

    pedidos = sum(1 for p in ("salve", "salva este", "comente", "comenta",
                              "compartilhe", "compartilha", "envie para",
                              "teste grátis", "experimente")
                  if p in texto.lower())
    if pedidos > 2:
        avisos.append("mais de uma chamada para ação na mesma legenda")

    if len(texto) > 2200:
        avisos.append(f"{len(texto)} caracteres; o limite do Instagram é 2200")

    return avisos


def humanizar(texto):
    """
    Arruma so o que e seguro arrumar por programa e devolve
    (texto_limpo, relatorio). O relatorio lista o que a IA precisa
    reescrever: vocabulario batido, vicios de estrutura e regras.
    """
    original = texto
    texto, n_inv = _limpar_invisiveis(texto)
    texto, n_tip = _tipografia(texto)
    texto = _arrumar(texto)
    texto, mudancas_tags = _hashtags(texto)

    slop = _lexico(texto)
    estrutura = [nome for padrao, nome in ESTRUTURA
                 if re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)]

    relatorio = {
        "invisiveis": n_inv,
        "tipografia": n_tip,
        "hashtags": mudancas_tags,
        "slop": slop,
        "estrutura": estrutura,
        "avisos": conferir(texto),
        "mudou": texto != original,
    }
    relatorio["precisa_reescrever"] = bool(slop or estrutura
                                           or relatorio["avisos"])
    return texto, relatorio


def instrucoes_de_reescrita(relatorio):
    """Transforma o relatorio num pedido curto para a IA reescrever."""
    itens = []
    for s in relatorio["slop"]:
        itens.append(f"- tire a expressão batida: {s}")
    for e in relatorio["estrutura"]:
        itens.append(f"- corrija: {e}")
    for a in relatorio["avisos"]:
        itens.append(f"- {a}")
    return "\n".join(itens)


def imprimir(relatorio, log=print):
    if relatorio["invisiveis"]:
        log(f"  {relatorio['invisiveis']} caractere(s) invisível(is) removido(s)")
    if relatorio["tipografia"]:
        log(f"  {relatorio['tipografia']} correção(ões) de tipografia")
    for t in relatorio.get("hashtags", []):
        log(f"  {t}")
    for s in relatorio["slop"]:
        log(f"  expressão batida: {s}")
    for e in relatorio["estrutura"]:
        log(f"  vício de escrita: {e}")
    for a in relatorio["avisos"]:
        log(f"  ATENÇÃO: {a}")
    if not any((relatorio["invisiveis"], relatorio["tipografia"],
                relatorio.get("hashtags"), relatorio["slop"],
                relatorio["estrutura"], relatorio["avisos"])):
        log("  legenda limpa, nada a corrigir")


if __name__ == "__main__":
    import sys
    entrada = (open(sys.argv[1], encoding="utf-8").read()
               if len(sys.argv) > 1 else sys.stdin.read())
    limpo, rel = humanizar(entrada)
    print(limpo)
    print("\n--- RELATORIO ---")
    imprimir(rel)
