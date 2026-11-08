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
    "manha": (8, 13),    # alvo 09:00 em Brasilia (desde 03/11/2026)
    "tarde": (14, 18),   # alvo 15:00 em Brasilia
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


def feed_recente_no_instagram(cfg, horas=3):
    """
    Trava pela fonte da verdade: ha post de feed (imagem ou carrossel)
    no perfil nas ultimas 'horas'? Os posts sao as 12h e as 18h, entao
    3 horas separa as duas janelas sem confundir uma com a outra.

    Criada em 02/11/2026, depois de um Reels sair duplicado porque uma
    largada de reserva leu um historico velho. O historico em arquivo
    pode estar desatualizado; o perfil nao.
    Devolve o link do post encontrado, ou None. Se nao der para
    conferir, devolve "?" e quem chama nao publica.
    """
    try:
        r = requests.get(
            f"https://graph.facebook.com/{VERSAO_GRAPH}/{cfg['ID']}/media",
            params={"fields": "timestamp,media_product_type,permalink",
                    "limit": 10, "access_token": cfg["TOKEN"]}, timeout=60)
        dados = r.json()
        if "error" in dados:
            log(f"  nao consegui conferir o perfil: {dados['error'].get('message')}")
            return "?"
    except Exception as e:
        log(f"  nao consegui conferir o perfil: {e}")
        return "?"
    limite = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=horas)
    for m in dados.get("data", []):
        if m.get("media_product_type") == "REELS":
            continue
        quando = datetime.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        if quando >= limite:
            return m.get("permalink") or m["timestamp"]
    return None


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


def _pedido_conteudo(tema_sugerido=None, fato="", fonte="", carrossel=False,
                     estilo="sabia", cuidados=""):
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
            + (f"- CUIDADOS DE QUEM CONFERIU O FATO (obedeca): {cuidados}\n"
               if cuidados else "") +
            "- Estudo observacional mostra ASSOCIACAO: escreva 'se associou', "
            "nunca 'causa', 'aumenta a vida' ou 'previne'. Nao transforme o "
            "achado em promessa de tratamento.\n"
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
        "objetivo; em carrossel, a chamada e SEMPRE pedir para salvar o post "
        "e enviar para um colega de profissao. Depois a assinatura em uma linha, copiada com "
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
        + (
        '  "slides": CARROSSEL. Lista de 3 ou 4 objetos {"titulo", "texto"} '
        "que explicam o fato passo a passo, um passo por slide, na ordem "
        "em que a pessoa entende. titulo: ate 5 palavras. texto: ate 32 "
        "palavras, frases completas. Cada slide so pode afirmar o que esta "
        "no fato conferido: nada de dado, exemplo clinico, beneficio ou "
        "numero que nao esteja nele. Pode explicar com palavras simples o "
        "que o fato diz e por que isso importa no dia a dia do "
        "fisioterapeuta, sem inventar regra.\n"
        '  "fechamento": frase do ultimo slide, ate 16 palavras, pedindo para '
        "salvar ou mandar para um colega especifico (ex: 'que da aula de "
        "Pilates'). Sem falar da FisioSync.\n"
        "  No carrossel, o titulo e o apoio sao a CAPA: o titulo e o gancho "
        "que faz arrastar.\n" if carrossel else "") +
        (
        "\n=== FORMATO MITO OU VERDADE (vale para este post) ===\n"
        "- sobretitulo: exatamente 'Mito ou verdade?'.\n"
        "- titulo (capa): UMA afirmacao curta, ate 8 palavras, sem ponto "
        "final, que o publico realmente poderia achar verdadeira ou falsa. "
        "Ate 60 caracteres. Ela tem que ser decidida PELO FATO CONFERIDO: ou o fato confirma a "
        "afirmacao (VERDADE) ou o fato a contradiz diretamente (MITO). Nada "
        "que o fato nao resolva.\n"
        "- apoio (capa): 'Arraste e confira a resposta.'\n"
        "- primeiro slide: titulo exatamente 'Verdade.' ou 'Mito.', e o texto "
        "explica por que, com o que o fato diz. Os outros slides "
        "aprofundam, sempre dentro do fato.\n"
        "- fechamento: uma pergunta curta para os comentarios, ligada ao "
        "assunto (ex: 'Voce ja sabia? Conta nos comentarios.').\n"
        "- legenda: comeca repetindo a afirmacao como pergunta, pede para "
        "a pessoa responder nos comentarios antes de arrastar, e depois "
        "segue a regra normal da legenda.\n"
        "=== FIM ===\n" if (carrossel and estilo == "mito") else "") +
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


def numeros_soltos(textos, fato="", fonte=""):
    """
    Numeros escritos na peca que NAO estao no fato conferido.

    Esta e a ultima linha de defesa contra o risco que vem junto com
    conteudo de curiosidade: a IA escreve "desde 1969" ou "em 68% dos
    casos" com total confianca e aquilo vai ao ar no perfil de um
    produto de saude. Numero sem lastro nao sai.

    Numero da FONTE citada tem lastro (07/11/2026): o carrossel sobre a
    Resolucao COFFITO 424/2013 caiu porque "424" e "2013" estavam so na
    fonte, nao no texto do fato, e foi ao ar so a capa pedindo para
    arrastar.
    """
    permitidos = (set(re.findall(r"\d+", f"{fato or ''} {fonte or ''}"))
                  | NUMEROS_DA_CASA)
    achados = set()
    for t in textos:
        achados |= set(re.findall(r"\d+", t or ""))
    return sorted(achados - permitidos)


def conferir_numeros(cfg, dados, fato, fonte=""):
    """
    Confere os numeros da peca; se houver invencao, pede UMA reescrita.
    Se insistir, devolve a lista do que sobrou para o chamador abortar.
    """
    campos = ("titulo", "apoio", "legenda")
    soltos = numeros_soltos([dados.get(c, "") for c in campos], fato, fonte)
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
        + (f"Fonte do fato (os numeros dela podem ser citados): {fonte}\n"
           if fato and fonte else "")
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

    return numeros_soltos([dados.get(c, "") for c in campos], fato, fonte)


# Ultimo slide do carrossel. Todas pedem salvar e enviar; a parte em
# destaque (ciano) comeca em "Salve".
FECHOS_SABIA = [
    "Salve este post e envie para um colega de profissão.",
    "Vale guardar. Salve e mande para quem atende com você.",
    "Útil? Salve e envie para um colega que precisa ver isso.",
    "Pra não esquecer: Salve e compartilhe com sua equipe.",
    "Conhece um estudante de fisio? Salve e mande para ele.",
]
FECHOS_MITO = [
    "Acertou? Conta nos comentários. Salve e envie para um colega de profissão.",
    "Você sabia a resposta? Comenta aí. Salve e desafie um colega.",
    "Mito ou verdade, qual foi o seu palpite? Salve e mande para a sua equipe.",
]


def _slides_validos(dados, fato, fonte=""):
    """
    Confere os slides do carrossel. Devolve [] em qualquer problema, e
    quem chama troca o post pelo "so fato": a capa de carrossel pede para
    arrastar e nao pode ir ao ar sozinha (07/11/2026).
    """
    slides = dados.get("slides")
    if not isinstance(slides, list) or not 2 <= len(slides) <= 5:
        log("AVISO: a IA nao mandou slides validos.")
        return []
    limpos = []
    for s in slides:
        if not isinstance(s, dict) or not s.get("titulo") or not s.get("texto"):
            log("AVISO: slide sem titulo ou texto.")
            return []
        limpos.append({"titulo": str(s["titulo"]).strip(),
                       "texto": str(s["texto"]).strip()})
    textos = [x for s in limpos for x in (s["titulo"], s["texto"])]
    textos.append(dados.get("fechamento", ""))
    soltos = numeros_soltos(textos, fato, fonte)
    if soltos:
        log(f"AVISO: slide com numero sem fonte ({', '.join(soltos)}).")
        return []
    # Pedido do Darlan (02/11/2026): TODO carrossel termina pedindo para
    # salvar e enviar para um colega de profissao. Frase fixa, nao fica a
    # criterio da IA. No "mito ou verdade" vem antes o convite a comentar.
    # Varia a frase (03/11/2026: "nem sempre falar a mesma coisa pra nao
    # enjoar"), mas toda versao pede salvar e enviar. O revezamento e pelo
    # dia do ano, entao dois dias seguidos nunca repetem.
    dia = datetime.date.today().timetuple().tm_yday
    if dados.get("_estilo") == "mito":
        opcoes = FECHOS_MITO
    else:
        opcoes = FECHOS_SABIA
    dados["fechamento"] = opcoes[dia % len(opcoes)]
    log(f"Carrossel: capa + {len(limpos)} slides + fechamento")
    return limpos


def _conteudo_so_fato(base, pauta_banco, eixo_banco, familia_banco,
                      fato_banco, fonte_banco):
    """
    Post montado SO com o texto literal do fato conferido e a fonte, sem
    nenhuma frase escrita pela IA. E a saida quando a IA falha ou quando
    a revisao de veracidade nao aprova o texto: melhor um post simples e
    correto do que um bonito com algo que a fonte nao diz.
    """
    titulo = base[:1].upper() + base[1:]
    ref = "a OMS" if "OMS" in fonte_banco else (
          "a lei" if fonte_banco.lower().startswith(("lei", "decreto"))
          else "a fonte")
    return {
        "tema": base,
        "pauta": pauta_banco or base,
        "eixo": eixo_banco,
        "familia": familia_banco,
        "fonte": fonte_banco,
        "objetivo": "salvar",
        "estilo": ESTILOS_ARTE[0],
        "layout": "tipografico",
        "conceito": "",
        "sobretitulo": "Você sabia?",
        "titulo": encurtar(titulo, 62, "titulo"),
        "apoio": f"Veja o que diz {ref}.",
        "slides": [],
        "foto": "",
        "verificacao": "so_fato",
        "legenda": (f"Você sabia? {titulo}.\n\n"
                    + (f"{fato_banco}\n\nFonte: {fonte_banco}\n\n"
                       if fato_banco else "")
                    + "Salve para consultar depois e mande para um "
                    "colega.\n\n"
                    "Conteúdo FisioSync. Teste grátis por 7 dias: "
                    "app.fisiosync.com.br\n\n"
                    "#FisioSync #FisioSyncExplica #fisioterapia "
                    "#fisioterapeuta #conhecimento"),
    }


def _sem_carrossel(c, motivo):
    """
    Carrossel que perdeu os slides (slide invalido, sem ilustracao, slide
    que nao coube). A capa dele pede para arrastar e, no "Mito ou
    verdade?", traz so a pergunta: sozinha ela nao se sustenta. Em
    07/11/2026 foi ao ar "Arraste e confira a resposta" sem resposta
    nenhuma, no feed e no story. Volta o post so com o fato e a fonte.
    """
    log(f"AVISO: {motivo}. A capa do carrossel nao sai sozinha: o post "
        "sai so com o fato conferido e a fonte.")
    return _conteudo_so_fato(c.get("pauta") or c.get("tema", ""),
                             c.get("pauta", ""), c.get("eixo", ""),
                             c.get("familia", "gestao"), c.get("_fato", ""),
                             c.get("fonte", ""))


def _texto_publicado(dados):
    """Tudo o que vai aparecer na arte, nos slides e na legenda."""
    partes = [f"SOBRETITULO: {dados.get('sobretitulo', '')}",
              f"TITULO DA CAPA: {dados.get('titulo', '')}",
              f"APOIO DA CAPA: {dados.get('apoio', '')}"]
    for n, sl in enumerate(dados.get("slides") or [], 2):
        partes.append(f"SLIDE {n}: {sl.get('titulo', '')} | {sl.get('texto', '')}")
    partes.append(f"LEGENDA: {dados.get('legenda', '')}")
    return "\n".join(partes)


def conferir_veracidade(cfg, dados, fato, fonte, cuidados="", estilo="sabia"):
    """
    REVISAO DE VERACIDADE (05/11/2026, pedido do Darlan: "garantir que
    todas as postagens sejam informacao valida e veridica").

    Um revisor, numa chamada separada da que escreveu o texto, compara
    cada afirmacao do post com o FATO CONFERIDO. Devolve (ok, problemas).
    Sem resposta valida do revisor, conta como NAO aprovado: na duvida,
    nao publica paráfrase.
    """
    if not fato:
        return False, ["post sem fato conferido"]
    regra_mito = (
        "FORMATO MITO OU VERDADE: o titulo da capa e uma afirmacao para o "
        "leitor julgar e pode ser falsa DE PROPOSITO. Nao conte a capa como "
        "erro; confira, isso sim, se o veredito do slide 2 ('Verdade.' ou "
        "'Mito.') esta CERTO segundo o fato. Veredito errado e problema "
        "grave.\n" if estilo == "mito" else "")
    pedido = (
        "Voce e um revisor cientifico rigoroso de um perfil de "
        "fisioterapia. Sua unica referencia de verdade e o FATO CONFERIDO "
        "abaixo (com a fonte e os cuidados de quem o conferiu).\n\n"
        f"FATO CONFERIDO: {fato}\nFONTE: {fonte}\n"
        + (f"CUIDADOS: {cuidados}\n" if cuidados else "")
        + "\nTEXTO DO POST:\n" + _texto_publicado(dados) + "\n\n"
        "Aponte TODA afirmacao do post que o fato NAO sustenta, por exemplo: "
        "informacao nova que nao esta no fato; numero diferente; "
        "generalizacao alem do que o fato diz (populacao, prazo, tipo de "
        "lesao); 'causa', 'previne' ou 'aumenta a vida' quando o fato e "
        "associacao; troca de obrigacao por possibilidade ('devera' virando "
        "'pode') ou o contrario; fonte citada de forma errada.\n"
        + regra_mito +
        "NAO conte como problema: perguntas ao leitor, pedidos para salvar, "
        "enviar ou comentar, a assinatura da FisioSync, hashtags, e frases "
        "de contexto obvias que nao afirmam nada tecnico.\n"
        'Responda SOMENTE um JSON: {"ok": true ou false, "problemas": '
        '["trecho exato -> por que o fato nao sustenta"]}')
    bruto = None
    if cfg.get("OPENAI_API_KEY"):
        bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    if not bruto and cfg.get("GEMINI_API_KEY"):
        bruto = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)
    r = _extrair_json(bruto) if bruto else None
    if not isinstance(r, dict) or "ok" not in r:
        return False, ["o revisor nao respondeu: sem revisao, sem paráfrase"]
    problemas = [str(p) for p in (r.get("problemas") or [])]
    return bool(r.get("ok")) and not problemas, problemas


def _corrigir_pelo_revisor(cfg, dados, fato, problemas, estilo):
    """Pede UMA correcao pontual dos trechos apontados pelo revisor."""
    campos = {k: dados.get(k) for k in ("sobretitulo", "titulo", "apoio",
                                       "slides", "legenda")}
    pedido = (
        "Corrija o JSON abaixo para que TODA afirmacao fique apoiada no "
        f"fato conferido. Fato: {fato}\n"
        "Problemas apontados pelo revisor (corrija todos, reescrevendo ou "
        "removendo o trecho):\n- " + "\n- ".join(problemas) + "\n"
        "Mantenha as mesmas chaves, o mesmo numero de slides, o tom e o "
        "tamanho. Nao acrescente informacao nova. Responda SOMENTE o JSON."
        + ("\nNo formato Mito ou verdade, o veredito do primeiro slide tem "
           "que ser o correto segundo o fato." if estilo == "mito" else "")
        + "\n\n" + json.dumps(campos, ensure_ascii=False))
    bruto = None
    if cfg.get("OPENAI_API_KEY"):
        bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    if not bruto and cfg.get("GEMINI_API_KEY"):
        bruto = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)
    novo = _extrair_json(bruto) if bruto else None
    if not isinstance(novo, dict) or not novo.get("titulo"):
        return None
    saida = dict(dados)
    for k in ("sobretitulo", "titulo", "apoio", "legenda"):
        if novo.get(k):
            saida[k] = novo[k]
    if dados.get("slides") and isinstance(novo.get("slides"), list):
        saida["slides"] = novo["slides"]
    return saida


def legenda_com_fonte(legenda, fonte, url=""):
    """
    Linha padrao de fonte no fim da legenda (05/11/2026: "para a pessoa
    saber que e confiavel, nao que a gente tirou da cabeca"). Tira as
    linhas 'Fonte:' que a IA escreveu e poe a referencia completa, com o
    link, antes da assinatura da FisioSync.
    """
    if not fonte:
        return legenda
    linhas = [l for l in legenda.split("\n")
              if not l.strip().lower().startswith(("fonte:", "📚 fonte", "🔗"))]
    texto = "\n".join(linhas)
    while "\n\n\n" in texto:
        texto = texto.replace("\n\n\n", "\n\n")
    bloco = f"📚 Fonte: {fonte}" + (f"\n🔗 {url}" if url else "")
    for marca in ("Conteúdo FisioSync", "Conteudo FisioSync"):
        i = texto.find(marca)
        if i >= 0:
            return texto[:i].rstrip() + "\n\n" + bloco + "\n\n" + texto[i:]
    partes = texto.rstrip().split("\n\n")
    if partes and partes[-1].lstrip().startswith("#"):
        return "\n\n".join(partes[:-1] + [bloco, partes[-1]])
    return texto.rstrip() + "\n\n" + bloco


def gerar_conteudo(cfg, tema=None, carrossel=False, estilo="sabia"):
    hist = ler_historico(limite=500)
    pauta_banco, eixo_banco, familia_banco = "", "", "gestao"
    fato_banco, fonte_banco = "", ""
    cuidados_banco = ""
    url_banco = ""

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
        cuidados_banco = p.get("observacao", "")
        url_banco = p.get("url", "")
    log(f"Escrevendo o conteudo sobre: {tema}")
    pedido = _pedido_conteudo(tema, fato_banco, fonte_banco, carrossel,
                              estilo, cuidados_banco)
    log(f"Formato: {'carrossel' if carrossel else 'imagem unica'}"
        + (' / mito ou verdade' if carrossel and estilo == 'mito' else ''))

    bruto = None
    if cfg.get("OPENAI_API_KEY"):
        bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
    if not bruto and cfg.get("GEMINI_API_KEY"):
        bruto = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)

    dados = _extrair_json(bruto) if bruto else None
    if not dados or not dados.get("titulo"):
        # Sem IA (ex.: 02/11/2026, creditos da OpenAI zerados) o post
        # sai mesmo assim, montado SO com o fato conferido e a fonte, em
        # layout tipografico (nao precisa gerar imagem). Nada escrito de
        # cabeca, entao nao ha o que conferir.
        log("AVISO: a IA nao devolveu o conteudo esperado. Montando o post "
            "so com o fato conferido, sem ilustracao.")
        return _conteudo_so_fato(tema or escolher_tema(), pauta_banco,
                                 eixo_banco, familia_banco, fato_banco,
                                 fonte_banco)

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
    sobraram = conferir_numeros(cfg, dados, fato_banco, fonte_banco)
    if sobraram:
        erro("A peca cita numero que nao tem fonte, e a reescrita nao "
             f"resolveu: {', '.join(sobraram)}.\n"
             "  Nao vou publicar dado inventado em perfil de produto de "
             "saude.\n  Rode de novo: a IA escreve outro texto.")

    if carrossel:
        dados["_estilo"] = estilo
        dados["slides"] = _slides_validos(dados, fato_banco, fonte_banco)
        if not dados["slides"]:
            # 07/11/2026: sem slides, a capa foi ao ar sozinha ("Arraste e
            # confira a resposta", sem resposta nenhuma). Capa de
            # carrossel nao se sustenta sozinha.
            return _sem_carrossel({**dados, "pauta": pauta_banco or tema,
                                   "eixo": eixo_banco,
                                   "familia": familia_banco,
                                   "fonte": fonte_banco, "_fato": fato_banco},
                                  "carrossel sem slides validos")
    else:
        dados["slides"] = []

    # Titulo NAO e encurtado por palavra: em 02/11/2026 "competencia da
    # Fisioterapia Respiratoria" virou "competencia da Fisioterapia." e o
    # fato mudou de sentido. A arte diminui a letra ate 3 linhas e, se nem
    # assim couber, o molde recusa a peca (TextoNaoCabe). So corta em
    # pontuacao, e so se passar muito do tamanho.
    dados["titulo"] = dados["titulo"].strip()
    if len(dados["titulo"]) > 95:
        dados["titulo"] = encurtar(dados["titulo"], 95, "titulo")
    dados["apoio"] = encurtar(dados.get("apoio", ""), 118, "apoio")
    dados["pauta"] = pauta_banco or dados.get("tema", "")
    dados["eixo"] = eixo_banco
    dados["familia"] = familia_banco
    dados["fonte"] = fonte_banco
    # REVISAO DE VERACIDADE: nada vai ao ar sem bater com o fato conferido
    ok, problemas = conferir_veracidade(cfg, dados, fato_banco, fonte_banco,
                                        cuidados_banco, estilo if carrossel
                                        else "sabia")
    if ok:
        log("Revisao de veracidade: APROVADO (tudo apoiado no fato).")
        dados["verificacao"] = "aprovado"
    else:
        log("Revisao de veracidade: problemas encontrados:")
        for p in problemas:
            log(f"  - {p}")
        corrigido = _corrigir_pelo_revisor(cfg, dados, fato_banco, problemas,
                                           estilo)
        ok2 = False
        if corrigido:
            if carrossel:
                corrigido["slides"] = _slides_validos(corrigido, fato_banco,
                                                      fonte_banco)
            soltos = numeros_soltos([corrigido.get(c, "") for c in
                                     ("titulo", "apoio", "legenda")],
                                    fato_banco, fonte_banco)
            if carrossel and not corrigido["slides"]:
                # sem slides a capa iria sozinha: cai no "so fato" abaixo
                log("AVISO: a correcao derrubou os slides do carrossel.")
            elif not soltos:
                ok2, problemas2 = conferir_veracidade(
                    cfg, corrigido, fato_banco, fonte_banco, cuidados_banco,
                    estilo if carrossel else "sabia")
                if not ok2:
                    for p in problemas2:
                        log(f"  - ainda: {p}")
        if ok2:
            log("Revisao de veracidade: APROVADO depois da correcao.")
            corrigido["verificacao"] = "corrigido"
            dados = corrigido
            dados["titulo"] = dados["titulo"].strip()
            dados["apoio"] = encurtar(dados.get("apoio", ""), 118, "apoio")
        else:
            log("Revisao de veracidade: NAO aprovado. O post sai so com o "
                "texto literal do fato e a fonte.")
            return _conteudo_so_fato(pauta_banco or tema, pauta_banco,
                                     eixo_banco, familia_banco, fato_banco,
                                     fonte_banco)

    dados["legenda"] = legenda_com_fonte(dados.get("legenda", ""), fonte_banco,
                                         url_banco)
    # o fato viaja junto: se o carrossel cair depois (ilustracao, slide
    # que nao coube), o main remonta o post "so fato" com ele
    dados["_fato"] = fato_banco
    log(f"Tema escolhido: {dados['tema']}")
    if eixo_banco:
        log(f"Eixo: {eixo_banco}  (pauta do banco: {pauta_banco})")
    log(f"Objetivo: {dados['objetivo']} | Estilo: {dados['estilo']}")
    log(f"Titulo: {dados['titulo']}")
    return dados


# ======================================================= CARROSSEL NOVO
# Formato aprovado pelo Darlan em 08/11/2026: "aula" as 9h e "mito ou
# verdade" as 15h, no visual de serie (aula.py). A pauta traz VARIOS fatos
# conferidos (campo "fatos"); a IA so organiza os fatos em slides e diz
# quais fatos cada slide usa. A fonte de cada slide sai desses fatos.

_EXTENSO = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
            "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
            "nove": 9, "dez": 10, "onze": 11, "doze": 12, "quinze": 15,
            "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
            "sessenta": 60, "cem": 100, "one": 1, "two": 2, "three": 3,
            "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
            "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
            "thirty": 30, "sixty": 60, "hundred": 100, "twice": 2, "dobro": 2}

_HASHTAG_EIXO = {"avaliacao": "#avaliacaofuncional",
                 "evidencia": "#fisioterapiabaseadaemevidencias",
                 "exercicio-saude": "#exerciciofisico", "pilates": "#pilates",
                 "regulacao": "#coffito", "etica": "#eticaprofissional"}


def _lastro_aula(fatos):
    """Texto com tudo que da lastro a um numero: fato, trecho original e
    fonte, mais os numeros que o original escreve por extenso."""
    texto = " ".join(" ".join((f.get("texto", ""), f.get("trecho_original", ""),
                               f.get("fonte", ""))) for f in fatos)
    extra = [str(n) for w, n in _EXTENSO.items()
             if re.search(rf"\b{w}\b", texto, re.I)]
    return texto + " " + " ".join(extra)


def _numeros_aula(spec, pauta):
    """Todo numero de um slide tem que estar nos fatos que ESSE slide cita."""
    import aula
    fatos = pauta.get("fatos") or []
    problemas = []
    for k, s in enumerate(spec.get("slides") or [], 2):
        if not isinstance(s, dict):
            continue
        usados = [fatos[i - 1] for i in (s.get("fatos") or [])
                  if isinstance(i, int) and 1 <= i <= len(fatos)]
        soltos = numeros_soltos(aula.textos_do_slide(s), _lastro_aula(usados))
        if soltos:
            problemas.append(f"slide {k}: o numero {', '.join(soltos)} nao esta "
                             "nos fatos que esse slide cita")
    capa = spec.get("capa") or {}
    textos = [capa.get("titulo", ""), *(capa.get("promessa") or []),
              spec.get("chamada_final", ""), spec.get("pergunta_final", ""),
              spec.get("legenda", "")]
    geral = _lastro_aula(fatos) + " " + " ".join(pauta.get("referencias") or [])
    soltos = numeros_soltos([aula._limpo(t) for t in textos if t], geral)
    if soltos:
        problemas.append("capa, fechamento ou legenda com numero sem fonte: "
                         + ", ".join(soltos))
    return problemas


def _pedido_aula(pauta, estilo, aviso=""):
    fatos = "\n".join(f"{i}. {f['texto']} (fonte: {f['fonte']})"
                      for i, f in enumerate(pauta["fatos"], 1))
    mito = estilo == "mito"
    lo, hi = (4, 6) if mito else (5, 7)
    return (
        "Voce e editor de conteudo de um perfil de fisioterapia no Instagram. "
        "O publico e fisioterapeuta e instrutor de Pilates. Monte um CARROSSEL "
        + ("'MITO OU VERDADE?'" if mito else "'AULA'")
        + " usando SOMENTE os fatos conferidos abaixo.\n\n"
        f"TEMA: {pauta['tema']}\n"
        + (f"AFIRMACAO DA CAPA (ja escrita, nao mude): {pauta['afirmacao']}\n"
           f"VEREDITO (decidido pelas fontes, nao mude): {pauta['veredito']}\n"
           if mito else "")
        + f"FATOS CONFERIDOS (cite pelo numero):\n{fatos}\n"
        + (f"CUIDADOS DE QUEM CONFERIU: {pauta['observacao']}\n"
           if pauta.get("observacao") else "")
        + "\nREGRAS\n"
        "- Cada slide usa 1 ou 2 fatos e diz quais em \"fatos\": [numeros]. "
        "Nada que o fato nao diga: nenhum numero, dado, exemplo clinico, "
        "beneficio, prazo ou regra fora dos fatos. Associacao continua "
        "associacao; 'pode' nao vira 'deve' nem o contrario.\n"
        "- Titulo de cada slide: UMA pergunta curta ou frase de comando, ate "
        "40 caracteres, na ordem em que a pessoa entende (o que e, por que "
        "importa, como fazer, como interpretar, cuidados). Marque com ==...== "
        "a parte final que fica em ciano. Ex.: 'O que o teste ==mede?=='.\n"
        "- Texto curto, de fisioterapeuta para fisioterapeuta, frases "
        "completas, portugues do Brasil com acentos. **negrito** so no "
        "essencial. Sem emoji nos slides.\n"
        "- Varie os tipos. 'numero' quando o fato tiver um numero forte; "
        "'duas' para comparar dois valores; 'passos' para protocolo; 'fluxo' "
        "para criterio em etapas; 'cards' ou 'lista' para itens; 'destaque' "
        "para definicao.\n"
        "- 'puxa' (opcional, ate 30 caracteres): provocacao para o proximo "
        "slide, sem afirmar nada. Ex.: 'E como interpretar'.\n"
        "- Proibido: sensacionalismo, promessa de resultado, preco, desconto, "
        "Black Friday, falar da FisioSync nos slides.\n\n"
        "TIPOS DE SLIDE E CAMPOS\n"
        "- destaque: titulo, destaque (frase principal, ate 90), texto "
        "(opcional, ate 190), card (opcional: {titulo, texto})\n"
        "- numero: titulo, numero (ate 12, ex.: '+16%', '≤ 0,8 m/s', '150 "
        "min'), texto (o que o numero significa, ate 190), card (opcional), "
        "nota (opcional, ressalva, ate 150)\n"
        "- cards: titulo, itens (2 ou 3 de {titulo ate 40, texto ate 170, "
        "destaque: true opcional}), nota (opcional)\n"
        "- lista: titulo, texto (opcional), itens (2 a 5 frases de ate 110), "
        "nota (opcional)\n"
        "- passos: titulo, itens (2 a 4 passos de ate 110), nota (opcional)\n"
        "- duas: titulo, itens (exatamente 2 de {rotulo ate 12, valor ate 8, "
        "unidade ate 5}), nota (opcional)\n"
        "- fluxo: titulo, itens (2 ou 3 de {texto ate 110, selo ate 12}), "
        "nota (opcional)\n"
        + ("- veredito (SO no primeiro slide): veredito (exatamente "
           f"'{pauta['veredito']}'), texto (por que, com o fato que decide, "
           "ate 190), card (opcional)\n" if mito else "")
        + "Todo slide tem tambem: tipo, fatos e, se quiser, puxa.\n\n"
        "RESPONDA SOMENTE UM JSON:\n"
        "{\n"
        ' "secao": "rotulo curto do cabecalho, ex.: Avaliação funcional",\n'
        ' "capa": {'
        + ('"ilustracao": "..."}' if mito else
           '"titulo": "o tema em ate 32 caracteres, com ==destaque==", '
           '"promessa": ["2 ou 3 linhas curtas do que o carrossel entrega, '
           'ex.: Como medir.", "..."], "ilustracao": "..."}')
        + ",\n"
        f' "slides": [{lo} a {hi} slides' + (", o primeiro do tipo veredito"
                                             if mito else "") + "],\n"
        ' "chamada_final": "pedido para salvar ou mandar a um colega, ate 45 '
        'caracteres, com ==destaque==",\n'
        ' "pergunta_final": "pergunta curta para os comentarios, ligada ao '
        'tema, ate 60 caracteres",\n'
        ' "legenda": "legenda do post"\n'
        "}\n"
        "ilustracao: uma de dinamometro, cronometro, cadeira, percurso, "
        "haltere, coracao, coluna, documento, balanca, osso, aro, grafico, "
        "alvo, ou vazio se nenhuma combinar.\n"
        "LEGENDA: gancho na primeira linha (pergunta ou frase forte tirada "
        "dos fatos); 2 ou 3 paragrafos curtos so com o que os fatos dizem; "
        "uma linha 'Neste carrossel: ...'; '👉 Salve para consultar depois e "
        "mande para um colega.'; '💬 ' e a pergunta final. NAO escreva "
        "fontes, hashtags nem assinatura: o robo poe. Ate 1.200 caracteres."
        + (f"\n\nATENCAO, a versao anterior foi recusada:\n{aviso}" if aviso else ""))


def _legenda_aula(spec, pauta):
    """Legenda da IA + fontes, assinatura e hashtags fixas do robo."""
    linhas = [l for l in spec["legenda"].strip().split("\n")
              if not l.strip().lower().startswith(
                  ("fonte", "📚", "#", "conteúdo fisiosync", "conteudo fisiosync"))]
    corpo = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()
    fontes = "; ".join(dict.fromkeys(f["fonte"] for f in pauta["fatos"]
                                     if f.get("fonte")))
    tags = ["#fisioterapia", "#fisioterapeuta",
            _HASHTAG_EIXO.get(pauta.get("eixo", ""), ""), "#FisioSync"]
    return (f"{corpo}\n\n📚 Fontes: {fontes}. Referências completas no "
            "penúltimo slide.\n\nConteúdo FisioSync. Teste grátis por 7 dias: "
            "app.fisiosync.com.br\n\n" + " ".join(t for t in tags if t))


def gerar_aula(cfg, pauta, estilo, base_feed, base_story):
    """
    Escreve, confere e monta o carrossel novo. Ate 3 tentativas; cada
    recusa volta para a IA com o motivo. Devolve (spec, feed, story) ou
    None se nada passar nas travas.
    """
    import aula
    fatos_txt = "\n".join(f"{i}. {f['texto']}"
                          for i, f in enumerate(pauta["fatos"], 1))
    fontes_txt = "; ".join(dict.fromkeys(f["fonte"] for f in pauta["fatos"]))
    aviso = ""
    for tentativa in (1, 2, 3):
        pedido = _pedido_aula(pauta, estilo, aviso)
        bruto = None
        if cfg.get("OPENAI_API_KEY"):
            bruto = _openai_texto(cfg["OPENAI_API_KEY"], pedido)
        if not bruto and cfg.get("GEMINI_API_KEY"):
            bruto = _gemini_texto(cfg["GEMINI_API_KEY"], pedido)
        spec = _extrair_json(bruto) if bruto else None
        if not isinstance(spec, dict):
            log(f"AVISO: a IA nao devolveu o carrossel (tentativa {tentativa}).")
            aviso = "A resposta nao era o JSON pedido. Responda SOMENTE o JSON."
            continue
        if spec.get("legenda"):
            spec["legenda"] = revisar_legenda(cfg, spec["legenda"])
        problemas = aula.validar(spec, pauta, estilo) + _numeros_aula(spec, pauta)
        if not problemas:
            ok, probs = conferir_veracidade(
                cfg, aula.para_revisao(spec, pauta, estilo), fatos_txt,
                fontes_txt, pauta.get("observacao", ""),
                "mito" if estilo == "mito" else "sabia")
            if not ok:
                problemas = [f"revisor de veracidade: {p}" for p in probs]
        if problemas:
            log(f"Carrossel {estilo}, tentativa {tentativa}: recusado.")
            for p in problemas[:8]:
                log(f"  - {p}")
            aviso = "Corrija TODOS estes problemas:\n- " + "\n- ".join(problemas[:12])
            continue
        log("Revisao de veracidade do carrossel: APROVADO (tudo apoiado nos fatos).")
        try:
            feed, story = aula.montar(spec, pauta, estilo, base_feed, base_story)
        except (layouts.TextoNaoCabe, aula.EspecInvalida) as falha:
            log(f"AVISO: {falha}")
            aviso = (f"O texto nao coube na arte ({falha}). Encurte esse slide "
                     "e os textos mais longos.")
            continue
        return spec, feed, story
    return None


def _fluxo_aula(cfg, args, carimbo):
    """
    Post das 9h ("aula") ou das 15h ("mito") no formato novo. Devolve
    False sem publicar nada quando nao ha pauta de varios fatos ou quando
    o formato novo falha antes de publicar: o main segue no formato de
    antes, e o post do dia nao se perde.
    """
    estilo = args.estilo
    if args.pauta_json:
        if not args.previa:
            erro("--pauta-json e so para teste: use junto com --previa.")
        with open(args.pauta_json, encoding="utf-8") as f:
            p = json.load(f)
        log(f"Pauta de teste: {p['tema']}")
    else:
        try:
            p = PT.proxima_pauta(ler_historico(limite=500), log, formato=estilo)
        except Exception as e:  # noqa: BLE001 - o post do dia nao pode cair
            log(f"AVISO: nao consegui escolher a pauta do formato novo ({e}).")
            p = None
    if not p:
        log(f"Sem pauta de varios fatos para o formato '{estilo}'. "
            "Seguindo no formato de antes.")
        return False
    log(f"Formato novo ({estilo}): {p['tema']} "
        f"({len(p.get('fatos') or [])} fatos conferidos)")
    apelido = re.sub(r"[^a-z0-9]+", "-", p["tema"].lower())[:40].strip("-")
    base_feed = os.path.join(PASTA_SAIDA, f"fisiosync_{apelido}_{estilo}")
    try:
        r = gerar_aula(cfg, p, estilo, base_feed, base_feed + "_story")
    except Exception as e:  # noqa: BLE001 - Chrome que nao abre etc.
        log(f"AVISO: o formato novo falhou ({type(e).__name__}: {e}). "
            "Seguindo no formato de antes.")
        return False
    if not r:
        log("AVISO: o carrossel novo nao passou nas travas em 3 tentativas. "
            "Seguindo no formato de antes.")
        return False
    spec, feed, story = r
    legenda = _legenda_aula(spec, p)
    with open(os.path.join(PASTA_SAIDA, f"legenda-{carimbo}.txt"), "w",
              encoding="utf-8") as f:
        f.write(legenda + "\n\n----- slides -----\n"
                + json.dumps(spec, ensure_ascii=False, indent=1))
    log(f"Carrossel {estilo} montado: {len(feed)} imagens + story")
    print("\n--- LEGENDA ---\n" + legenda + "\n---------------\n")

    if args.previa:
        print("PREVIA PRONTA. Nada foi publicado.")
        for a in feed + [story]:
            print("  " + a)
        return True

    if os.environ.get("FORCAR") != "1":
        no_ar = feed_recente_no_instagram(cfg)
        if no_ar:
            erro(f"Outro processo publicou enquanto eu montava ({no_ar}). "
                 "Nao publico duplicado.")
    if not args.so_story:
        links = [subir_para_github(cfg, a, f"feed-{carimbo}-{n}.jpg")
                 for n, a in enumerate(feed, 1)]
        publicar_carrossel(cfg, links, legenda)
    if not args.so_feed:
        link = subir_para_github(cfg, story, f"story-{carimbo}.jpg")
        publicar(cfg, link, story=True)

    capa = spec.get("capa") or {}
    c = {"tema": p["tema"], "pauta": p["tema"], "eixo": p.get("eixo", ""),
         "familia": p.get("familia", ""), "fonte": p.get("fonte", ""),
         "apoio": spec.get("pergunta_final", ""),
         "titulo": p.get("afirmacao") if estilo == "mito" else capa.get("titulo", ""),
         "layout": f"carrossel-{estilo}", "estilo": estilo, "objetivo": "salvar"}
    gravar_historico(registro_completo(c, p["tema"], feed + [story],
                                       "publicado", estilo))
    print("\n" + "=" * 56 + "\n  TUDO PUBLICADO COM SUCESSO\n" + "=" * 56)
    return True


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


def publicar_carrossel(cfg, links, legenda):
    """Carrossel: um container por imagem, depois o container pai."""
    ig, tok = cfg["ID"], cfg["TOKEN"]
    log(f"Publicando carrossel com {len(links)} imagens...")
    filhos = []
    for link in links:
        r = graph("POST", f"{ig}/media", tok, image_url=link,
                  is_carousel_item="true")
        filhos.append(r["id"])
    for f in filhos:
        inicio = time.time()
        while time.time() - inicio < 180:
            st = graph("GET", f, tok, fields="status_code,status")
            if st.get("status_code") == "FINISHED":
                break
            if st.get("status_code") in ("ERROR", "EXPIRED"):
                erro(f"A Meta nao aceitou um slide: {st.get('status')}")
            time.sleep(4)
        else:
            erro("A Meta demorou demais processando um slide.")
    pai = graph("POST", f"{ig}/media", tok, media_type="CAROUSEL",
                children=",".join(filhos), caption=legenda or "")["id"]
    inicio = time.time()
    while time.time() - inicio < 180:
        st = graph("GET", pai, tok, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            erro(f"A Meta nao aceitou o carrossel: {st.get('status')}")
        time.sleep(5)
    media_id = graph("POST", f"{ig}/media_publish", tok, creation_id=pai)["id"]
    try:
        link = graph("GET", media_id, tok, fields="permalink").get("permalink")
    except SystemExit:
        link = "(sem link)"
    log(f"PUBLICADO carrossel: {link}")
    return media_id


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
    ap.add_argument("--carrossel", action="store_true",
                    help="feed em carrossel: capa + slides do fato + fechamento")
    ap.add_argument("--estilo", choices=["sabia", "mito", "aula"], default="sabia",
                    help="carrossel 'aula' ou 'Voce sabia?' (9h), 'Mito ou verdade?' (15h)")
    ap.add_argument("--pauta-json", default=None,
                    help="so para teste com --previa: pauta de varios fatos num arquivo")
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
        no_ar = feed_recente_no_instagram(cfg)
        if no_ar:
            log(f"O perfil ja tem post de feed nas ultimas 3 horas ({no_ar}). "
                "Nao vou publicar de novo.")
            return
        log(f"Janela da {janela} de {data_br}, {hora} em Brasilia. "
            "Ainda nao publicada: seguindo.")

    atualizar_logo(cfg)

    # Formato novo (08/11/2026): aula as 9h e mito as 15h, quando o banco
    # tem pauta de varios fatos. Sem ela, ou se o formato novo falhar
    # antes de publicar, segue tudo como antes.
    if (args.carrossel and args.estilo in ("aula", "mito")
            and not (args.brief or args.tema)):
        if _fluxo_aula(cfg, args, carimbo):
            return
        if args.estilo == "aula":
            args.estilo = "sabia"

    if args.brief:
        with open(args.brief, encoding="utf-8") as f:
            c = json.load(f)
        log(f"Briefing carregado de {os.path.basename(args.brief)}")
        log(f"Tema: {c.get('tema')}")
        log(f"Conceito: {c.get('conceito')}")
    else:
        # Sem --tema, a IA escolhe sozinha, olhando o historico
        c = gerar_conteudo(cfg, args.tema, carrossel=args.carrossel,
                           estilo=args.estilo)
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
    if c.get("slides"):
        c["layout"] = "calibrado"   # a capa do carrossel leva ilustracao
    if c.get("layout") == "tipografico":
        log("Layout tipografico: a tipografia e o visual, sem gerar imagem.")
        foto = ""
    else:
        log("Gerando a imagem com IA. Leva de 30 a 90 segundos, aguarde...")
        log(f"  cena pedida: {c['foto'][:110]}")
        try:
            gerar_foto(cfg, c, foto, c["layout"])
        except SystemExit:
            # sem imagem o post ainda sai, em layout tipografico. Se era
            # carrossel, a capa (que pede para arrastar) nao vai sozinha.
            if c.get("slides"):
                c = _sem_carrossel(c, "sem ilustracao para a capa")
                tema = c["tema"]
            log("AVISO: sem ilustracao hoje. Saindo em layout tipografico.")
            c["layout"], c["slides"], foto = "tipografico", [], ""

    quer_feed = not args.so_story
    quer_story = not args.so_feed

    apelido = re.sub(r"[^a-z0-9]+", "-",
                     tema.lower().replace("ç", "c"))[:40].strip("-")
    base_feed = os.path.join(PASTA_SAIDA, f"fisiosync_{apelido}_feed")
    base_story = os.path.join(PASTA_SAIDA, f"fisiosync_{apelido}_stories")

    # Carrossel PRIMEIRO: capa sem assinatura + slides do fato +
    # fechamento. Nunca corta texto: se algum slide nao couber, o post
    # vira o "so fato" ANTES de montar feed e story, para nenhuma peca
    # sair com a capa que pede para arrastar (07/11/2026).
    slides_arq = []
    if quer_feed and c.get("slides"):
        import carrossel
        try:
            capa = molde.montar(foto, c["titulo"], c["apoio"],
                                base_feed + "_capa", "feed",
                                layout="calibrado",
                                sobretitulo=c.get("sobretitulo", ""),
                                capa=True, fonte=c.get("fonte", ""))
            total = len(c["slides"]) + 2
            slides_arq = [capa] + carrossel.montar(
                c["slides"], c["fechamento"], c.get("fonte", ""),
                base_feed, primeiro_numero=2, total=total)
            log(f"Carrossel montado: {len(slides_arq)} imagens")
        except layouts.TextoNaoCabe as falha:
            c = _sem_carrossel(c, f"slide nao coube ({falha})")
            tema, foto, slides_arq = c["tema"], "", []

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
            # no "Mito ou verdade?" o story nao pode mostrar a afirmacao
            # sem a resposta: quem so ve o story sairia com o mito
            apoio_story = c["apoio"]
            if c.get("slides") and args.estilo == "mito":
                resp = c["slides"][0]["titulo"].strip().rstrip(".")
                apoio_story = f"{resp}. Veja o porquê no post de hoje."
            arq_story = molde.montar(foto, c["titulo"], apoio_story, base_story,
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
        for n, sl in enumerate(c.get("slides") or [], 2):
            f.write(f"\nSLIDE {n}: {sl['titulo']}\n{sl['texto']}\n")
        if c.get("slides"):
            f.write(f"\nFECHAMENTO: {c.get('fechamento')}\n")

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

    if os.environ.get("FORCAR") != "1":
        no_ar = feed_recente_no_instagram(cfg)
        if no_ar:
            erro(f"Outro processo publicou enquanto eu montava ({no_ar}). "
                 "Nao publico duplicado.")
    if quer_feed and slides_arq:
        links = [subir_para_github(cfg, a, f"feed-{carimbo}-{n}.jpg")
                 for n, a in enumerate(slides_arq, 1)]
        publicar_carrossel(cfg, links, c["legenda"])
    elif quer_feed:
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
