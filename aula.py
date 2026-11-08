"""
CARROSSEL NO FORMATO NOVO: "aula" (9h) e "mito ou verdade" (15h).

Aprovado pelo Darlan em 08/11/2026, a partir de carrosseis que deram
resultado em perfis de fisioterapia (NAIUEPA, @cinesio.lab):

  - uma pergunta por slide, que da motivo para arrastar;
  - pouco texto e muito destaque: numero grande, caixinhas, passos;
  - fonte em todo slide e um slide de referencias no fim;
  - cara de serie: mesmo cabecalho, mesma cor, numeracao "05/10";
  - o ultimo slide puxa conversa ("Qual tema voce quer ver por aqui?").

Este modulo so MONTA: recebe a especificacao dos slides (escrita pela IA
a partir dos fatos conferidos da pauta, em postador.gerar_aula) e devolve
as imagens. Tambem confere a especificacao antes de montar.

O render e HTML no Chrome (Playwright), com a fonte Inter embutida, para
o resultado no GitHub ser igual ao da amostra aprovada. Texto que nao
cabe NAO e cortado: levanta layouts.TextoNaoCabe e quem chama decide.
"""
import base64
import html
import math
import os
import re

import layouts

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_FONTES = os.path.join(PASTA, "fontes")
ARQ_LOGO = os.path.join(PASTA, "logo.png")

# A API de publicacao do Instagram aceita ate 10 itens num carrossel.
MAX_SLIDES = 10
# capa + conteudo + referencias + fechamento
CONTEUDO = {"aula": (5, 7), "mito": (4, 6)}

TIPOS = ("destaque", "numero", "cards", "lista", "passos", "duas", "fluxo",
         "veredito")

# limites de caracteres (sem os marcadores ** e ==). O render ainda
# confere se coube; isto so evita pedir ao navegador o impossivel.
LIM = {"titulo": 44, "destaque": 95, "texto": 200, "card_titulo": 42,
       "card_texto": 175, "item": 120, "numero": 14, "rotulo": 14,
       "valor": 9, "unidade": 6, "selo": 14, "nota": 160, "puxa": 32,
       "capa_titulo": 40, "promessa": 26, "pergunta_final": 64,
       "chamada_final": 52}


class EspecInvalida(Exception):
    pass


# ----------------------------------------------------------------- fontes
_FONTES = [("Inter", 400, "normal", "Inter-Regular"),
           ("Inter", 400, "italic", "Inter-Italic"),
           ("Inter", 500, "normal", "Inter-Medium"),
           ("Inter", 600, "normal", "Inter-SemiBold"),
           ("Inter", 700, "normal", "Inter-Bold"),
           ("Inter", 800, "normal", "Inter-ExtraBold"),
           ("Inter Display", 800, "normal", "InterDisplay-ExtraBold"),
           ("Inter Display", 900, "normal", "InterDisplay-Black")]


def _css_fontes():
    regras = []
    for familia, peso, estilo, arq in _FONTES:
        with open(os.path.join(PASTA_FONTES, arq + ".woff"), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        regras.append(f"@font-face{{font-family:'{familia}';font-weight:{peso};"
                      f"font-style:{estilo};src:url(data:font/woff;base64,{b64}) "
                      f"format('woff')}}")
    return "".join(regras)


def _logo_b64():
    with open(ARQ_LOGO, "rb") as f:
        return base64.b64encode(f.read()).decode()


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#F3F7F9;--navy:#0B2948;--cyan:#18B7D8;--cyan2:#0E9DBC;--soft:#E2F5FA;
--ink:#1E3A57;--muted:#73879B;--line:#DCE6EC;--mito:#C2410C}
html,body{width:var(--W);height:var(--H)}
body{background:var(--bg);font-family:'Inter',sans-serif;color:var(--ink);
-webkit-font-smoothing:antialiased;position:relative;overflow:hidden}
b{font-weight:700;color:var(--navy)}
.c{color:var(--cyan)}
.pg{position:absolute;inset:0;padding:78px 84px 0 84px}
.topo{font-size:21px;font-weight:600;letter-spacing:4.5px;color:var(--navy);
text-transform:uppercase;display:flex;gap:14px;white-space:nowrap}
.topo .sec{color:var(--cyan2)}
.traco{width:72px;height:7px;border-radius:9px;background:var(--cyan);margin:30px 0 40px}
h1{font-family:'Inter Display','Inter',sans-serif;font-weight:800;font-size:92px;
line-height:1.02;letter-spacing:-2px;color:var(--navy)}
h1 .c{color:var(--cyan)}
.lead{font-size:38px;line-height:1.3;font-weight:700;color:var(--navy);margin-top:26px}
.txt{font-size:35px;line-height:1.38;color:var(--ink);margin-top:22px}
.nota{font-size:29px;line-height:1.38;color:var(--muted);margin-top:22px}
.card{background:#fff;border:2px solid var(--line);border-radius:26px;padding:32px 36px;
font-size:34px;line-height:1.36;color:var(--ink);margin-top:20px}
.card.hl{background:var(--soft);border-color:transparent}
.card.grande{font-size:38px;font-weight:700;color:var(--navy);margin-top:40px}
.card .t{font-weight:800;color:var(--navy);font-size:35px;display:block;margin-bottom:6px}
.big{font-family:'Inter Display','Inter',sans-serif;font-weight:900;font-size:180px;
line-height:1;letter-spacing:-6px;color:var(--navy);margin-top:30px;white-space:nowrap}
.big .s{color:var(--cyan)} .big .u{font-size:84px;letter-spacing:-2px;margin-left:10px}
.lista .card{padding:24px 32px;margin-top:14px}
.passos .card{display:flex;gap:26px;align-items:center}
.num{flex:none;width:74px;height:74px;border-radius:50%;background:var(--navy);color:#fff;
font-family:'Inter Display',sans-serif;font-weight:800;font-size:38px;display:flex;
align-items:center;justify-content:center}
.duas{display:flex;gap:24px;margin-top:40px}
.duas .card{flex:1;margin:0;text-align:center;padding:60px 18px}
.duas .rot{font-size:30px;font-weight:700;letter-spacing:4px;color:var(--cyan2);text-transform:uppercase}
.duas .val{font-family:'Inter Display',sans-serif;font-weight:900;font-size:140px;
letter-spacing:-4px;color:var(--navy);line-height:1.05;margin-top:10px;white-space:nowrap}
.duas .val .s{color:var(--cyan)} .duas .val small{font-size:56px;letter-spacing:-1px}
.fluxo{margin-top:40px}
.fluxo .card{display:flex;justify-content:space-between;align-items:center;gap:18px;
margin-top:0;padding:34px 36px;font-size:35px}
.seta{text-align:center;color:var(--cyan);font-size:46px;line-height:1;height:58px;padding-top:6px}
.selo{flex:none;background:var(--navy);color:#fff;border-radius:999px;padding:16px 28px;
font-size:29px;font-weight:700}
.selo.s2{background:var(--cyan2)} .selo.s3{background:var(--mito)}
.veredito{font-family:'Inter Display',sans-serif;font-weight:900;font-size:200px;line-height:1;
letter-spacing:-7px;margin-top:10px}
.veredito.mito{color:var(--mito)} .veredito.verdade{color:var(--cyan2)}
.pill{display:inline-block;background:var(--navy);color:#fff;border-radius:999px;padding:14px 30px;
font-size:28px;font-weight:800;letter-spacing:4px;text-transform:uppercase}
.refs p{font-size:var(--fr,29px);line-height:1.42;color:var(--ink);margin-top:30px;overflow-wrap:anywhere}
.refs b{color:var(--navy)}
.base{position:absolute;left:84px;right:84px;bottom:112px;display:flex;flex-direction:column;gap:18px}
.fonte{font-size:22px;color:var(--muted);line-height:1.35}
.puxa{align-self:flex-end;font-size:29px;font-weight:700;color:var(--cyan2)}
.rodape{position:absolute;left:84px;right:84px;bottom:50px;display:flex;align-items:center;
justify-content:space-between}
.rodape img{height:44px}
.rodape .n{font-size:25px;font-weight:600;color:var(--muted);letter-spacing:1px}
.ilu{position:absolute;right:60px}
.icones{display:flex;justify-content:space-between;margin-top:84px}
.icones div{text-align:center;width:200px}
.icones span{display:block;font-size:25px;font-weight:700;letter-spacing:2px;color:var(--navy);
margin-top:12px;text-transform:uppercase}
"""

# ------------------------------------------------------------ ilustracoes
_N, _C = "#0B2948", "#18B7D8"


def _gauge_ticks(cx, cy, r1, r2, n, a0, a1):
    out = []
    for k in range(n):
        ang = math.radians(a0 - k * (a0 - a1) / (n - 1))
        x1, y1 = cx + r1 * math.cos(ang), cy - r1 * math.sin(ang)
        x2, y2 = cx + r2 * math.cos(ang), cy - r2 * math.sin(ang)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{_N}" stroke-width="8" stroke-linecap="round"/>')
    return "".join(out)


ILUSTRACOES = {
    "dinamometro": lambda: f"""
<circle cx="300" cy="175" r="150" fill="#fff" stroke="{_N}" stroke-width="14"/>
{_gauge_ticks(300, 175, 118, 98, 11, 210, -30)}
<line x1="300" y1="175" x2="392" y2="92" stroke="{_C}" stroke-width="14" stroke-linecap="round"/>
<circle cx="300" cy="175" r="17" fill="{_N}"/>
<text x="300" y="268" text-anchor="middle" font-family="Inter" font-weight="800" font-size="40" fill="{_N}">kg</text>
<rect x="268" y="322" width="64" height="34" rx="8" fill="{_N}"/>
<rect x="140" y="352" width="320" height="136" rx="44" fill="none" stroke="{_N}" stroke-width="14"/>
<rect x="190" y="402" width="220" height="36" rx="18" fill="{_C}"/>""",
    "cronometro": lambda: f"""
<rect x="262" y="40" width="76" height="44" rx="12" fill="{_N}"/>
<line x1="300" y1="84" x2="300" y2="112" stroke="{_N}" stroke-width="16"/>
<line x1="436" y1="146" x2="466" y2="116" stroke="{_N}" stroke-width="16" stroke-linecap="round"/>
<circle cx="300" cy="295" r="180" fill="#fff" stroke="{_N}" stroke-width="16"/>
<path d="M300 135 A160 160 0 0 1 460 295" fill="none" stroke="{_C}" stroke-width="22" stroke-linecap="round"/>
{_gauge_ticks(300, 295, 140, 118, 12, 90, -240)}
<line x1="300" y1="295" x2="395" y2="200" stroke="{_C}" stroke-width="14" stroke-linecap="round"/>
<circle cx="300" cy="295" r="18" fill="{_N}"/>""",
    "cadeira": lambda: f"""
<g stroke="{_N}" stroke-width="18" stroke-linecap="round" fill="none">
<line x1="190" y1="70" x2="190" y2="330"/><line x1="190" y1="330" x2="410" y2="330"/>
<line x1="410" y1="330" x2="410" y2="470"/><line x1="190" y1="330" x2="190" y2="470"/></g>
<g stroke="{_C}" stroke-width="16" stroke-linecap="round" fill="none">
<line x1="500" y1="330" x2="500" y2="130"/><polyline points="455,175 500,125 545,175"/></g>""",
    "percurso": lambda: f"""
<g stroke-linecap="round" fill="none">
<line x1="90" y1="170" x2="90" y2="380" stroke="{_N}" stroke-width="16"/>
<line x1="510" y1="170" x2="510" y2="380" stroke="{_C}" stroke-width="16"/>
<line x1="130" y1="275" x2="460" y2="275" stroke="{_N}" stroke-width="14"/>
<polyline points="425,235 470,275 425,315" stroke="{_N}" stroke-width="14"/>
<line x1="90" y1="430" x2="510" y2="430" stroke="{_C}" stroke-width="8" stroke-dasharray="4 24"/></g>""",
    "haltere": lambda: f"""
<rect x="180" y="232" width="240" height="36" rx="12" fill="{_N}"/>
<rect x="120" y="150" width="56" height="200" rx="16" fill="{_C}"/>
<rect x="424" y="150" width="56" height="200" rx="16" fill="{_C}"/>
<rect x="72" y="185" width="44" height="130" rx="14" fill="{_N}"/>
<rect x="484" y="185" width="44" height="130" rx="14" fill="{_N}"/>""",
    "coracao": lambda: f"""
<path d="M300 440 C 120 330 60 230 90 150 C 120 70 230 60 300 140 C 370 60 480 70 510 150 C 540 230 480 330 300 440 Z"
 fill="#fff" stroke="{_N}" stroke-width="16" stroke-linejoin="round"/>
<polyline points="110,250 220,250 255,190 300,320 340,215 365,250 490,250" fill="none"
 stroke="{_C}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>""",
    "coluna": lambda: "".join(
        f'<rect x="{230 + 40 * math.sin(k / 5 * math.pi):.0f}" y="{50 + k * 74}" width="140" '
        f'height="56" rx="18" fill="#fff" stroke="{_N}" stroke-width="13"/>'
        + (f'<ellipse cx="{300 + 40 * math.sin((k + .5) / 5 * math.pi):.0f}" cy="{50 + k * 74 + 65}" '
           f'rx="50" ry="8" fill="{_C}"/>' if k < 5 else "")
        for k in range(6)),
    "documento": lambda: f"""
<rect x="160" y="40" width="270" height="380" rx="26" fill="#fff" stroke="{_N}" stroke-width="15"/>
<g stroke="{_N}" stroke-width="12" stroke-linecap="round"><line x1="210" y1="120" x2="380" y2="120"/>
<line x1="210" y1="180" x2="380" y2="180"/><line x1="210" y1="240" x2="330" y2="240"/></g>
<circle cx="425" cy="395" r="78" fill="{_C}"/>
<polyline points="388,397 415,424 465,370" fill="none" stroke="#fff" stroke-width="16"
 stroke-linecap="round" stroke-linejoin="round"/>""",
    "balanca": lambda: f"""
<g stroke="{_N}" stroke-width="15" stroke-linecap="round" fill="none">
<line x1="300" y1="70" x2="300" y2="430"/><line x1="200" y1="440" x2="400" y2="440"/>
<line x1="120" y1="140" x2="480" y2="140"/>
<line x1="150" y1="140" x2="95" y2="290"/><line x1="150" y1="140" x2="205" y2="290"/>
<line x1="450" y1="140" x2="395" y2="290"/><line x1="450" y1="140" x2="505" y2="290"/></g>
<path d="M80 290 A70 50 0 0 0 220 290 Z" fill="{_C}"/>
<path d="M380 290 A70 50 0 0 0 520 290 Z" fill="{_C}"/>
<circle cx="300" cy="70" r="20" fill="{_N}"/>""",
    "osso": lambda: f"""
<g transform="rotate(-30 300 250)">
<rect x="150" y="215" width="300" height="70" rx="20" fill="#fff" stroke="{_N}" stroke-width="15"/>
<circle cx="140" cy="205" r="52" fill="#fff" stroke="{_N}" stroke-width="15"/>
<circle cx="140" cy="295" r="52" fill="#fff" stroke="{_N}" stroke-width="15"/>
<circle cx="460" cy="205" r="52" fill="#fff" stroke="{_N}" stroke-width="15"/>
<circle cx="460" cy="295" r="52" fill="#fff" stroke="{_N}" stroke-width="15"/>
<rect x="150" y="228" width="300" height="44" fill="#fff"/>
<line x1="230" y1="250" x2="370" y2="250" stroke="{_C}" stroke-width="14" stroke-linecap="round"/></g>""",
    "aro": lambda: f"""
<circle cx="300" cy="260" r="175" fill="none" stroke="{_N}" stroke-width="24"/>
<rect x="88" y="200" width="70" height="120" rx="26" fill="{_C}"/>
<rect x="442" y="200" width="70" height="120" rx="26" fill="{_C}"/>""",
    "grafico": lambda: f"""
<g stroke="{_N}" stroke-width="14" stroke-linecap="round"><line x1="90" y1="60" x2="90" y2="440"/>
<line x1="90" y1="440" x2="520" y2="440"/></g>
<rect x="140" y="320" width="70" height="105" rx="12" fill="{_N}"/>
<rect x="240" y="250" width="70" height="175" rx="12" fill="{_N}"/>
<rect x="340" y="180" width="70" height="245" rx="12" fill="{_N}"/>
<rect x="440" y="100" width="70" height="325" rx="12" fill="{_C}"/>""",
    "alvo": lambda: f"""
<circle cx="280" cy="270" r="180" fill="#fff" stroke="{_N}" stroke-width="15"/>
<circle cx="280" cy="270" r="115" fill="none" stroke="{_N}" stroke-width="15"/>
<circle cx="280" cy="270" r="50" fill="{_C}"/>
<line x1="280" y1="270" x2="500" y2="70" stroke="{_N}" stroke-width="14" stroke-linecap="round"/>
<polyline points="470,60 505,65 500,100" fill="none" stroke="{_N}" stroke-width="14"
 stroke-linecap="round" stroke-linejoin="round"/>""",
}


def _svg(chave, largura=560):
    if chave not in ILUSTRACOES:
        return ""
    alt = int(largura * 500 / 600)
    return (f'<svg width="{largura}" height="{alt}" viewBox="0 0 600 500" '
            f'xmlns="http://www.w3.org/2000/svg">{ILUSTRACOES[chave]()}</svg>')


# ------------------------------------------------------------- texto rico
def _limpo(t):
    """Texto sem marcadores, para medir e para revisar."""
    return re.sub(r"\*\*|==", "", str(t or "")).strip()


def _rico(t):
    """Escapa o HTML e troca **negrito** e ==destaque em ciano==."""
    t = html.escape(str(t or "").strip())
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r'<span class="c">\1</span>', t)
    return t


def _titulo(t, estilo=""):
    """Titulo com destaque em ciano: o marcado com ==, ou a ultima palavra."""
    t = str(t or "").strip()
    if "==" not in t:
        partes = t.rsplit(" ", 1)
        t = f"{partes[0]} =={partes[1]}==" if len(partes) == 2 else f"=={t}=="
    h = _rico(t)
    # como na amostra aprovada: o trecho em ciano no fim ganha linha propria
    m = re.match(r"^(.*\S)\s+(<span class=\"c\">[^<]*</span>)$", h)
    if m and len(_limpo(re.sub("<[^>]+>", "", m.group(1)))) <= 21:
        h = f"{m.group(1)}<br>{m.group(2)}"
    return f'<h1{estilo}>{h}</h1>'


_RE_NUM = re.compile(r"^\s*([+\-−<>≤≥≈~]?)\s*([\d][\d.,]*)\s*(%|x)?\s*(.*)$")


def _numero(t):
    m = _RE_NUM.match(str(t or ""))
    if not m:
        return _rico(t)
    sim, num, pct, unid = m.groups()
    out = f'<span class="s">{html.escape(sim)}</span>' if sim else ""
    out += html.escape(num) + (f'<span class="s">{pct}</span>' if pct else "")
    if unid:
        out += f'<span class="u">{html.escape(unid)}</span>'
    return out


# ------------------------------------------------------------- pecas comuns
def _topo(secao):
    return (f'<div class="topo"><span>FisioSync explica</span><span>|</span>'
            f'<span class="sec">{html.escape(secao)}</span></div><div class="traco"></div>')


def _rodape(n, total, logo):
    return (f'<div class="rodape"><img src="data:image/png;base64,{logo}">'
            f'<span class="n">{n:02d} / {total:02d}</span></div>')


def _card(c, hl=False):
    if isinstance(c, dict):
        t = f'<span class="t">{_rico(c.get("titulo"))}</span>' if c.get("titulo") else ""
        classe = "card hl" if (hl or c.get("destaque")) else "card"
        return f'<div class="{classe}">{t}{_rico(c.get("texto"))}</div>'
    return f'<div class="card{" hl" if hl else ""}">{_rico(c)}</div>'


def _pagina(corpo, secao, n, total, logo, fonte="", puxa=""):
    base = ((f'<div class="puxa">{_rico(puxa)} →</div>' if puxa else "")
            + (f'<div class="fonte">Fonte: {_rico(fonte)}</div>' if fonte else ""))
    return (f'<div class="pg"><div class="conteudo">{_topo(secao)}{corpo}</div></div>'
            + (f'<div class="base">{base}</div>' if base else "")
            + _rodape(n, total, logo))


# ------------------------------------------------------ slides de conteudo
def _s_destaque(s):
    out = _titulo(s["titulo"]) + f'<div class="card hl grande">{_rico(s["destaque"])}</div>'
    if s.get("texto"):
        out += f'<div class="txt">{_rico(s["texto"])}</div>'
    if s.get("card"):
        out += _card(s["card"])
    return out


def _s_numero(s):
    out = _titulo(s["titulo"]) + f'<div class="big">{_numero(s["numero"])}</div>'
    out += f'<div class="lead" style="margin-top:14px">{_rico(s["texto"])}</div>'
    if s.get("card"):
        out += _card(s["card"])
    if s.get("nota"):
        out += f'<div class="nota">{_rico(s["nota"])}</div>'
    return out


def _s_cards(s):
    itens = s["itens"]
    out = _titulo(s["titulo"]) + '<div style="margin-top:24px">'
    out += "".join(_card(c) for c in itens) + "</div>"
    if s.get("nota"):
        out += _card(s["nota"], hl=True)
    return out


def _s_lista(s):
    out = _titulo(s["titulo"])
    if s.get("texto"):
        out += f'<div class="lead" style="margin-top:22px">{_rico(s["texto"])}</div>'
    out += '<div class="lista" style="margin-top:18px">'
    out += "".join(f'<div class="card">{_rico(i)}</div>' for i in s["itens"]) + "</div>"
    if s.get("nota"):
        out += f'<div class="lead" style="font-size:31px">{_rico(s["nota"])}</div>'
    return out


def _s_passos(s):
    out = _titulo(s["titulo"]) + '<div class="passos" style="margin-top:40px">'
    out += "".join(f'<div class="card"><div class="num">{k}</div><div>{_rico(i)}</div></div>'
                   for k, i in enumerate(s["itens"], 1)) + "</div>"
    if s.get("nota"):
        out += f'<div class="card hl" style="margin-top:30px">{_rico(s["nota"])}</div>'
    return out


def _s_duas(s):
    def bloco(i):
        val = _RE_NUM.match(str(i.get("valor", "")))
        if val:
            sim, num, pct, resto = val.groups()
            v = (f'<span class="s">{html.escape(sim)}</span>' if sim else "") + html.escape(num)
            v += (pct or "") + html.escape(resto)
        else:
            v = _rico(i.get("valor"))
        un = f'<small> {html.escape(i["unidade"])}</small>' if i.get("unidade") else ""
        return (f'<div class="card"><div class="rot">{_rico(i.get("rotulo"))}</div>'
                f'<div class="val">{v}{un}</div></div>')
    out = _titulo(s["titulo"]) + '<div class="duas">' + "".join(bloco(i) for i in s["itens"]) + "</div>"
    if s.get("nota"):
        out += f'<div class="card hl" style="margin-top:32px;font-size:36px">{_rico(s["nota"])}</div>'
    return out


def _s_fluxo(s):
    partes = []
    for k, i in enumerate(s["itens"]):
        if k:
            partes.append('<div class="seta">↓</div>')
        partes.append(f'<div class="card"><div>{_rico(i["texto"])}</div>'
                      f'<span class="selo s{k + 1}">{_rico(i["selo"])}</span></div>')
    out = _titulo(s["titulo"]) + '<div class="fluxo">' + "".join(partes) + "</div>"
    if s.get("nota"):
        out += f'<div class="lead" style="margin-top:40px;font-size:40px">{_rico(s["nota"])}</div>'
    return out


def _s_veredito(s, veredito):
    classe = "mito" if veredito.lower().startswith("mito") else "verdade"
    out = (f'<h1 style="font-size:64px">A resposta é:</h1>'
           f'<div class="veredito {classe}">{html.escape(veredito.rstrip("."))}.</div>'
           f'<div class="lead" style="margin-top:34px">{_rico(s["texto"])}</div>')
    if s.get("card"):
        out += _card(s["card"], hl=True)
    return out


_MONTA = {"destaque": _s_destaque, "numero": _s_numero, "cards": _s_cards,
          "lista": _s_lista, "passos": _s_passos, "duas": _s_duas,
          "fluxo": _s_fluxo}


# ----------------------------------------------------------- capa e finais
def _tam_capa(t):
    n = len(_limpo(t))
    return 124 if n <= 24 else (108 if n <= 32 else 94)


def _capa(spec, pauta, estilo, total, logo, ilu_tam=560):
    capa = spec["capa"]
    ilu = capa.get("ilustracao", "") if ilu_tam else ""
    if estilo == "mito":
        afirm = pauta["afirmacao"].rstrip(".?! ") + "?"
        corpo = (f'<div class="pill">Mito ou verdade?</div>'
                 f'<h1 style="font-size:{_tam_capa(afirm) - 10}px;margin-top:40px;'
                 f'letter-spacing:-3px">{_rico(afirm)}</h1>'
                 f'<div style="font-size:42px;margin-top:34px;color:var(--navy)">'
                 f'Arraste e confira <b>a resposta.</b></div>')
        secao = spec.get("secao") or "Evidência"
    else:
        promessa = "".join(
            f'<div>{"<b>" if k == len(capa["promessa"]) - 1 else ""}{_rico(p)}'
            f'{"</b>" if k == len(capa["promessa"]) - 1 else ""}</div>'
            for k, p in enumerate(capa["promessa"]))
        corpo = (_titulo(capa["titulo"], f' style="font-size:{_tam_capa(capa["titulo"])}px;'
                                         f'letter-spacing:-3.5px"')
                 + f'<div style="font-size:42px;line-height:1.32;margin-top:34px;'
                   f'color:var(--navy)">{promessa}</div>')
        secao = spec.get("secao") or "Avaliação"
    ilu_html = (f'<div class="ilu" style="bottom:140px">{_svg(ilu, ilu_tam)}</div>' if ilu else "")
    return (f'<div class="pg"><div class="conteudo">{_topo(secao)}{corpo}</div></div>'
            f'{ilu_html}<div class="base"><div class="puxa">Arraste →</div></div>'
            + _rodape(1, total, logo))


def _referencias(refs, total, logo, secao="Referências"):
    corpo = '<h1>Referências</h1><div class="refs" style="margin-top:14px">'
    for r in refs:
        r = html.escape(r)
        r = re.sub(r"(doi:\s*\S+|https?://\S+)", r"<b>\1</b>", r, flags=re.I)
        corpo += f"<p>{r}</p>"
    corpo += "</div>"
    return _pagina(corpo, secao, total - 1, total, logo)


_ICONES = {
    "Curta": '<path d="M12 21s-7.5-4.6-9.6-9.2C1 8.6 3 5 6.5 5c2 0 3.3 1.1 4.1 2.3h2.8C14.2 6.1 15.5 5 17.5 5 21 5 23 8.6 21.6 11.8 19.5 16.4 12 21 12 21z"/>',
    "Comente": '<path d="M21 11.5a8.4 8.4 0 0 1-12.3 7.5L3 21l2-5.3A8.5 8.5 0 1 1 21 11.5z"/>',
    "Compartilhe": '<path d="M22 3 11 14"/><path d="M22 3l-7 19-4-8-8-4 19-7z"/>',
    "Salve": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
}


def _fechamento(spec, total, logo):
    icones = "".join(
        f'<div><svg width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="{_N}" '
        f'stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round">{p}</svg>'
        f'<span>{nome}</span></div>' for nome, p in _ICONES.items())
    chamada = spec.get("chamada_final") or "Salve para consultar depois."
    pergunta = spec.get("pergunta_final") or "Qual tema você quer ver por aqui?"
    corpo = (_titulo(chamada, f' style="font-size:{100 if _len(chamada) <= 30 else 84}px"')
             + f'<div class="card hl grande" style="margin-top:44px">{_rico(pergunta)}'
               f'<div style="font-size:31px;font-weight:500;margin-top:8px;color:var(--ink)">'
               f'Conta nos comentários.</div></div>'
             + f'<div class="icones">{icones}</div>'
             + '<div style="margin-top:90px;text-align:center;font-size:30px">Conteúdo FisioSync · '
               'Teste grátis por 7 dias: <b style="color:var(--cyan2)">app.fisiosync.com.br</b></div>')
    return _pagina(corpo, "Aprender para atender melhor", total, total, logo)


# ----------------------------------------------------------- conferencia
def _len(t):
    return len(_limpo(t))


def validar(spec, pauta, estilo):
    """Lista os problemas da especificacao. Vazia = pode montar."""
    p = []
    if not isinstance(spec, dict):
        return ["a resposta nao e um objeto JSON"]
    fatos = pauta.get("fatos") or []
    capa = spec.get("capa") or {}
    if estilo == "aula":
        if _len(capa.get("titulo")) == 0 or _len(capa.get("titulo")) > LIM["capa_titulo"]:
            p.append(f"capa.titulo vazio ou com mais de {LIM['capa_titulo']} caracteres")
        prom = capa.get("promessa")
        if not isinstance(prom, list) or not 2 <= len(prom) <= 3 or any(
                _len(x) == 0 or _len(x) > LIM["promessa"] for x in prom):
            p.append(f"capa.promessa precisa de 2 ou 3 linhas de ate {LIM['promessa']} caracteres")
    if capa.get("ilustracao") and capa["ilustracao"] not in ILUSTRACOES:
        capa["ilustracao"] = ""
    slides = spec.get("slides")
    lo, hi = CONTEUDO[estilo]
    if not isinstance(slides, list) or not lo <= len(slides) <= hi:
        return p + [f"slides precisa ter de {lo} a {hi} itens"]
    if estilo == "mito":
        if slides[0].get("tipo") != "veredito":
            p.append("no mito o primeiro slide tem que ser do tipo veredito")
        vered = str(pauta.get("veredito", "")).lower()
        if slides[0].get("veredito", "").lower().rstrip(".") != vered:
            p.append(f"o veredito tem que ser '{pauta.get('veredito')}', como diz a pauta")
    for k, s in enumerate(slides, 2):
        tag = f"slide {k}"
        if not isinstance(s, dict) or s.get("tipo") not in TIPOS:
            p.append(f"{tag}: tipo invalido")
            continue
        t = s["tipo"]
        idx = s.get("fatos")
        if (not isinstance(idx, list) or not idx
                or any(not isinstance(i, int) or not 1 <= i <= len(fatos) for i in idx)):
            p.append(f"{tag}: 'fatos' precisa listar os numeros dos fatos usados (1 a {len(fatos)})")
        if t == "veredito" and k != 2:
            p.append(f"{tag}: veredito so no primeiro slide")
        if t != "veredito" and not (0 < _len(s.get("titulo")) <= LIM["titulo"]):
            p.append(f"{tag}: titulo vazio ou com mais de {LIM['titulo']} caracteres")
        if s.get("puxa") and _len(s["puxa"]) > LIM["puxa"]:
            p.append(f"{tag}: puxa com mais de {LIM['puxa']} caracteres")
        if s.get("nota") and _len(s["nota"]) > LIM["nota"]:
            p.append(f"{tag}: nota com mais de {LIM['nota']} caracteres")
        if s.get("texto") and _len(s["texto"]) > LIM["texto"]:
            p.append(f"{tag}: texto com mais de {LIM['texto']} caracteres")
        card = s.get("card")
        if isinstance(card, dict):
            if _len(card.get("titulo")) > LIM["card_titulo"] or _len(card.get("texto")) > LIM["card_texto"]:
                p.append(f"{tag}: card grande demais")
        elif card and _len(card) > LIM["card_texto"]:
            p.append(f"{tag}: card grande demais")
        itens = s.get("itens")
        if t == "destaque" and not (0 < _len(s.get("destaque")) <= LIM["destaque"]):
            p.append(f"{tag}: destaque vazio ou longo")
        elif t == "numero":
            if not (0 < _len(s.get("numero")) <= LIM["numero"]) or not _len(s.get("texto")):
                p.append(f"{tag}: numero (ate {LIM['numero']} caracteres) e texto sao obrigatorios")
        elif t in ("cards",):
            if not isinstance(itens, list) or not 2 <= len(itens) <= 3 or any(
                    not isinstance(i, dict) or not _len(i.get("texto"))
                    or _len(i.get("titulo")) > LIM["card_titulo"]
                    or _len(i.get("texto")) > LIM["card_texto"] for i in itens):
                p.append(f"{tag}: cards precisa de 2 ou 3 itens com titulo curto e texto")
        elif t in ("lista", "passos"):
            if not isinstance(itens, list) or not 2 <= len(itens) <= (5 if t == "lista" else 4) or any(
                    not _len(i) or _len(i) > LIM["item"] for i in itens):
                p.append(f"{tag}: {t} precisa de itens curtos (ate {LIM['item']} caracteres)")
        elif t == "duas":
            if not isinstance(itens, list) or len(itens) != 2 or any(
                    not isinstance(i, dict) or not _len(i.get("valor"))
                    or _len(i.get("valor")) > LIM["valor"] or _len(i.get("rotulo")) > LIM["rotulo"]
                    or _len(i.get("unidade")) > LIM["unidade"] for i in itens):
                p.append(f"{tag}: duas precisa de 2 itens com rotulo, valor e unidade curtos")
        elif t == "fluxo":
            if not isinstance(itens, list) or not 2 <= len(itens) <= 3 or any(
                    not isinstance(i, dict) or not _len(i.get("texto")) or not _len(i.get("selo"))
                    or _len(i.get("selo")) > LIM["selo"] or _len(i.get("texto")) > LIM["item"]
                    for i in itens):
                p.append(f"{tag}: fluxo precisa de 2 ou 3 itens com texto e selo curto")
        elif t == "veredito" and not _len(s.get("texto")):
            p.append(f"{tag}: veredito precisa de texto explicando a resposta")
    for chave in ("pergunta_final", "chamada_final"):
        if _len(spec.get(chave)) > LIM[chave]:
            p.append(f"{chave} com mais de {LIM[chave]} caracteres")
    if not _len(spec.get("legenda")):
        p.append("legenda vazia")
    return p


def fontes_do_slide(s, pauta):
    """A fonte do slide sai dos fatos que ele usou, nunca da IA."""
    fatos = pauta.get("fatos") or []
    vistas = []
    for i in s.get("fatos") or []:
        if isinstance(i, int) and 1 <= i <= len(fatos):
            f = fatos[i - 1].get("fonte", "").strip()
            if f and f not in vistas:
                vistas.append(f)
    return "; ".join(vistas)


def textos_do_slide(s):
    """Todo texto visivel de um slide, sem marcadores."""
    out = [s.get(k, "") for k in ("titulo", "destaque", "texto", "numero", "nota", "puxa")]
    card = s.get("card")
    if isinstance(card, dict):
        out += [card.get("titulo", ""), card.get("texto", "")]
    elif card:
        out.append(card)
    for i in s.get("itens") or []:
        if isinstance(i, dict):
            out += [i.get(k, "") for k in ("titulo", "texto", "rotulo", "valor", "unidade", "selo")]
        else:
            out.append(i)
    return [_limpo(x) for x in out if _limpo(x)]


def para_revisao(spec, pauta, estilo):
    """Formato que o revisor de veracidade do postador entende."""
    capa = spec.get("capa") or {}
    slides = []
    for s in spec.get("slides") or []:
        textos = textos_do_slide(s)
        if s.get("tipo") == "veredito":
            slides.append({"titulo": f"{pauta.get('veredito', '').rstrip('.')}.",
                           "texto": " ".join(textos)})
        else:
            slides.append({"titulo": textos[0] if textos else "", "texto": " ".join(textos[1:])})
    if estilo == "mito":
        titulo, apoio = pauta.get("afirmacao", ""), "Arraste e confira a resposta."
    else:
        titulo, apoio = _limpo(capa.get("titulo")), " ".join(_limpo(x) for x in capa.get("promessa") or [])
    return {"sobretitulo": "Mito ou verdade?" if estilo == "mito" else "",
            "titulo": titulo, "apoio": apoio, "slides": slides,
            "legenda": spec.get("legenda", "")}


# ----------------------------------------------------------------- render
_JS_ESTOURO = """
(() => {
  const c = document.querySelector('.conteudo');
  if (!c) return null;
  const fim = c.getBoundingClientRect().bottom;
  const tetos = [...document.querySelectorAll('.base,.rodape')].map(e => e.getBoundingClientRect().top);
  const teto = tetos.length ? Math.min(...tetos) : innerHeight;
  if (fim > teto - 14) return 'o texto termina em ' + Math.round(fim) + 'px e o rodape comeca em ' + Math.round(teto) + 'px';
  for (const e of c.querySelectorAll('h1,.big,.val,.veredito,.card,.lead,.txt')) {
    if (e.scrollWidth > e.clientWidth + 2) return 'linha larga demais: ' + e.innerText.slice(0, 40);
  }
  // a ilustracao so atrapalha se alguma LINHA de texto encostar nela
  const ilu = document.querySelector('.ilu');
  if (ilu) {
    const r = ilu.getBoundingClientRect();
    const w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) {
      if (!w.currentNode.textContent.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(w.currentNode);
      for (const q of rg.getClientRects()) {
        if (q.right > r.left + 10 && q.left < r.right - 10 && q.bottom > r.top + 10 && q.top < r.bottom - 10)
          return 'texto encosta na ilustracao: ' + w.currentNode.textContent.trim().slice(0, 30);
      }
    }
  }
  return null;
})()
"""


def _abrir_navegador(p):
    erros = []
    for opcoes in ({}, {"channel": "chrome"}):
        try:
            return p.chromium.launch(**opcoes)
        except Exception as e:  # noqa: BLE001 - registra e tenta o proximo
            erros.append(str(e).splitlines()[0][:160])
    raise RuntimeError("Nao consegui abrir o Chrome: " + " | ".join(erros))


def _documento(corpo, largura, altura, fontes_css):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{fontes_css}"
            f":root{{--W:{largura}px;--H:{altura}px}}{CSS}</style></head>"
            f"<body>{corpo}</body></html>")


def renderizar(paginas, destino_base, largura=1080, altura=1350, ajustaveis=()):
    """
    Gera um JPEG por pagina. Pagina cujo indice esta em 'ajustaveis' (as
    referencias) diminui a letra ate caber; as outras, se nao couberem,
    levantam layouts.TextoNaoCabe.
    """
    from playwright.sync_api import sync_playwright
    fontes_css = _css_fontes()
    arquivos = []
    with sync_playwright() as p:
        nav = _abrir_navegador(p)
        try:
            pag = nav.new_page(viewport={"width": largura, "height": altura},
                               device_scale_factor=1)
            for i, entrada in enumerate(paginas, 1):
                # uma pagina pode vir com alternativas (capa com ilustracao
                # menor ou sem ela): vale a primeira em que o texto cabe
                opcoes = entrada if isinstance(entrada, (list, tuple)) else (entrada,)
                tamanhos = (29, 26, 23, 21, 19) if (i - 1) in ajustaveis else (None,)
                estouro = "sem opcao"
                for corpo in opcoes:
                    for tam in tamanhos:
                        extra = f"<style>:root{{--fr:{tam}px}}</style>" if tam else ""
                        pag.set_content(_documento(corpo + extra, largura, altura, fontes_css))
                        pag.evaluate("document.fonts.ready")
                        estouro = pag.evaluate(_JS_ESTOURO)
                        if not estouro:
                            break
                    if not estouro:
                        break
                if estouro:
                    raise layouts.TextoNaoCabe(f"slide {i}: {estouro}")
                arq = f"{destino_base}_{i:02d}.jpg"
                pag.screenshot(path=arq, type="jpeg", quality=92)
                arquivos.append(arq)
        finally:
            nav.close()
    return arquivos


def paginas_carrossel(spec, pauta, estilo):
    logo = _logo_b64()
    slides = spec["slides"]
    total = len(slides) + 3
    if total > MAX_SLIDES:
        raise EspecInvalida(f"{total} slides passam do limite de {MAX_SLIDES}")
    secao = spec.get("secao") or ("Evidência" if estilo == "mito" else "Avaliação")
    # texto comprido na capa: tenta a ilustracao menor e, por fim, sem ela
    paginas = [tuple(_capa(spec, pauta, estilo, total, logo, t) for t in (560, 430, 0))]
    for k, s in enumerate(slides, 2):
        if s["tipo"] == "veredito":
            corpo = _s_veredito(s, pauta.get("veredito", ""))
        else:
            corpo = _MONTA[s["tipo"]](s)
        paginas.append(_pagina(corpo, secao, k, total, logo,
                               fonte=fontes_do_slide(s, pauta), puxa=s.get("puxa", "")))
    refs = pauta.get("referencias") or [pauta.get("fonte", "")]
    paginas.append(_referencias(refs, total, logo))
    paginas.append(_fechamento(spec, total, logo))
    return paginas


def pagina_story(spec, pauta, estilo, ilu_tam=640):
    """Story 9:16. No mito mostra a resposta: quem so ve o story nao sai com o mito."""
    logo = _logo_b64()
    capa = spec["capa"]
    ilu = _svg(capa.get("ilustracao", ""), ilu_tam) if ilu_tam else ""
    if estilo == "mito":
        vered = pauta.get("veredito", "").rstrip(".")
        classe = "mito" if vered.lower().startswith("mito") else "verdade"
        afirm = pauta["afirmacao"].rstrip(".?! ") + "?"
        primeiro = spec["slides"][0]
        corpo = (f'<div class="pill">Mito ou verdade?</div>'
                 f'<h1 style="font-size:96px;margin-top:44px;letter-spacing:-3px">{_rico(afirm)}</h1>'
                 f'<div class="veredito {classe}" style="margin-top:50px">{html.escape(vered)}.</div>'
                 f'<div class="lead" style="margin-top:30px">{_rico(primeiro["texto"])}</div>')
        ilu = ""
    else:
        corpo = (f'<div class="pill">Aula nova no feed</div>'
                 + _titulo(capa["titulo"], f' style="font-size:{_tam_capa(capa["titulo"]) + 6}px;'
                                           f'margin-top:44px;letter-spacing:-3.5px"')
                 + f'<div style="font-size:46px;line-height:1.32;margin-top:36px;color:var(--navy)">'
                 + "".join(f"<div>{_rico(x)}</div>" for x in capa["promessa"]) + "</div>")
    secao = spec.get("secao") or ("Evidência" if estilo == "mito" else "Avaliação")
    return (f'<div class="pg" style="padding-top:120px"><div class="conteudo">{_topo(secao)}{corpo}'
            f'</div></div>'
            + (f'<div class="ilu" style="bottom:330px;right:220px">{ilu}</div>' if ilu else "")
            + '<div class="base" style="bottom:200px"><div class="puxa" style="align-self:center;'
              'font-size:40px">Veja o post completo no feed</div></div>'
            + f'<div class="rodape" style="bottom:90px;justify-content:center">'
              f'<img src="data:image/png;base64,{logo}" style="height:64px"></div>')


def montar(spec, pauta, estilo, base_feed, base_story):
    """Confere, monta o carrossel e o story. Devolve (lista_feed, story)."""
    problemas = validar(spec, pauta, estilo)
    if problemas:
        raise EspecInvalida("; ".join(problemas))
    paginas = paginas_carrossel(spec, pauta, estilo)
    feed = renderizar(paginas, base_feed, ajustaveis=(len(paginas) - 2,))
    story = renderizar([tuple(pagina_story(spec, pauta, estilo, t) for t in (640, 480, 0))],
                       base_story, largura=1080, altura=1920)[0]
    return feed, story
