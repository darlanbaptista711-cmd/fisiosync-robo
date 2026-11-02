#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robo de postagem diaria do Instagram @fisiosyncapp (FisioSync).

Publico: fisioterapeutas que gerenciam a propria agenda e clinica.

Como funciona:
  1. Escolhe um tema do arquivo temas.txt
  2. A IA escreve titulo, texto de apoio e legenda
  3. A IA gera apenas a FOTO (sem nenhum texto na imagem)
  4. O molde.py coloca por cima a logo oficial e os textos
  5. Sobe para o GitHub (vira link publico) e publica no Instagram

Como rodar:
  python postador.py              -> gera e publica (feed + story)
  python postador.py --previa     -> so gera e salva, NAO publica
  python postador.py --so-feed
  python postador.py --so-story
  python postador.py --tema "como reduzir faltas de pacientes"
"""

import argparse
import base64
import datetime
import json
import os
import re
import sys
import time

try:
    import requests
except ImportError:
    print("[ERRO] Falta a biblioteca 'requests'. Rode: pip install requests")
    sys.exit(1)

import humanizador
import layouts
import molde
import pautas as PT

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_CRED = os.path.join(PASTA, "CREDENCIAIS.txt")
ARQ_CHAVES = os.path.join(PASTA, "CHAVES.txt")
ARQ_TEMAS = os.path.join(PASTA, "temas.txt")
PASTA_SAIDA = os.path.join(PASTA, "gerado")

VERSAO_GRAPH = "v23.0"

# LOGO OFICIAL: usar SEMPRE este arquivo. Definido pelo Darlan em 30/10/2026.
# Se o caminho existir e estiver mais novo que o logo.png da pasta,
# o robo recorta a logo de novo a partir daqui, sozinho.
LOGO_ORIGEM = (r"C:\Users\darla\OneDrive\Área de Trabalho"
               r"\FisioSync-20251113T171021Z-1-001\FisioSync"
               r"\Marca d_água\Artboard 10.png")

MODELOS_IMAGEM = [
    "imagen-4.0-ultra-generate-001",
    "imagen-4.0-generate-001",
    "gemini-2.5-flash-image",
    "imagen-4.0-fast-generate-001",
]
MODELOS_TEXTO = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
MODELOS_TEXTO_OPENAI = ["gpt-6-astra"]
MODELOS_IMAGEM_OPENAI = [
    "chatgpt-image-latest",      # o mesmo que o ChatGPT usa
    "gpt-image-2.5-sunburst",
    "gpt-image-2.5-flare",
    "gpt-image-2",
]

# Estilo visual fixo da marca. A foto NUNCA leva texto: o texto e colocado
# depois pelo molde.py, com a tipografia e as cores oficiais.
PASTA_REFS = os.path.join(PASTA, "referencias")

# Paleta e regras que valem para qualquer tratamento
BASE_VISUAL = (
    "pure white seamless background #FFFFFF, "
    "vivid saturated cyan #18B7D8 as the dominant accent, not pastel, not "
    "muted, not dusty teal; deep navy #0B2948 for contrast; light grey "
    "#E8EEF2 only for soft shapes; pure white #FFFFFF background, "
    "the subject must FILL the frame edge to edge with no empty margins, "
    "nothing touching or cut by the frame border, "
    "consistent single-direction studio lighting across every element, "
    "soft contact shadows, crisp edges, coherent volumes and proportions, "
    "no people, no faces, no hands, "
    "no phones, no tablets, no laptops, no app screens, "
    "no text, no letters, no numbers, no logos, no watermarks, "
    "no confetti, no neon, no glow, no floating charts, no gears, "
    "no coins, no banknotes, no currency symbols"
)

# Tratamento visual: escolhido por peca, nunca o mesmo sempre
ESTILOS_VISUAIS = {
    "ilustracao 3D minimalista e sofisticada": (
        "polished 3D advertising illustration, matte surfaces with subtle "
        "texture, rounded but precise geometry, clear recognisable objects, "
        "soft ambient occlusion, advertising render quality"),
    "fotografia realista de produto": (
        "convincing advertising product photography, real materials with "
        "believable texture, plausible proportions, coherent perspective, "
        "shallow but controlled depth of field, sharp on the main subject"),
    "composicao tipografica": (
        "minimal editorial composition, one single graphic element, generous "
        "negative space, flat vector shapes with precise edges"),
    "checklist visual": (
        "clean vector illustration of a short list or sequence, simple "
        "recognisable marks, even spacing, flat shapes with light depth"),
    "icones lineares discretos": (
        "minimal line icons with uniform stroke weight, generous spacing, "
        "flat and quiet, no 3D"),
    "representacao conceitual do beneficio": (
        "simple conceptual illustration that reads instantly, one clear "
        "relationship between two or three recognisable objects, "
        "advertising illustration quality"),
}
ESTILO_PADRAO = ESTILOS_VISUAIS["ilustracao 3D minimalista e sofisticada"]


def referencias_aprovadas(maximo=2):
    """Arquivos de imagem da pasta referencias, enviados na requisicao."""
    if not os.path.isdir(PASTA_REFS):
        return []
    arquivos = sorted(
        os.path.join(PASTA_REFS, n) for n in os.listdir(PASTA_REFS)
        if n.lower().endswith((".png", ".jpg", ".jpeg")))
    return arquivos[:maximo]


FOTOS_RESERVA = [
    "a tidy modern desk with a closed laptop, a small notebook and a cup of "
    "coffee, seen from above",
    "a compact navy professional bag with a rolled cyan resistance band and a "
    "small dumbbell beside it on a white surface",
    "a smartphone lying face down next to a clean notebook and a pen on a "
    "bright white table",
]


# --------------------------------------------------------------------------
# Base
# --------------------------------------------------------------------------

def erro(msg):
    print(f"\n[ERRO] {msg}\n", file=sys.stderr)
    sys.exit(1)


def log(msg):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{agora}] {msg}", flush=True)


def carregar_config():
    cfg = {}
    for arquivo in (ARQ_CRED, ARQ_CHAVES):
        if not os.path.exists(arquivo):
            continue
        with open(arquivo, "r", encoding="utf-8", errors="replace") as f:
            for linha in f:
                linha = linha.strip()
                if linha.startswith("#") or "=" not in linha:
                    continue
                k, _, v = linha.partition("=")
                valor = v.strip().strip('"').strip("'")
                if valor:
                    cfg[k.strip().upper()] = valor

    for chave in ("ID", "TOKEN", "GEMINI_API_KEY", "OPENAI_API_KEY",
                  "GITHUB_TOKEN", "GITHUB_REPO", "MODELO_IMAGEM"):
        if os.environ.get(chave):
            cfg[chave] = os.environ[chave].strip()

    faltando = [c for c in ("ID", "TOKEN") if not cfg.get(c)]
    if faltando:
        erro("Faltam no CREDENCIAIS.txt: " + ", ".join(faltando))
    if not cfg.get("GEMINI_API_KEY") and not cfg.get("OPENAI_API_KEY"):
        erro("Falta a chave da IA. Preencha GEMINI_API_KEY ou OPENAI_API_KEY "
             "no arquivo CHAVES.txt.")
    return cfg


def atualizar_logo(cfg):
    """Mantem o logo.png em dia com o arquivo oficial da marca."""
    origem = cfg.get("LOGO_ORIGINAL") or LOGO_ORIGEM
    if not os.path.exists(origem):
        return
    destino = molde.LOGO
    if (os.path.exists(destino)
            and os.path.getmtime(destino) >= os.path.getmtime(origem)):
        return

    try:
        from PIL import Image, ImageChops
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(origem).convert("RGB")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        dif = ImageChops.difference(im, fundo).convert("L")
        caixa = dif.point(lambda p: 255 if p > 18 else 0).getbbox()
        if not caixa:
            return
        logo = im.crop(caixa).convert("RGBA")
        px = logo.load()
        for y in range(logo.height):
            for x in range(logo.width):
                r, g, b, a = px[x, y]
                if r > 242 and g > 242 and b > 242:
                    px[x, y] = (r, g, b, 0)
        larg = 1400
        logo = logo.resize((larg, int(logo.height * larg / logo.width)),
                           Image.LANCZOS)
        logo.save(destino)
        log(f"Logo oficial atualizada a partir de: {os.path.basename(origem)}")
    except Exception as e:
        log(f"Nao consegui atualizar a logo ({type(e).__name__}: {e}). "
            f"Seguindo com o logo.png atual.")


def escolher_tema(forcado=None):
    if forcado:
        return forcado
    temas = []
    if os.path.exists(ARQ_TEMAS):
        with open(ARQ_TEMAS, "r", encoding="utf-8", errors="replace") as f:
            temas = [t.strip() for t in f
                     if t.strip() and not t.startswith("#")]
    if not temas:
        temas = ["como reduzir faltas de pacientes na clinica"]
    dia = datetime.date.today().timetuple().tm_yday
    return temas[dia % len(temas)]


# --------------------------------------------------------------------------
# IA: texto
# --------------------------------------------------------------------------

ARQ_HISTORICO = os.path.join(PASTA, "historico.json")

OBJETIVOS = ["salvar", "compartilhar", "comentar"]

ESTILOS_ARTE = [
    "ilustracao 3D minimalista e sofisticada",
    "fotografia realista de produto",
    "composicao tipografica",
    "checklist visual",
    "icones lineares discretos",
    "representacao conceitual do beneficio",
]


def ler_historico(limite=25):
    if not os.path.exists(ARQ_HISTORICO):
        return []
    try:
        with open(ARQ_HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)[-limite:]
    except Exception:
        return []


STATUS = ("rascunho", "aprovado", "publicado", "rejeitado")

# -------------------------------------------------------------------
# Janelas de publicacao
#
# O agendador do GitHub e "melhor esforco", nao promessa. Em 31/10/2026
# o cron das 11:55 so disparou as 15:52, quase quatro horas atrasado, e
# o das 18:25 nao disparou. Pedir o horario exato uma vez por dia e
# apostar na sorte.
#
# A solucao: o workflow tenta MUITAS vezes dentro de cada janela, e e o
# codigo que decide se ja publicou. A primeira tentativa que pega
# publica; todas as outras saem na hora, sem gastar API nem pauta.
# -------------------------------------------------------------------

JANELAS = {
    "manha": (10, 16),   # alvo 12:00 em Brasilia
    "tarde": (17, 23),   # alvo 18:00 em Brasilia
}


def agora_brasilia():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=3)


def janela_agora():
    """Devolve (data em Brasilia, nome da janela) ou (data, None)."""
    agora = agora_brasilia()
    for nome, (ini, fim) in JANELAS.items():
        if ini <= agora.hour <= fim:
            return agora.date().isoformat(), nome
    return agora.date().isoformat(), None


def ja_publicou_nesta_janela():
    """
    True se esta janela de hoje ja tem post publicado.

    E isto que impede a rajada de tentativas virar uma rajada de posts.
    """
    data, janela = janela_agora()
    if not janela:
        return False
    for r in ler_historico(limite=40):
        if (r.get("status") == "publicado"
                and r.get("data") == data
                and r.get("janela") == janela):
            return True
    return False


def registro_completo(c, tema, arquivos, status="rascunho", modo="molde"):
    """Registro editorial exigido pelo projeto."""
    data, janela = janela_agora()
    return {
        "data": data or datetime.date.today().isoformat(),
        "janela": janela or "",
        "tema": tema,
        "pauta": c.get("pauta", tema),
        "eixo": c.get("eixo", ""),
        "familia": c.get("familia", "gestao"),
        "fonte": c.get("fonte", ""),
        "publico": c.get("publico", "fisioterapeutas e gestores de clinica"),
        "situacao": c.get("situacao", ""),
        "mensagem": c.get("mensagem", c.get("apoio", "")),
        "chamada": c.get("titulo", ""),
        "conceito": c.get("conceito", ""),
        "composicao": c.get("layout", ""),
        "estilo": c.get("estilo", ""),
        "objetivo": c.get("objetivo", ""),
        "arquivos": [os.path.basename(a) for a in arquivos if a],
        "status": status if status in STATUS else "rascunho",
        "modo": modo,
    }


def gravar_historico(registro):
    try:
        # pela frase do BANCO, nao pelo tema reescrito pela IA
        PT.marcar_usada(registro.get("pauta") or registro.get("tema", ""),
                        registro.get("status"))
    except Exception:
        pass
    hist = []
    if os.path.exists(ARQ_HISTORICO):
        try:
            with open(ARQ_HISTORICO, "r", encoding="utf-8") as f:
                hist = json.load(f)
        except Exception:
            hist = []
    hist.append(registro)
    try:
        with open(ARQ_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(hist[-200:], f, ensure_ascii=False, indent=1)
    except Exception as e:
        log(f"Nao consegui gravar o historico: {e}")


def _pedido_conteudo(tema_sugerido=None, fato="", fonte=""):
    hist = ler_historico()
    if hist:
        recentes = "\n".join(
            f"  - {h.get('data', '?')}: {h.get('tema', '?')} "
            f"(objetivo: {h.get('objetivo', '?')}, estilo: "
            f"{h.get('estilo', '?')})" for h in hist[-15:])
        bloco_hist = (
            "\nHISTORICO. Compare o SIGNIFICADO da sua proposta com estes, "
            "nao so o titulo. Sinonimo, titulo novo ou troca de objeto NAO "
            "e tema novo. Se a sua ideia repetir o mesmo problema, a mesma "
            "mensagem ou o mesmo beneficio de algum destes, descarte e "
            "escolha outra:\n" + recentes + "\n")
        usados = [h.get("objetivo") for h in hist[-3:]]
        sugerir = [o for o in OBJETIVOS if o not in usados] or OBJETIVOS
        usados_e = [h.get("estilo") for h in hist[-3:]]
        sugerir_e = [e for e in ESTILOS_ARTE if e not in usados_e] or ESTILOS_ARTE
    else:
        bloco_hist = "\nAinda nao ha historico: escolha livremente.\n"
        sugerir, sugerir_e = OBJETIVOS, ESTILOS_ARTE

    linha_tema = (f"\nO tema de hoje foi definido: {tema_sugerido}\n"
                  if tema_sugerido else
                  "\nESCOLHA O TEMA VOCE MESMO. Nao peca tema a ninguem.\n")

    # Pauta factual: o fato ja vem conferido do banco. A IA escreve EM
    # VOLTA dele e nao acrescenta nada verificavel por conta propria.
    if fato:
        bloco_fato = (
            "\n=== FATO CONFERIDO, USE EXATAMENTE ESTE ===\n"
            f"{fato}\n"
            f"Fonte: {fonte}\n"
            "\nREGRAS DESTE POST, sem excecao:\n"
            "- Escreva em volta deste fato. Ele e o conteudo.\n"
            "- PROIBIDO citar qualquer outro numero, ano, prazo, "
            "percentual, artigo de lei ou numero de resolucao que nao "
            "esteja escrito acima. Se voce nao tem certeza, nao escreva.\n"
            "- PROIBIDO dizer que a FisioSync garante conformidade legal. "
            "O software ajuda a organizar o registro; quem responde pelo "
            "cumprimento da norma e o profissional.\n"
            "- Cite a fonte na legenda, do jeito que esta acima.\n"
            "- Nada de orientacao clinica ou de consultoria juridica: "
            "informe o que a norma diz e pare ai.\n"
            "=== FIM DO FATO ===\n")
    else:
        bloco_fato = ("\nEste tema e de rotina e decisao profissional, nao "
                      "de norma. NAO cite lei, resolucao, estatistica, "
                      "percentual nem data historica: voce nao tem fonte "
                      "para isso e inventar esta proibido.\n")

    return (
        "Voce e o estrategista de conteudo e diretor de arte senior do "
        "perfil @fisiosyncapp. O perfil e de CONHECIMENTO: cada post ensina "
        "algo verdadeiro e util sobre fisioterapia, Pilates, quiropraxia, "
        "osteopatia ou a profissao, com fonte. NAO e post de produto: nao "
        "venda, nao fale de software no titulo, no apoio nem na imagem. A "
        "FisioSync (software de gestao para fisioterapeutas, teste gratis de "
        "7 dias) aparece SO na ultima linha da legenda, como assinatura.\n"
        "Publico: fisioterapeutas, estudantes, gestores de clinica e donos "
        "de estudio de Pilates. Nao sao pacientes.\n"
        "O post bom e aquele que o fisioterapeuta manda para um colega "
        "dizendo 'voce sabia disso?' ou salva para consultar depois.\n"
        + linha_tema + bloco_fato + bloco_hist +
        f"\nObjetivos ainda nao usados recentemente: {', '.join(sugerir)}\n"
        f"Estilos de arte ainda nao usados: {', '.join(sugerir_e)}\n"
        "\nEscolha UM objetivo principal e UM estilo de arte. "
        "Nao peca salvar, comentar e testar ao mesmo tempo.\n"
        "\nResponda SOMENTE com um JSON valido, sem cercas de codigo, com "
        "estas chaves:\n"
        '  "tema": o assunto escolhido, em poucas palavras.\n'
        '  "objetivo": um entre salvar, compartilhar, comentar.\n'
        '  "estilo": o estilo de arte escolhido.\n'
        '  "sobretitulo": rotulo curto de contexto, ate 5 palavras, tipo '
        "'Voce sabia?', 'Norma do COFFITO' ou 'Especialidades'. Pode vir "
        "vazio. Nunca cite a FisioSync aqui.\n"
        '  "conceito": UMA frase objetiva dizendo o que a imagem comunica e '
        "por que. Antes de responder, pense em tres caminhos visuais "
        "diferentes e escolha o mais claro. Nao vale 'objetos 3D premium', "
        "'tecnologia moderna' nem 'imagem sofisticada': isso nao e conceito.\n"
        '  "layout": "calibrado" quando a peca tiver ilustracao, ou '
        '"tipografico" quando a mensagem funcionar so com tipografia. '
        "O padrao visual esta travado nesses dois.\n"
        '  "titulo": chamada curta e forte, no maximo 8 palavras, sem ponto '
        "final. Tem que expressar uma ACAO, uma SITUACAO ou uma MUDANCA. "
        "NAO pode ser o nome de um recurso: 'Evolucao clinica por audio' e "
        "nome de recurso e esta proibido. 'Fale a evolucao, ela entra no "
        "prontuario' e uma acao e esta certo.\n"
        '  "apoio": UMA frase curta que desenvolve o tema escolhido, no '
        "maximo 14 palavras e 110 caracteres, terminada em ponto. Ela e "
        "desenhada na arte em no maximo tres linhas: frase longa nao cabe "
        "e a peca inteira e descartada. PROIBIDO listar funcionalidades: "
        "nao escreva "
        "'A FisioSync reune agenda online, prontuario digital e evolucao por "
        "audio'. Fale do assunto do dia, nao do catalogo.\n"
        '  "legenda": abertura que desperte curiosidade, o fato explicado em '
        "linguagem simples, a fonte citada, UMA chamada coerente com o "
        "objetivo (salvar, mandar para um colega ou responder uma pergunta "
        "nos comentarios), depois a assinatura em uma linha, copiada com "
        "os acentos: 'Conteúdo FisioSync. Teste grátis por 7 dias: "
        "app.fisiosync.com.br'. Legenda inteira com acentuacao correta. "
        "Depois "
        "de uma linha em branco, de 3 a 5 hashtags do assunto, incluindo "
        "#FisioSync.\n"
        '  "foto": descricao EM INGLES do elemento visual, detalhando objeto '
        "principal, complementares, materiais, texturas, proporcoes, "
        "enquadramento, angulo, iluminacao de estudio e sombras de contato. "
        "Cada objeto precisa ter funcao na mensagem: se der para tirar sem "
        "perder sentido, tire. SEM pessoas, rostos ou maos. SEM celulares, "
        "tablets ou computadores. SEM texto na imagem. Nao caia sempre em "
        "pasta, onda sonora, relogio, engrenagem ou grafico flutuando.\n"
        "\nA imagem tem que explicar sozinha. Se o paragrafo for necessario para "
        "a imagem fazer sentido, o conceito esta fraco. Se um objeto puder "
        "sair sem perda de sentido, tire.\n"
        "\nProibido: sensacionalismo, promessa de resultado, 'comente SIM', "
        "'marque tres amigos', frases genericas, preco, desconto, cupom ou "
        "Black Friday. Trate a marca no feminino: a FisioSync."
    )


def _extrair_json(texto):
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.MULTILINE).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        return None
    try:
        return json.loads(texto[inicio:fim + 1])
    except json.JSONDecodeError:
        return None


def encurtar(texto, limite, rotulo=""):
    """
    Encurta SEM deixar frase pela metade.

    Corta na ultima pontuacao de fim de frase que cabe. Se nao houver,
    corta na ultima virgula e fecha com ponto. So no ultimo caso corta
    na palavra, e ainda assim fecha a frase.

    O prompt ja pede frase curta, mas pedir nao e garantir: em
    01/11/2026 a IA mandou 16 palavras, a arte so tinha espaco para
    duas linhas, e foi publicado "e deixar claras as condicoes do".
    """
    texto = (texto or "").strip()
    if len(texto) <= limite:
        return texto

    recorte = texto[:limite]
    for marcas, fecho in ((".!?", ""), (",;:", ".")):
        corte = max(recorte.rfind(c) for c in marcas)
        # so vale se sobrar frase de verdade, nao tres palavras
        if corte >= limite * 0.55:
            novo = recorte[:corte].rstrip(" ,;:") + fecho
            log(f"AVISO: {rotulo} tinha {len(texto)} caracteres e nao "
                f"caberia na arte. Encurtado para: {novo}")
            return novo

    novo = recorte.rsplit(" ", 1)[0].rstrip(" ,;:") + "."
    log(f"AVISO: {rotulo} tinha {len(texto)} caracteres sem pontuacao "
        f"aproveitavel. Encurtado para: {novo}")
    return novo


# Numeros que podem aparecer em qualquer peca sem vir de um fato:
# sao do proprio produto, nao do mundo.
NUMEROS_DA_CASA = {"7", "1", "2", "3", "24", "2026"}


def numeros_soltos(textos, fato=""):
    """
    Numeros escritos na peca que NAO estao no fato conferido.

    Esta e a ultima linha de defesa contra o risco que vem junto com
    conteudo de curiosidade: a IA escreve "desde 1969" ou "em 68% dos
    casos" com total confianca e aquilo vai ao ar no perfil de um
    produto de saude. Numero sem lastro nao sai.
    """
    permitidos = set(re.findall(r"\d+", fato or "")) | NUMEROS_DA_CASA
    achados = set()
    for t in textos:
        achados |= set(re.findall(r"\d+", t or ""))
    return sorted(achados - permitidos)


def conferir_numeros(cfg, dados, fato):
    """
    Confere os numeros da peca; se houver invencao, pede UMA reescrita.
    Se insistir, devolve a lista do que sobrou para o chamador abortar.
    """
    campos = ("titulo", "apoio", "legenda")
    soltos = numeros_soltos([dados.get(c, "") for c in campos], fato)
    if not soltos:
        return []

    log(f"AVISO: numero sem lastro na peca: {', '.join(soltos)}. "
        "Pedindo reescrita.")
    pedido = (
        "Reescreva os tres campos abaixo REMOVENDO os numeros "
        f"{', '.join(soltos)}, que nao tem fonte e nao podem ser "
        "publicados. Mantenha o sentido e o tom. "
        + (f"O unico fato com fonte e: {fato}\n" if fato else
           "Nao existe fato com fonte para este post: escreva sem "
           "numero nenhum.\n")
        + "Responda SOMENTE um JSON com as chaves titulo, apoio e legenda.\n\n"
        + json.dumps({c: dados.get(c, "") for c in campos},
                     ensure_ascii=False))

    bruto = None
    if cfg.get("OPENAI_API_KEY"):
        bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    novo = _extrair_json(bruto) if bruto else None
    if novo:
        for c in campos:
            if novo.get(c):
                dados[c] = novo[c]

    return numeros_soltos([dados.get(c, "") for c in campos], fato)


def gerar_conteudo(cfg, tema=None):
    hist = ler_historico(limite=500)
    pauta_banco, eixo_banco, familia_banco = "", "", "gestao"
    fato_banco, fonte_banco = "", ""

    if not tema:
        # A pauta sai do banco, nao da cabeca do modelo. A trava contra
        # repeticao e de codigo, nao de pedido educado ao modelo.
        p = PT.proxima_pauta(hist, log)
        if not p:
            erro("O banco de pautas acabou ou tudo que sobrou ja foi "
                 "usado.\n  Nao vou inventar funcionalidade para encher "
                 "calendario.\n  Abasteca o pautas.json com assuntos novos "
                 "e rode de novo.\n  Veja a situacao com: python pautas.py")
        tema = p["tema"]
        # A frase original do banco e o eixo viajam junto com o
        # conteudo. A IA reescreve o "tema"; a identidade da pauta nao
        # pode depender desse texto reescrito, senao o banco nunca sabe
        # o que ja saiu e o rodizio de eixo para de funcionar.
        pauta_banco, eixo_banco = p["tema"], p.get("eixo", "")
        familia_banco = p.get("familia", "gestao")
        fato_banco, fonte_banco = p.get("fato", ""), p.get("fonte", "")
    log(f"Escrevendo o conteudo sobre: {tema}")
    pedido = _pedido_conteudo(tema, fato_banco, fonte_banco)

    bruto = None
    if cfg.get("OPENAI_API_KEY"):
        bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    if not bruto and cfg.get("GEMINI_API_KEY"):
        bruto = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)

    dados = _extrair_json(bruto) if bruto else None
    if not dados or not dados.get("titulo"):
        log("AVISO: a IA nao devolveu o conteudo esperado. Usando reserva.")
        base = tema or escolher_tema()
        return {
            "tema": base,
            "pauta": pauta_banco or base,
            "eixo": eixo_banco,
            "objetivo": "salvar",
            "estilo": ESTILOS_ARTE[0],
            "titulo": base[:60].capitalize(),
            # reserva de conhecimento: so o fato conferido e a fonte, nada
            # escrito de cabeca
            "apoio": (encurtar(fato_banco, 118, "apoio")
                      if fato_banco else "Você sabia disso?"),
            "familia": familia_banco,
            "fonte": fonte_banco,
            "legenda": (f"Você sabia? {base.capitalize()}.\n\n"
                        + (f"{fato_banco}\n\nFonte: {fonte_banco}\n\n"
                           if fato_banco else "")
                        + "Salve para consultar depois.\n\n"
                        "Conteúdo FisioSync. Teste grátis por 7 dias: "
                        "app.fisiosync.com.br\n\n"
                        "#FisioSync #FisioSyncExplica #fisioterapia "
                        "#coffito #fisioterapeuta"),
            "foto": FOTOS_RESERVA[datetime.date.today().day % len(FOTOS_RESERVA)],
        }

    dados.setdefault("tema", tema or "tema livre")
    dados.setdefault("objetivo", "salvar")
    dados.setdefault("estilo", ESTILOS_ARTE[0])
    dados.setdefault("conceito", "")
    dados.setdefault("sobretitulo", "")
    import layouts as _LY
    if dados.get("layout") not in _LY.LAYOUTS:
        hist = ler_historico()
        usados = [h.get("layout") for h in hist[-3:]]
        livres = [l for l in _LY.LAYOUTS if l not in usados] or _LY.LAYOUTS
        dados["layout"] = livres[0]
    if dados.get("conceito"):
        log(f"Conceito: {dados['conceito']}")
    log(f"Layout: {dados['layout']}")
    for chave, reserva in (("apoio", ""), ("legenda", ""),
                           ("foto", FOTOS_RESERVA[0])):
        if not dados.get(chave):
            dados[chave] = reserva
    # segunda trava: o modelo pode ter desviado para algo ja feito
    parecido, motivo = PT.ja_usado(
        f"{dados.get('tema','')} {dados.get('conceito','')}",
        ler_historico(limite=500))
    if parecido:
        log(f"AVISO: a proposta repete o historico ({motivo}).")
        log("Mantendo o tema do banco de pautas e seguindo.")
        dados["tema"] = tema or dados.get("tema", "")
    sobraram = conferir_numeros(cfg, dados, fato_banco)
    if sobraram:
        erro("A peca cita numero que nao tem fonte, e a reescrita nao "
             f"resolveu: {', '.join(sobraram)}.\n"
             "  Nao vou publicar dado inventado em perfil de produto de "
             "saude.\n  Rode de novo: a IA escreve outro texto.")

    dados["titulo"] = encurtar(dados["titulo"], 62, "titulo")
    dados["apoio"] = encurtar(dados.get("apoio", ""), 118, "apoio")
    dados["pauta"] = pauta_banco or dados.get("tema", "")
    dados["eixo"] = eixo_banco
    dados["familia"] = familia_banco
    dados["fonte"] = fonte_banco
    log(f"Tema escolhido: {dados['tema']}")
    if eixo_banco:
        log(f"Eixo: {eixo_banco}  (pauta do banco: {pauta_banco})")
    log(f"Objetivo: {dados['objetivo']} | Estilo: {dados['estilo']}")
    log(f"Titulo: {dados['titulo']}")
    return dados


def revisar_legenda(cfg, legenda):
    """
    Limpa a legenda e, se sobrar vicio de IA, pede UMA reescrita ao modelo.
    Quem reescreve e a IA; o programa so arruma o que e seguro.
    """
    log("Revisando a legenda...")
    limpa, rel = humanizador.humanizar(legenda)
    humanizador.imprimir(rel, log)

    if not rel["precisa_reescrever"]:
        return limpa

    pedido = (
        "Reescreva a legenda de Instagram abaixo em portugues do Brasil, "
        "corrigindo os problemas apontados. Mantenha o mesmo assunto, o mesmo "
        "tamanho aproximado e a mesma unica chamada para acao. Escreva como "
        "uma pessoa escreve, sem vocabulario de IA.\n\n"
        f"PROBLEMAS:\n{humanizador.instrucoes_de_reescrita(rel)}\n\n"
        f"LEGENDA:\n{limpa}\n\n"
        "Responda SOMENTE com a legenda corrigida, sem explicacao e sem aspas."
    )

    novo = None
    if cfg.get("OPENAI_API_KEY"):
        novo = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    if not novo and cfg.get("GEMINI_API_KEY"):
        novo = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)

    if not novo:
        log("  nao consegui reescrever; seguindo com a versao limpa")
        return limpa

    final, rel2 = humanizador.humanizar(novo.strip())
    log("  legenda reescrita pela IA. Conferindo de novo:")
    humanizador.imprimir(rel2, log)
    return final


def _gemini_texto(chave, pedido):
    for modelo in MODELOS_TEXTO:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{modelo}:generateContent")
        try:
            r = requests.post(
                url,
                headers={"x-goog-api-key": chave,
                         "Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": pedido}]}]},
                timeout=120)
            if r.status_code == 200:
                log(f"Texto escrito pelo Google ({modelo})")
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            log(f"  {modelo} nao deu: {r.status_code}")
        except Exception as e:
            log(f"  {modelo} falhou: {e}")
    return None


def _openai_modelos(chave, filtro):
    try:
        r = requests.get("https://api.openai.com/v1/models",
                         headers={"Authorization": f"Bearer {chave}"},
                         timeout=60)
        if r.status_code != 200:
            return []
        nomes = [m.get("id", "") for m in r.json().get("data", [])]
        return sorted([n for n in nomes if filtro(n)], reverse=True)
    except Exception:
        return []


def _openai_texto(chave, pedido):
    candidatos = list(MODELOS_TEXTO_OPENAI)
    tentou_listar = False
    while candidatos:
        modelo = candidatos.pop(0)
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {chave}",
                         "Content-Type": "application/json"},
                json={"model": modelo,
                      "messages": [{"role": "user", "content": pedido}]},
                timeout=180)
            if r.status_code == 200:
                log(f"Texto escrito pela OpenAI ({modelo})")
                return r.json()["choices"][0]["message"]["content"]
            log(f"  {modelo} nao deu: {r.status_code} {r.text[:200]}")
        except Exception as e:
            log(f"  {modelo} falhou: {e}")
        if not candidatos and not tentou_listar:
            tentou_listar = True
            achados = _openai_modelos(
                chave,
                lambda n: n.startswith("gpt") and not any(
                    x in n for x in ("image", "audio", "realtime",
                                     "transcribe", "tts", "embed")))
            candidatos = [m for m in achados
                          if m not in MODELOS_TEXTO_OPENAI][:3]
    return None


# --------------------------------------------------------------------------
# IA: foto
# --------------------------------------------------------------------------

def gerar_foto(cfg, c, destino, layout="editorial"):
    """
    Gera a imagem da peca.

    O pedido leva: conceito, descricao dos elementos, tratamento visual
    escolhido, espaco negativo exigido pelo layout e a paleta. As
    referencias aprovadas vao na PROPRIA requisicao, como imagem, nao
    como caminho citado no texto.
    """
    import layouts as _LY

    espaco = _LY.ESPACO_NEGATIVO.get(layout, "")
    tratamento = ESTILOS_VISUAIS.get(c.get("estilo", ""), ESTILO_PADRAO)
    partes = []
    if c.get("conceito"):
        partes.append(f"Concept to communicate: {c['conceito']}")
    partes.append(c.get("foto", ""))
    if espaco:
        partes.append(espaco)
    partes.append(tratamento)
    partes.append(BASE_VISUAL)
    prompt = ". ".join(p.strip().rstrip(".") for p in partes if p) + "."

    refs = referencias_aprovadas()
    if refs and cfg.get("OPENAI_API_KEY"):
        log(f"  referência aprovada enviada: "
            f"{', '.join(os.path.basename(r) for r in refs)}")
        dados = _openai_com_referencia(cfg["OPENAI_API_KEY"], prompt, refs,
                                       cfg.get("MODELO_IMAGEM"),
                                       TAMANHO_POR_LAYOUT.get(layout,
                                                              "1024x1536"))
        if dados:
            open(destino, "wb").write(dados)
            return destino
        log("  não deu com referência; gerando sem ela")

    if cfg.get("OPENAI_API_KEY"):
        dados = _openai_imagem(cfg["OPENAI_API_KEY"], prompt,
                               cfg.get("MODELO_IMAGEM"),
                               TAMANHO_POR_LAYOUT.get(layout, "1024x1536"))
        if dados:
            open(destino, "wb").write(dados)
            return destino
        log("OpenAI não deu certo; tentando o Google.")

    chave = cfg.get("GEMINI_API_KEY")
    if chave:
        preferido = cfg.get("MODELO_IMAGEM")
        modelos = ([preferido] if preferido else []) + [
            m for m in MODELOS_IMAGEM if m != preferido]
        for modelo in modelos:
            try:
                dados = (_imagen(chave, modelo, prompt)
                         if modelo.startswith("imagen")
                         else _gemini_imagem(chave, modelo, prompt))
            except Exception as e:
                log(f"  {modelo} falhou: {e}")
                continue
            if dados:
                open(destino, "wb").write(dados)
                log(f"Imagem gerada por {modelo} ({len(dados)//1024} KB)")
                return destino
        _listar_modelos_google(chave)

    erro("Nao consegui gerar a imagem com nenhum modelo disponivel.")


INSTRUCAO_REFERENCIA = (
    "The attached image is an APPROVED QUALITY REFERENCE from this brand. "
    "Match its finish: illustration craft, recognisable objects, consistent "
    "lighting, soft contact shadows, colour palette and overall polish. "
    "Do NOT reproduce its subject, its microphone, its documents, its wavy "
    "background shape, its layout or any of its text, logo or store badges. "
    "Create a completely different scene for the concept described below, "
    "with no text anywhere in the image."
)


TAMANHO_POR_LAYOUT = {
    "calibrado": "1536x1024",   # cena horizontal, como a referencia
    "editorial": "1536x1024",
    "detalhe": "1536x1024",
    "lateral": "1024x1536",
    "objeto": "1024x1024",
    "centro": "1024x1024",
}


def _openai_com_referencia(chave, prompt, refs, preferido=None,
                           tamanho="1024x1536"):
    """Endpoint de edicao: manda a referencia aprovada junto do pedido."""
    candidatos = ([preferido] if preferido else []) + [
        m for m in MODELOS_IMAGEM_OPENAI if m != preferido]
    corpo = f"{INSTRUCAO_REFERENCIA}\n\n{prompt}"

    for modelo in candidatos:
        arquivos = []
        try:
            for caminho in refs:
                arquivos.append(("image[]", (os.path.basename(caminho),
                                             open(caminho, "rb"), "image/png")))
            r = requests.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {chave}"},
                data={"model": modelo, "prompt": corpo, "size": tamanho,
                      "quality": "high", "n": "1", "input_fidelity": "low"},
                files=arquivos, timeout=600)
            if r.status_code == 200:
                log(f"  imagem gerada por {modelo}, com referência")
                return base64.b64decode(r.json()["data"][0]["b64_json"])
            log(f"  {modelo} com referência não deu: {r.status_code} "
                f"{r.text[:200]}")
        except Exception as e:
            log(f"  {modelo} com referência falhou: {type(e).__name__}: {e}")
        finally:
            for _, (_, fh, _) in arquivos:
                try:
                    fh.close()
                except Exception:
                    pass
    return None


def _imagen(chave, modelo, prompt):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:predict",
        headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
        json={"instances": [{"prompt": prompt}],
              "parameters": {"sampleCount": 1, "aspectRatio": "3:4"}},
        timeout=240)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    preds = r.json().get("predictions", [])
    if not preds:
        raise RuntimeError("resposta sem imagem")
    return base64.b64decode(preds[0]["bytesBase64Encoded"])


def _gemini_imagem(chave, modelo, prompt):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
        headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"responseModalities": ["IMAGE"],
                                   "imageConfig": {"aspectRatio": "3:4"}}},
        timeout=240)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    for cand in r.json().get("candidates", []):
        for parte in cand.get("content", {}).get("parts", []):
            inline = parte.get("inlineData") or parte.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError("resposta sem imagem")


def _openai_imagem(chave, prompt, preferido=None,
                   tamanho="1024x1536"):
    candidatos = list(MODELOS_IMAGEM_OPENAI)
    if preferido:
        candidatos = [preferido] + [m for m in candidatos if m != preferido]
    tentou_listar = False
    while candidatos:
        modelo = candidatos.pop(0)
        try:
            r = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {chave}",
                         "Content-Type": "application/json"},
                json={"model": modelo, "prompt": prompt,
                      "size": tamanho, "quality": "high", "n": 1},
                timeout=300)
            if r.status_code == 200:
                log(f"Foto gerada pela OpenAI ({modelo})")
                return base64.b64decode(r.json()["data"][0]["b64_json"])
            log(f"  {modelo} nao deu: {r.status_code} {r.text[:200]}")
        except Exception as e:
            log(f"  {modelo} falhou: {e}")
        if not candidatos and not tentou_listar:
            tentou_listar = True
            achados = _openai_modelos(
                chave, lambda n: "image" in n and "gpt" in n)
            candidatos = [m for m in achados if m not in MODELOS_IMAGEM_OPENAI]
            if candidatos:
                log(f"  modelos de imagem na conta: {', '.join(candidatos)}")
    return None


def _listar_modelos_google(chave):
    try:
        r = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": chave}, timeout=60)
        if r.status_code == 200:
            nomes = [m.get("name", "").replace("models/", "")
                     for m in r.json().get("models", [])]
            img = [n for n in nomes if "image" in n or "imagen" in n]
            log("Modelos de imagem na sua conta Google: "
                + (", ".join(img) if img else "nenhum"))
            log("Coloque um deles em MODELO_IMAGEM no CHAVES.txt.")
    except Exception:
        pass


# --------------------------------------------------------------------------
# Hospedagem e publicacao
# --------------------------------------------------------------------------

NOME_REPO_PADRAO = "fisiosync-robo"


def descobrir_repo(token):
    """
    Descobre o repositorio sozinho quando o GITHUB_REPO nao foi
    preenchido: pergunta ao GitHub quem e o dono do token e monta
    usuario/fisiosync-robo, conferindo se existe.
    """
    try:
        r = requests.get("https://api.github.com/user",
                         headers={"Authorization": f"Bearer {token}",
                                  "Accept": "application/vnd.github+json"},
                         timeout=60)
        if r.status_code != 200:
            return None
        usuario = r.json().get("login")
        repo = f"{usuario}/{NOME_REPO_PADRAO}"
        c = requests.get(f"https://api.github.com/repos/{repo}",
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=60)
        if c.status_code == 200:
            log(f"Repositorio descoberto automaticamente: {repo}")
            return repo
    except Exception:
        pass
    return None


def subir_para_github(cfg, caminho, nome_remoto):
    token = cfg.get("GITHUB_TOKEN")
    repo = cfg.get("GITHUB_REPO")
    if token and not repo:
        repo = descobrir_repo(token)
        if repo:
            cfg["GITHUB_REPO"] = repo
    if not token or not repo:
        erro("Faltam GITHUB_TOKEN e GITHUB_REPO no CHAVES.txt.\n"
             "GITHUB_REPO deve ser assim: seu-usuario/nome-do-repositorio")

    with open(caminho, "rb") as f:
        conteudo = base64.b64encode(f.read()).decode()

    caminho_remoto = f"imagens/{nome_remoto}"
    url = f"https://api.github.com/repos/{repo}/contents/{caminho_remoto}"
    cab = {"Authorization": f"Bearer {token}",
           "Accept": "application/vnd.github+json"}

    sha = None
    try:
        g = requests.get(url, headers=cab, timeout=60)
        if g.status_code == 200:
            sha = g.json().get("sha")
    except Exception:
        pass

    corpo = {"message": f"imagem {nome_remoto}", "content": conteudo}
    if sha:
        corpo["sha"] = sha

    r = requests.put(url, headers=cab, json=corpo, timeout=180)
    if r.status_code not in (200, 201):
        erro(f"Nao consegui subir a imagem para o GitHub.\n"
             f"  HTTP {r.status_code}: {r.text[:300]}\n"
             f"  Confira o GITHUB_REPO e se o token tem permissao 'repo'.")

    link = r.json().get("content", {}).get("download_url")
    if not link:
        link = (f"https://raw.githubusercontent.com/{repo}/main/"
                f"{caminho_remoto}")
    log(f"Imagem publicada em: {link}")
    return link


def graph(metodo, caminho, token, fatal=True, **params):
    params["access_token"] = token
    url = f"https://graph.facebook.com/{VERSAO_GRAPH}/{caminho.lstrip('/')}"
    r = (requests.get(url, params=params, timeout=90) if metodo == "GET"
         else requests.post(url, data=params, timeout=90))
    try:
        d = r.json()
    except ValueError:
        if not fatal:
            return None
        erro(f"Resposta inesperada da Meta ({r.status_code}): {r.text[:200]}")
    if r.status_code >= 400 or "error" in d:
        e = d.get("error", {})
        msg = f"A Meta recusou: codigo {e.get('code')} - {e.get('message')}"
        if not fatal:
            log("  " + msg)
            return None
        erro(msg)
    return d


def publicar(cfg, link_imagem, legenda=None, story=False, fatal=True):
    ig, tok = cfg["ID"], cfg["TOKEN"]
    tipo = "story" if story else "feed"
    log(f"Publicando no {tipo}...")

    params = {"image_url": link_imagem}
    if story:
        params["media_type"] = "STORIES"
    else:
        params["caption"] = legenda or ""

    resposta = graph("POST", f"{ig}/media", tok, fatal=fatal, **params)
    if resposta is None:
        return None
    container = resposta["id"]

    inicio = time.time()
    while time.time() - inicio < 180:
        st = graph("GET", container, tok, fields="status_code,status")
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            if not fatal:
                log(f"  a Meta nao aceitou a imagem: {st.get('status')}")
                return None
            erro(f"A Meta nao aceitou a imagem: {st.get('status')}")
        time.sleep(5)
    else:
        if not fatal:
            return None
        erro("A Meta demorou demais processando a imagem.")

    media_id = graph("POST", f"{ig}/media_publish", tok,
                     creation_id=container)["id"]
    try:
        link = graph("GET", media_id, tok, fields="permalink").get("permalink")
    except SystemExit:
        link = "(sem link)"
    log(f"PUBLICADO no {tipo}: {link}")
    return media_id


def publicar_feed(cfg, arquivo, legenda, carimbo):
    """Feed em 4:5 (1080x1350), que e o formato que a API aceita."""
    link = subir_para_github(cfg, arquivo, f"feed-{carimbo}.jpg")
    publicar(cfg, link, legenda=legenda, story=False)
    return True


# --------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------

def _fluxo_completo(cfg, args, tema, c, carimbo):
    """A IA desenha a peca inteira, com a logo como referencia."""
    import modo_completo
    from PIL import Image

    chave = cfg.get("OPENAI_API_KEY")
    if not chave:
        erro("O modo completo precisa da OPENAI_API_KEY no CHAVES.txt.")

    apelido = re.sub(r"[^a-z0-9]+", "-",
                     tema.lower().replace("ç", "c"))[:40].strip("-")
    saidas = {}
    pedidos = []
    if not args.so_story:
        pedidos.append(("feed", (1080, 1350)))      # 4:5
    if not args.so_feed:
        pedidos.append(("story", (1080, 1920)))

    for formato, (Lf, Af) in pedidos:
        log(f"Desenhando a peca de {formato} com IA. Pode levar 1 a 3 minutos...")
        bruto = os.path.join(PASTA_SAIDA, f"bruto-{formato}-{carimbo}.png")
        if not modo_completo.gerar(chave, c["titulo"], c["apoio"], c["foto"],
                                   formato, bruto, log,
                                   estilo=c.get("estilo", ""),
                                   preferido=cfg.get("MODELO_IMAGEM")):
            erro(f"Nao consegui gerar a peca de {formato}.")

        im = Image.open(bruto).convert("RGB")
        im = molde._encaixar(im, Lf, Af)
        nome = f"fisiosync_{apelido}_{'feed' if formato == 'feed' else 'stories'}"
        final_jpg = os.path.join(PASTA_SAIDA, f"{nome}_{Lf}x{Af}.jpg")
        im.save(final_jpg, "JPEG", quality=94, optimize=True)
        saidas[formato] = final_jpg
        log(f"Peca de {formato}: {os.path.basename(final_jpg)} -> {Lf}x{Af}")

    print("\nATENCAO: no modo completo a IA escreve o texto dentro da imagem.")
    print("Confira as letras, a logo e os selos antes de publicar.\n")

    if args.previa:
        gravar_historico(registro_completo(
            c, tema, list(saidas.values()), "rascunho", "completo"))
        print("PREVIA PRONTA. Nada foi publicado. Gravada como rascunho.")
        print(f"Veja os arquivos em: {PASTA_SAIDA}")
        return

    if "feed" in saidas:
        publicar_feed(cfg, saidas["feed"], c["legenda"], carimbo)
    if "story" in saidas:
        link = subir_para_github(cfg, saidas["story"], f"story-{carimbo}.jpg")
        publicar(cfg, link, story=True)

    gravar_historico(registro_completo(
        c, tema, list(saidas.values()), "publicado", "completo"))
    print("\n  TUDO PUBLICADO COM SUCESSO")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previa", action="store_true")
    ap.add_argument("--so-feed", action="store_true")
    ap.add_argument("--so-story", action="store_true")
    ap.add_argument("--tema", default=None)
    ap.add_argument("--completo", action="store_true",
                    help="a IA desenha a peca inteira, igual ao ChatGPT")
    ap.add_argument("--layout", default=None,
                    help="forca um layout, ex: tipografico")
    ap.add_argument("--brief", default=None,
                    help="arquivo .json com o briefing pronto da peca")
    ap.add_argument("--molde", action="store_true",
                    help="forca o modo molde (texto perfeito)")
    args = ap.parse_args()

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    cfg = carregar_config()
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    print("=" * 56)
    print(f"  ROBO FISIOSYNC - {datetime.date.today().isoformat()}")
    print("=" * 56)

    # Trava de janela. A nuvem tenta varias vezes dentro de cada
    # janela porque o cron do GitHub atrasa; quem garante um unico post
    # por janela e esta checagem, nao o horario do agendador.
    if os.environ.get("FORCAR") == "1":
        log("Disparo manual: a trava de janela nao se aplica.")
    elif not (args.previa or args.tema or args.brief):
        data_br, janela = janela_agora()
        hora = agora_brasilia().strftime("%H:%M")
        if janela is None:
            log(f"Fora das janelas de publicacao ({hora} em Brasilia). "
                "Saindo sem fazer nada.")
            return
        if ja_publicou_nesta_janela():
            log(f"A janela da {janela} de {data_br} ja foi publicada. "
                "Saindo sem gerar imagem nem gastar pauta.")
            return
        log(f"Janela da {janela} de {data_br}, {hora} em Brasilia. "
            "Ainda nao publicada: seguindo.")

    atualizar_logo(cfg)

    if args.brief:
        with open(args.brief, encoding="utf-8") as f:
            c = json.load(f)
        log(f"Briefing carregado de {os.path.basename(args.brief)}")
        log(f"Tema: {c.get('tema')}")
        log(f"Conceito: {c.get('conceito')}")
    else:
        # Sem --tema, a IA escolhe sozinha, olhando o historico
        c = gerar_conteudo(cfg, args.tema)
    tema = c["tema"]
    if args.layout:
        c["layout"] = args.layout
        log(f"Layout forcado: {args.layout}")
    c["legenda"] = revisar_legenda(cfg, c["legenda"])

    print("\n--- TITULO ---")
    print(c["titulo"])
    print("--- APOIO ---")
    print(c["apoio"])
    print("--- LEGENDA ---")
    print(c["legenda"])
    print("--------------\n")

    modo_completo_ligado = args.completo or (
        not args.molde and cfg.get("MODO", "").lower() == "completo")

    if modo_completo_ligado:
        return _fluxo_completo(cfg, args, tema, c, carimbo)

    # Garante os selos oficiais das lojas, baixando se ainda nao existirem
    if not (os.path.exists(molde.SELO_GOOGLE)
            and os.path.exists(molde.SELO_APPLE)):
        log("Selos das lojas ainda nao estao aqui. Baixando os oficiais...")
        try:
            import baixar_selos
            baixar_selos.main()
        except Exception as e:
            log(f"Nao consegui baixar os selos automaticamente: {e}")

    foto = os.path.join(PASTA_SAIDA, f"foto-{carimbo}.jpg")
    if c.get("layout") == "tipografico":
        log("Layout tipografico: a tipografia e o visual, sem gerar imagem.")
        foto = ""
    else:
        log("Gerando a imagem com IA. Leva de 30 a 90 segundos, aguarde...")
        log(f"  cena pedida: {c['foto'][:110]}")
        gerar_foto(cfg, c, foto, c["layout"])

    quer_feed = not args.so_story
    quer_story = not args.so_feed

    apelido = re.sub(r"[^a-z0-9]+", "-",
                     tema.lower().replace("ç", "c"))[:40].strip("-")
    base_feed = os.path.join(PASTA_SAIDA, f"fisiosync_{apelido}_feed")
    base_story = os.path.join(PASTA_SAIDA, f"fisiosync_{apelido}_stories")

    arq_feed = arq_story = None
    try:
        if quer_feed:
            arq_feed = molde.montar(foto, c["titulo"], c["apoio"], base_feed,
                                    "feed", layout=c["layout"],
                                    sobretitulo=c.get("sobretitulo", ""))
            ok, medida = molde.validar(arq_feed, "feed")
            log(f"Peca do feed: {os.path.basename(arq_feed)} -> {medida} "
                f"{'OK' if ok else 'PROPORCAO ERRADA'}")
        if quer_story:
            arq_story = molde.montar(foto, c["titulo"], c["apoio"], base_story,
                                     "story", layout=c["layout"],
                                     sobretitulo=c.get("sobretitulo", ""))
            ok, medida = molde.validar(arq_story, "story")
            log(f"Peca do story: {os.path.basename(arq_story)} -> {medida} "
                f"{'OK' if ok else 'PROPORCAO ERRADA'}")
    except layouts.TextoNaoCabe as falha:
        # Preferir NAO publicar a publicar frase cortada. Nao ha
        # fallback aqui de proposito: fallback silencioso foi o que
        # colocou "e deixar claras as condicoes do" no ar.
        erro("O texto nao coube na arte e cortar nao e opcao.\n"
             f"  {falha}\n"
             "  A peca NAO foi publicada. Rode de novo: a IA escreve "
             "outro texto, mais curto.")

    if molde.avisos:
        print("\n" + "!" * 56)
        for a in molde.avisos:
            print("  " + a)
        print("!" * 56 + "\n")

    with open(os.path.join(PASTA_SAIDA, f"legenda-{carimbo}.txt"),
              "w", encoding="utf-8") as f:
        f.write(f"TEMA: {tema}\n\nTITULO: {c['titulo']}\n"
                f"APOIO: {c['apoio']}\n\n{c['legenda']}\n")

    if args.previa:
        gravar_historico(registro_completo(
            c, tema, [arq_feed, arq_story], "rascunho", "molde"))
        print("\nPREVIA PRONTA. Nada foi publicado.")
        print("Registrada no historico.json como rascunho.")
        print("Se voce aprovar, rode:")
        print(f"  python aprovar.py gerado\\<arquivo>.png \"o que funcionou\"")
        print(f"\nVeja os arquivos na pasta: {PASTA_SAIDA}")
        return

    if molde.avisos:
        erro("Nao publiquei porque a peca esta incompleta. Resolva os avisos "
             "acima e rode de novo. Para ver a peca sem publicar, use --previa.")

    if quer_feed:
        publicar_feed(cfg, arq_feed, c["legenda"], carimbo)
    if quer_story:
        link = subir_para_github(cfg, arq_story, f"story-{carimbo}.jpg")
        publicar(cfg, link, story=True)

    gravar_historico(registro_completo(
        c, tema, [arq_feed, arq_story], "publicado", "molde"))

    print("\n" + "=" * 56)
    print("  TUDO PUBLICADO COM SUCESSO")
    print("=" * 56)


if __name__ == "__main__":
    main()
