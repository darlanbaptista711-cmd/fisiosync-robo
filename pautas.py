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

# Quantos posts para tras o rodizio olha antes de repetir um eixo.
# Com 8 eixos e 2 posts por dia, 6 cobre os tres ultimos dias.
JANELA_EIXO = 6

# Ate 02/11/2026 havia mistura gestao/dica. Agora e so conhecimento:
# FAMILIA_PADRAO (gestao) fica fora do sorteio em proxima_pauta.
FAMILIA_PADRAO = "gestao"

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


def eixo_do_registro(r, dados):
    """
    Descobre o eixo de um post ja publicado.

    O campo "eixo" gravado no proprio registro e a fonte certa. Antes
    isso era deduzido comparando o tema do historico com o tema da
    pauta, e nunca batia: o que vai para o historico e o tema REESCRITO
    pela IA, nao a frase do banco. Com isso o rodizio de eixo nunca saiu
    do lugar, o banco nunca marcava pauta como usada, e em 31/10/2026 o
    robo publicou dois posts de confirmacao no mesmo dia.

    Registro antigo, sem o campo, ainda cai na comparacao por texto.
    """
    if r.get("eixo"):
        return r["eixo"]
    alvo = r.get("pauta") or r.get("tema", "")
    for p in dados["pautas"]:
        if p["tema"] == alvo:
            return p["eixo"]
    melhor, nota = None, 0.0
    for p in dados["pautas"]:
        s = semelhanca(alvo, p["tema"])
        if s > nota:
            melhor, nota = p["eixo"], s
    return melhor if nota >= 0.45 else None


def familia_do_registro(r, dados):
    """Familia de um post ja publicado, pelo campo ou pela pauta."""
    if r.get("familia"):
        return r["familia"]
    alvo = r.get("pauta") or r.get("tema", "")
    for p in dados["pautas"]:
        if p["tema"] == alvo:
            return p.get("familia", FAMILIA_PADRAO)
    return FAMILIA_PADRAO


def _tem_fato(p):
    """
    Pauta de regulacao so entra no sorteio com o fato preenchido.

    Conteudo factual sem fato no banco vira conteudo inventado pela IA,
    e o briefing proibe inventar estatistica, data ou norma. Sem fato,
    a pauta fica de fora ate alguem escrever o fato e a fonte.
    """
    if p.get("familia") != "regulacao":
        return True
    return bool(p.get("fato") and p.get("fonte"))


def temas_dos_reels(dias=10, proximos=2):
    """
    Titulos dos Reels recentes e dos proximos da fila.

    O feed nao pode repetir no mesmo dia (nem na mesma semana) o assunto
    de um Reels. Em 02/11/2026 o feed das 18h ia sair com "os oito itens
    do prontuario", o mesmo tema do Reels das 20h.
    """
    base = os.path.join(PASTA, "reels")
    titulos, feitos = [], set()
    try:
        with open(os.path.join(base, "historico-reels.json"), encoding="utf-8") as f:
            hist = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        hist = []
    limite = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    for h in hist:
        feitos.add(h.get("titulo"))
        if str(h.get("data_brasilia") or h.get("data") or "")[:10] >= limite:
            titulos.append(h.get("titulo", ""))
    fila = os.path.join(base, "fila")
    if os.path.isdir(fila):
        for nome in sorted(os.listdir(fila)):
            if proximos <= 0:
                break
            if not nome.endswith(".json"):
                continue
            try:
                with open(os.path.join(fila, nome), encoding="utf-8") as f:
                    r = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            if r.get("titulo") in feitos:
                continue
            titulos.append(r.get("titulo", ""))
            proximos -= 1
    return [t for t in titulos if t]


def proxima_pauta(historico, log=print):
    """
    Escolhe a proxima pauta livre, evitando repetir o eixo dos ultimos
    dias, respeitando a mistura de familias e pulando o que ja foi feito.
    """
    dados = carregar()
    livres = [p for p in dados["pautas"]
              if p.get("status") == "livre" and _tem_fato(p)]
    if not livres:
        log("BANCO DE PAUTAS VAZIO. Nenhum tema novo disponivel.")
        return None

    # Decisao do Darlan em 02/11/2026: o perfil passa a ser 100%
    # conhecimento. Gestao/software sai do sorteio; o produto so aparece
    # como assinatura no fim da legenda. E so entra pauta com fato e
    # fonte conferidos: conhecimento sem fonte vira conhecimento inventado.
    livres = [p for p in livres
              if p.get("familia", FAMILIA_PADRAO) != FAMILIA_PADRAO
              and p.get("fato") and p.get("fonte")]
    if not livres:
        log("SEM PAUTA DE CONHECIMENTO CONFERIDA. Abasteca o pautas.json "
            "com fatos de fonte oficial antes de publicar.")
        return None
    log("Vez de: conhecimento")

    # Eixos usados por ultimo, do mais recente para o mais antigo.
    recentes = []
    for r in reversed(historico[-JANELA_EIXO:]):
        e = eixo_do_registro(r, dados)
        if e and e not in recentes:
            recentes.append(e)

    def prioridade(p):
        # Eixo que nao aparece na janela vale mais que qualquer um que
        # apareceu. Entre os que apareceram, ganha o mais antigo.
        # sorted() e estavel, entao o empate mantem a ordem do arquivo.
        e = p.get("eixo", "")
        return recentes.index(e) if e in recentes else len(recentes)

    candidatas = sorted(livres, key=prioridade, reverse=True)

    reels = temas_dos_reels()
    for p in candidatas:
        bate = next((t for t in reels
                     if semelhanca(p["tema"], t) >= LIMITE_TEMA), None)
        if bate:
            # nao marca como usada: volta ao sorteio depois que o Reels sair
            # da janela
            log(f"  pulando '{p['tema']}': mesmo assunto do Reels '{bate}'")
            continue
        parecido, motivo = ja_usado(p["tema"], historico)
        if parecido:
            log(f"  pulando '{p['tema']}': {motivo}")
            p["status"] = "parecida"
            p["usado_em"] = parecido.get("data")
            continue
        salvar(dados)
        log(f"Pauta escolhida: {p['tema']}  "
            f"(eixo {p['eixo']}, familia {p.get('familia', FAMILIA_PADRAO)})")
        if p.get("fato"):
            log(f"  fato conferido: {p['fato'][:90]}...")
            log(f"  fonte: {p['fonte']}")
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


def _usavel(p):
    return (p.get("familia", FAMILIA_PADRAO) != FAMILIA_PADRAO
            and p.get("fato") and p.get("fonte"))


def situacao(log=print):
    """Conta so o que o robo pode usar: conhecimento com fato e fonte."""
    dados = carregar()
    uteis = [p for p in dados["pautas"] if _usavel(p)]
    livres = [p for p in uteis if p.get("status", "livre") == "livre"]
    log(f"Pautas de conhecimento: {len(uteis)} no total, {len(livres)} livres "
        f"(cerca de {len(livres) // 2} dias a 2 posts por dia).")
    for eixo in sorted({p["eixo"] for p in uteis}):
        n = sum(1 for p in livres if p["eixo"] == eixo)
        log(f"  {eixo}: {n} livres")
    if len(livres) <= 15:
        log("\nATENCAO: menos de 15 pautas livres. Hora de conferir fatos "
            "novos em fonte oficial antes que o robo fique sem tema.")
    return len(livres)


if __name__ == "__main__":
    situacao()
