#!/usr/bin/env python3
"""
Le as metricas do Instagram da FisioSync e escreve um relatorio.

O que entra:
  - conta: seguidores, numero de posts
  - cada post recente: curtidas, comentarios e, se o token tiver a
    permissao instagram_manage_insights, alcance, visualizacoes,
    salvamentos, envios (shares) e seguidores ganhos

Por que estes numeros: o Instagram disse que os sinais que mais pesam
hoje sao envios por DM, retencao e originalidade. Curtida sozinha diz
pouco. O relatorio ordena os posts por envios e salvamentos, que e o
que traz gente nova.

Sem a permissao de metricas, o script nao quebra: le o que da e diz o
que esta faltando.

Grava metricas/AAAA-MM-DD.json e metricas/RELATORIO.md.
Ambiente: IG_USER_ID, IG_ACCESS_TOKEN
"""

import datetime
import json
import os
import sys

import requests

GRAPH = "https://graph.facebook.com/v23.0"
ID = os.environ.get("IG_USER_ID")
TOKEN = os.environ.get("IG_ACCESS_TOKEN")
PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metricas")
QUANTOS = 30

# Metricas por tipo de post. O Instagram recusa o pedido inteiro se uma
# metrica nao vale para aquele tipo, entao cada tipo tem a sua lista.
METRICAS = {
    "REELS": ["views", "reach", "saved", "shares", "total_interactions",
              "ig_reels_avg_watch_time"],
    "FEED": ["views", "reach", "saved", "shares", "total_interactions",
             "follows", "profile_visits"],
}


def get(caminho, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{GRAPH}/{caminho}", params=params, timeout=30)
    j = r.json()
    if "error" in j:
        return None, j["error"]
    return j, None


def insights_do_post(media_id, tipo):
    lista = METRICAS.get(tipo, METRICAS["FEED"])
    j, erro = get(f"{media_id}/insights", metric=",".join(lista))
    if erro:
        # permissao: nao adianta tentar uma a uma
        if erro.get("code") in (10, 200) or "permission" in str(erro).lower():
            return None, "sem_permissao"
        # alguma metrica nao vale para este post: tenta uma por uma
        saida = {}
        for m in lista:
            jj, e = get(f"{media_id}/insights", metric=m)
            if jj:
                for item in jj.get("data", []):
                    saida[item["name"]] = item["values"][0]["value"]
        return saida, None
    return {i["name"]: i["values"][0]["value"] for i in j.get("data", [])}, None


def main():
    if not ID or not TOKEN:
        sys.exit("faltam IG_USER_ID e IG_ACCESS_TOKEN")
    os.makedirs(PASTA, exist_ok=True)

    conta, erro = get(ID, fields="username,followers_count,follows_count,media_count")
    if erro:
        sys.exit(f"nao consegui ler a conta: {erro.get('message')}")

    midia, erro = get(f"{ID}/media", limit=QUANTOS,
                      fields="id,caption,media_type,media_product_type,timestamp,"
                             "permalink,like_count,comments_count")
    if erro:
        sys.exit(f"nao consegui listar os posts: {erro.get('message')}")

    posts = []
    falta_permissao = False
    for m in midia.get("data", []):
        tipo = "REELS" if m.get("media_product_type") == "REELS" else "FEED"
        ins, problema = insights_do_post(m["id"], tipo)
        if problema == "sem_permissao":
            falta_permissao = True
            ins = {}
        legenda = (m.get("caption") or "").strip().split("\n")[0][:90]
        posts.append({
            "data": m["timestamp"][:16].replace("T", " "),
            "tipo": tipo,
            "titulo": legenda,
            "link": m.get("permalink"),
            "curtidas": m.get("like_count", 0),
            "comentarios": m.get("comments_count", 0),
            **(ins or {}),
        })

    hoje = datetime.date.today().isoformat()
    dados = {"lido_em": datetime.datetime.utcnow().isoformat() + "Z",
             "conta": conta, "posts": posts,
             "falta_permissao_de_metricas": falta_permissao}
    with open(os.path.join(PASTA, f"{hoje}.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)

    # ------------------------------ relatorio ------------------------------
    L = [f"# Instagram @{conta.get('username')} — {hoje}", "",
         f"- Seguidores: **{conta.get('followers_count')}**",
         f"- Posts publicados: {conta.get('media_count')}", ""]
    if falta_permissao:
        L += ["> **Falta a permissão de métricas** (`instagram_manage_insights`). "
              "Sem ela, só dá para ler curtidas e comentários. Alcance, "
              "visualizações, salvamentos e envios precisam de um token novo "
              "com essa permissão.", ""]

    def peso(p):
        # o que traz gente nova primeiro: envios, depois salvamentos
        return (p.get("shares", 0) * 3 + p.get("saved", 0) * 2
                + p.get("comentarios", 0) + p.get("curtidas", 0) * 0.2)

    ordem = sorted(posts, key=peso, reverse=True)
    cab = "| data | tipo | post | curt. | coment. |"
    sep = "|---|---|---|---|---|"
    if not falta_permissao:
        cab = "| data | tipo | post | alcance | views | envios | salvos | curt. | coment. |"
        sep = "|---|---|---|---|---|---|---|---|---|"
    L += ["## Posts, do que mais trouxe gente nova para o que menos", "", cab, sep]
    for p in ordem:
        t = p["titulo"].replace("|", "/")[:60] or "(sem legenda)"
        if falta_permissao:
            L.append(f"| {p['data']} | {p['tipo']} | [{t}]({p['link']}) | "
                     f"{p['curtidas']} | {p['comentarios']} |")
        else:
            L.append(f"| {p['data']} | {p['tipo']} | [{t}]({p['link']}) | "
                     f"{p.get('reach','-')} | {p.get('views','-')} | "
                     f"{p.get('shares','-')} | {p.get('saved','-')} | "
                     f"{p['curtidas']} | {p['comentarios']} |")

    for tipo in ("REELS", "FEED"):
        g = [p for p in posts if p["tipo"] == tipo]
        if g:
            media = lambda k: sum(p.get(k, 0) for p in g) / len(g)
            L += ["", f"**{tipo}** ({len(g)} posts): média de "
                  f"{media('curtidas'):.1f} curtidas e {media('comentarios'):.1f} "
                  "comentários" + ("" if falta_permissao else
                  f", {media('reach'):.0f} de alcance, {media('shares'):.1f} envios "
                  f"e {media('saved'):.1f} salvamentos") + " por post."]

    with open(os.path.join(PASTA, "RELATORIO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
