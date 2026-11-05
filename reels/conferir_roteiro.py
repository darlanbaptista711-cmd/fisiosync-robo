#!/usr/bin/env python3
"""
Revisao de veracidade de um roteiro de Reels, antes de montar o video.

Mesmo revisor do carrossel (postador.conferir_veracidade): compara a fala,
cada tela e a legenda com o FATO CONFERIDO do roteiro. Sem aprovacao, o
Reels NAO vai ao ar e o workflow avisa por e-mail (criado em 05/11/2026,
depois que uma auditoria independente achou erros de redacao em volta de
fatos corretos).

Uso:
  python3 reels/conferir_roteiro.py reels/roteiro-hoje.json   (sai 1 se reprovar)
  python3 reels/conferir_roteiro.py --todos                   (relatorio da fila)
"""
import glob
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import postador  # noqa: E402


def dados_do_roteiro(r):
    """Tudo o que vai ao ar, no formato que o revisor le."""
    resp, extra = r.get("resposta", {}), r.get("extra", {})
    slides = [
        {"titulo": resp.get("destaque", ""),
         "texto": f"{resp.get('complemento', '')} (fonte na tela: {resp.get('fonte', '')})"},
        {"titulo": extra.get("titulo", ""), "texto": extra.get("texto", "").replace("\n", " ")},
        {"titulo": "Frase da tela final", "texto": (r.get("fecho") or {}).get("frase", "")},
    ]
    return {
        "sobretitulo": r.get("pergunta", {}).get("rotulo", ""),
        "titulo": " ".join(r.get("pergunta", {}).get("linhas", [])),
        "apoio": "",
        "slides": slides,
        "legenda": f"NARRACAO FALADA: {r.get('narracao', '')}\n\nLEGENDA: {r.get('legenda', '')}",
    }


def conferir(caminho, cfg):
    r = json.load(open(caminho, encoding="utf-8"))
    ok, problemas = postador.conferir_veracidade(
        cfg, dados_do_roteiro(r), r.get("fato", ""), r.get("fonte", ""))
    return r, ok, problemas


def main():
    cfg = {"OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
           "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY")}
    if not (cfg["OPENAI_API_KEY"] or cfg["GEMINI_API_KEY"]):
        sys.exit("[veracidade] sem chave de IA: nao da para revisar, nao publico.")

    if len(sys.argv) > 1 and sys.argv[1] == "--todos":
        try:
            feitos = {h.get("titulo") for h in json.load(
                open(os.path.join(RAIZ, "reels", "historico-reels.json"), encoding="utf-8"))}
        except (FileNotFoundError, json.JSONDecodeError):
            feitos = set()
        reprovados = 0
        for c in sorted(glob.glob(os.path.join(RAIZ, "reels", "fila", "*.json"))):
            r = json.load(open(c, encoding="utf-8"))
            if r.get("interesse") != "alto" or r.get("titulo") in feitos:
                continue
            _, ok, problemas = conferir(c, cfg)
            nome = os.path.basename(c)
            print(f"[veracidade] {'APROVADO ' if ok else 'REPROVADO'} {nome}")
            for p in problemas:
                print(f"      - {p}")
            reprovados += 0 if ok else 1
        print(f"[veracidade] {reprovados} reprovado(s)")
        return

    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "reels", "roteiro-hoje.json")
    r, ok, problemas = conferir(caminho, cfg)
    if ok:
        print(f"[veracidade] APROVADO: {r.get('titulo')}")
        return
    print(f"[veracidade] REPROVADO: {r.get('titulo')}. O Reels NAO vai ao ar.")
    for p in problemas:
        print(f"  - {p}")
    sys.exit(1)


if __name__ == "__main__":
    main()
