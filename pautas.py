#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banco de pautas e trava contra repeticao.

A garantia NAO vem de pedir para a IA nao repetir. Vem daqui:

  1. Um banco com 120 pautas reais, divididas em 8 eixos.
  2. Cada pauta tem status. Usada, sai do sorteio.
  3. Rodizio de eixo: nao repete o mesmo assunto em dias seguidos.
  4. Trava de semelhanca por codigo, comparando a proposta com TODO o
     historico por sobreposicao de palavras, nao por titulo igual.
  5. Quando o banco esvazia, o robo avisa em vez de inventar.
"""

import datetime
import json
import os
import re
import unicodedata

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_PAUTAS = os.path.join(PASTA, "pautas.json")

# Semelhanca aceita entre uma proposta e qualquer item do historico.
# Acima disso, e o mesmo assunto com outro nome.
LIMITE_TEMA = 0.60      # proposta contra o tema do registro
LIMITE_TEXTO = 0.70     # proposta contra tema + mensagem + conceito

VAZIAS = {
    "a", "o", "as", "os", "de", "do", "da", "dos", "das", "e", "em", "no",
    "na", "nos", "nas", "um", "uma", "para", "por", "com", "sem", "que",
    "se", "ao", "aos", "the", "of", "sua", "seu", "suas", "seus", "mais",
    "menos", "nao", "ja", "quando", "como", "qual", "quais", "voce", "ou",
    "pelo", "pela", "entre", "sobre", "ate", "isso", "esse", "essa",
}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", texto)


def palavras(texto):
    """
    Radicais de 5 letras, para 'avisa' e 'avisar' contarem como a mesma
    ideia. Cru, mas pega as variacoes que mais aparecem em portugues.
    """
    brutas = [p for p in _normalizar(texto).split()
              if len(p) > 2 and p not in VAZIAS]
    return {p[:5] for p in brutas}


def semelhanca(a, b):
    """
    Sobreposicao relativa ao MENOR dos dois textos.

    Jaccard nao serve aqui: o registro do historico e longo (tema +
    mensagem + conceito) e a proposta e curta, entao a uniao explode e
    a semelhanca afunda mesmo quando o assunto e identico.
    """
    pa, pb = palavras(a), palavras(b)
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / min(len(pa), len(pb))


def carregar():
    if not os.path.exists(ARQ_PAUTAS):
        return {"versao": 1, "pautas": []}
    with open(ARQ_PAUTAS, encoding="utf-8") as f:
        return json.load(f)


def salvar(dados):
    with open(ARQ_PAUTAS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def _texto_do_registro(r):
    return " ".join(str(r.get(c, "")) for c in
                    ("tema", "mensagem", "conceito", "chamada", "situacao"))


def ja_usado(proposta, historico):
    """Devolve (registro, motivo) do item parecido, ou (None, None)."""
    for r in historico:
        if r.get("status") == "rejeitado":
            continue
        s_tema = semelhanca(proposta, r.get("tema", ""))
        if s_tema >= LIMITE_TEMA:
            return r, f"tema {int(s_tema*100)}% igual a '{r.get('tema')}'"
        s_txt = semelhanca(proposta, _texto_do_registro(r))
        if s_txt >= LIMITE_TEXTO:
            return r, (f"mesma ideia de '{r.get('tema')}' "
                       f"({int(s_txt*100)}% de sobreposição)")
    return None, None


def proxima_pauta(historico, log=print):
    """
    Escolhe a proxima pauta livre, evitando repetir o eixo dos ultimos
    dias e qualquer coisa parecida com o que ja foi feito.
    """
    dados = carregar()
    livres = [p for p in dados["pautas"] if p.get("status") == "livre"]
    if not livres:
        log("BANCO DE PAUTAS VAZIO. Nenhum tema novo disponivel.")
        return None

    eixos_recentes = []
    for r in historico[-3:]:
        for p in dados["pautas"]:
            if p["tema"] == r.get("tema"):
                eixos_recentes.append(p["eixo"])

    preferidas = [p for p in livres if p["eixo"] not in eixos_recentes]
    candidatas = preferidas or livres

    for p in candidatas:
        parecido, motivo = ja_usado(p["tema"], historico)
        if parecido:
            log(f"  pulando '{p['tema']}': {motivo}")
            p["status"] = "parecida"
            p["usado_em"] = parecido.get("data")
            continue
        salvar(dados)
        log(f"Pauta escolhida: {p['tema']}  (eixo {p['eixo']})")
        log(f"Pautas livres restantes: {len(livres) - 1}")
        return p

    salvar(dados)
    log("Todas as pautas livres sao parecidas com o historico.")
    return None


def marcar_usada(tema, status="publicado"):
    dados = carregar()
    for p in dados["pautas"]:
        if p["tema"] == tema:
            p["status"] = status
            p["usado_em"] = datetime.date.today().isoformat()
            salvar(dados)
            return True
    return False


def situacao(log=print):
    dados = carregar()
    from collections import Counter
    c = Counter(p.get("status", "livre") for p in dados["pautas"])
    total = len(dados["pautas"])
    livres = c.get("livre", 0)
    log(f"Banco de pautas: {total} no total, {livres} livres.")
    for eixo in sorted({p["eixo"] for p in dados["pautas"]}):
        n = sum(1 for p in dados["pautas"]
                if p["eixo"] == eixo and p.get("status") == "livre")
        log(f"  {eixo}: {n} livres")
    if livres <= 15:
        log("\\nATENCAO: menos de 15 pautas livres. Hora de abastecer o "
            "banco com assuntos novos, antes que o robo fique sem tema.")
    return livres


if __name__ == "__main__":
    situacao()
