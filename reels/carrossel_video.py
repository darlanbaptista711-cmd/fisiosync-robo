#!/usr/bin/env python3
"""
Reels das 19h feito com o carrossel do dia (decisao de 09/11/2026).

O Darlan viu que os carrosseis rendem mais que os videos de IA ("ninguem
quer ficar assistindo video por IA"), mas o Reels ainda e o formato que
mais mostra a conta para quem nao segue. Entao o Reels passa a ser o
carrossel do dia em video: os slides passando, com a trilha propria do
robo (gerada por codigo, sem direito autoral), sem voz e sem imagem de IA.

Pega o ultimo carrossel publicado hoje (imagens/feed-AAAAMMDD-HHMMSS-N.jpg,
que o postador sobe para o repositorio) e grava:
  reels/saida-hoje.mp4      1080x1920, 30 fps, com audio
  reels/roteiro-hoje.json   legenda e titulo para o reels/publicar.mjs

Uso:  python3 reels/carrossel_video.py [--data AAAAMMDD] [--saida arquivo.mp4]
"""

import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "reels"))

LARGURA, ALTURA, FPS = 1080, 1920, 30
# O Reels cobre o topo (~170px), a base (legenda e nome, ~400px) e a
# coluna de botoes da direita. O slide fica no meio, um pouco acima.
SLIDE_L, SLIDE_TOPO = 900, 190
TRANSICAO = 0.4
FUNDO = (243, 245, 249)
NAVY = (14, 42, 71)
CIANO = (14, 143, 176)


def log(msg):
    print(f"[carrossel-video] {msg}", flush=True)


def morrer(msg):
    print(f"\n[carrossel-video] FALHOU: {msg}\n", file=sys.stderr)
    sys.exit(1)


def ultimo_carrossel(data):
    """Slides do ultimo carrossel do dia, em ordem. Data no relogio do runner (UTC)."""
    grupos = {}
    for caminho in glob.glob(os.path.join(RAIZ, "imagens", f"feed-{data}-*-*.jpg")):
        m = re.search(r"feed-(\d{8}-\d{6})-(\d+)\.jpg$", caminho)
        if m:
            grupos.setdefault(m.group(1), []).append((int(m.group(2)), caminho))
    validos = {k: sorted(v) for k, v in grupos.items() if len(v) >= 3}
    if not validos:
        return None, []
    carimbo = max(validos)
    return carimbo, [c for _, c in validos[carimbo]]


def chamada_do_dia(data, n_slides):
    """Chamada, fonte, formato e eixo do carrossel no historico.

    Procura o registro do mesmo dia com o mesmo numero de slides, para a
    legenda nunca falar de um post e o video mostrar outro."""
    try:
        with open(os.path.join(RAIZ, "historico.json"), encoding="utf-8") as f:
            hist = json.load(f)
    except (OSError, ValueError):
        return "", "", "", ""
    regs = hist if isinstance(hist, list) else hist.get("posts", [])
    dia = f"{data[:4]}-{data[4:6]}-{data[6:8]}"
    do_dia = [r for r in regs if isinstance(r, dict) and r.get("status") == "publicado"
              and str(r.get("composicao", "")).startswith("carrossel")
              and str(r.get("data", ""))[:10] == dia]
    mesmos = [r for r in do_dia
              if len([a for a in r.get("arquivos", []) if "story" not in a]) == n_slides]
    if not (mesmos or do_dia):
        return "", "", "", ""
    r = (mesmos or do_dia)[-1]
    return ((r.get("chamada") or r.get("tema") or "").strip(),
            (r.get("fonte") or "").strip(), str(r.get("composicao", "")),
            str(r.get("eixo", "")))


def fonte(tam, peso="Bold"):
    try:
        return ImageFont.truetype(os.path.join(RAIZ, "fontes", f"Inter-{peso}.woff"), tam)
    except OSError:
        return None


def quadro(slide, destino, ultimo):
    """Slide 4:5 centralizado no 9:16, com o convite para o post completo."""
    tela = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    im = Image.open(slide).convert("RGB")
    alt = round(im.height * SLIDE_L / im.width)
    im = im.resize((SLIDE_L, alt), Image.LANCZOS)
    x = (LARGURA - SLIDE_L) // 2
    sombra = Image.new("RGB", (SLIDE_L + 8, alt + 8), (225, 230, 238))
    tela.paste(sombra, (x - 4, SLIDE_TOPO - 2))
    tela.paste(im, (x, SLIDE_TOPO))
    d = ImageDraw.Draw(tela)
    f1, f2 = fonte(40, "Bold"), fonte(34, "Medium")
    if f1 and f2:
        y = SLIDE_TOPO + alt + 48
        # no ultimo quadro, o convite e seguir: quem chega pelo Reels ainda nao segue
        linha1 = "Post completo, com as fontes," if not ultimo else "Siga @fisiosyncapp"
        linha2 = "no perfil @fisiosyncapp" if not ultimo else "Post completo, com as fontes, no perfil"
        for texto, f, cor in ((linha1, f1, NAVY), (linha2, f2, CIANO)):
            larg = d.textlength(texto, font=f)
            d.text(((LARGURA - larg) / 2, y), texto, font=f, fill=cor)
            y += 52
    tela.save(destino, quality=95)


def duracoes(n):
    """Capa 3s, slides do meio 2,8s, fechamento 2,5s (mais a transicao)."""
    return [3.0] + [2.8] * (n - 2) + [2.5]


def montar_video(slides, saida, pasta):
    quadros = []
    for i, s in enumerate(slides):
        q = os.path.join(pasta, f"quadro-{i + 1:02d}.jpg")
        quadro(s, q, ultimo=(i == len(slides) - 1))
        quadros.append(q)
    durs = duracoes(len(quadros))
    entradas, filtros = [], []
    for i, (q, d) in enumerate(zip(quadros, durs)):
        tempo = d + (TRANSICAO if i < len(quadros) - 1 else 0)
        entradas += ["-loop", "1", "-t", f"{tempo:.2f}", "-framerate", str(FPS), "-i", q]
        filtros.append(f"[{i}:v]scale={LARGURA}:{ALTURA},setsar=1,fps={FPS},format=yuv420p[v{i}]")
    atual, deslocamento = "v0", 0.0
    for i in range(1, len(quadros)):
        deslocamento += durs[i - 1]
        filtros.append(f"[{atual}][v{i}]xfade=transition=slideleft:duration={TRANSICAO}:"
                       f"offset={deslocamento:.2f}[x{i}]")
        atual = f"x{i}"
    total = sum(durs)
    mudo = os.path.join(pasta, "mudo.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas,
                    "-filter_complex", ";".join(filtros), "-map", f"[{atual}]",
                    "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-pix_fmt", "yuv420p", mudo], check=True)

    import musica   # trilha do robo, gerada por codigo
    os.makedirs(musica.SAIDA, exist_ok=True)
    musica.gravar(musica.trilha(total), "musica.mp3")
    trilha = os.path.join(musica.SAIDA, "musica.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mudo, "-i", trilha,
                    "-filter_complex", f"[1:a]afade=t=in:d=0.4,afade=t=out:st={total - 1.2:.2f}:d=1.2,"
                    "volume=0.8[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", saida],
                   check=True)
    return total


HASHTAG_EIXO = {"avaliacao": "#avaliacaofuncional",
                "evidencia": "#fisioterapiabaseadaemevidencias",
                "exercicio-saude": "#exerciciofisico", "pilates": "#pilates",
                "regulacao": "#coffito", "etica": "#eticaprofissional"}


def legenda(chamada, fonte_txt, composicao="", eixo=""):
    mito = composicao.endswith("mito")
    corpo = chamada.rstrip(".?! ")
    if corpo:
        corpo = f"Mito ou verdade? {corpo}?" if mito else f"{corpo}."
    partes = [corpo or "Conteúdo novo no perfil.",
              "Resumo do post de hoje. O post completo, com as fontes, está no perfil "
              "@fisiosyncapp.",
              "Salve para consultar depois e mande para um colega.",
              "Conteúdo FisioSync. Teste grátis por 7 dias: app.fisiosync.com.br",
              " ".join(t for t in ("#fisioterapia", "#fisioterapeuta",
                                   HASHTAG_EIXO.get(eixo, ""), "#FisioSync") if t)]
    if fonte_txt:
        partes.insert(2, f"📚 Fonte: {fonte_txt}")
    return "\n\n".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d"))
    ap.add_argument("--saida", default=os.path.join(RAIZ, "reels", "saida-hoje.mp4"))
    ap.add_argument("--roteiro", default=os.path.join(RAIZ, "reels", "roteiro-hoje.json"))
    args = ap.parse_args()

    carimbo, slides = ultimo_carrossel(args.data)
    if not slides:
        morrer(f"nenhum carrossel publicado em {args.data} (imagens/feed-{args.data}-*). "
               "Sem carrossel do dia, sem Reels: nao vou inventar video.")
    log(f"carrossel {carimbo}: {len(slides)} slides")

    pasta = os.path.join(RAIZ, "reels", "tmp-carrossel")
    os.makedirs(pasta, exist_ok=True)
    total = montar_video(slides, args.saida, pasta)
    log(f"video: {args.saida} ({total:.1f}s)")

    chamada, fonte_txt, composicao, eixo = chamada_do_dia(args.data, len(slides))
    roteiro = {"tipo": "carrossel", "titulo": f"carrossel-video {carimbo}",
               "legenda": legenda(chamada, fonte_txt, composicao, eixo), "fonte": fonte_txt,
               "capa_ms": 600}
    with open(args.roteiro, "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)
    log(f"roteiro: {args.roteiro} | {chamada or '(sem chamada)'}")


if __name__ == "__main__":
    main()
