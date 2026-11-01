#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acrescenta ao banco as pautas de regulacao e de carreira.

Rode uma vez. Nao duplica: pula o id que ja existe.

REGULACAO carrega FATO e FONTE conferidos. A IA escreve em volta do
fato e fica proibida de inventar numero ou data. CARREIRA nao tem fato
porque e rotina e decisao, nao norma: nada a conferir.

Fontes usadas, as duas conferidas em pagina oficial:
  - Resolucao COFFITO 414/2012, texto no coffito.gov.br e no
    normasbrasil.com.br
  - Lei 13.709/2018 (LGPD), Art. 5, II
"""

import json
import os

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(PASTA, "pautas.json")

R414 = "Resolução COFFITO nº 414/2012"
LGPD = "Lei 13.709/2018 (LGPD)"

REGULACAO = [
    ("registro em prontuario nao e opcional",
     "A Resolução COFFITO 414/2012, no Art. 1º, obriga o fisioterapeuta "
     "a registrar em prontuário todas as atividades assistenciais que "
     "presta ao cliente/paciente.", R414),
    ("os oito itens que o prontuario precisa ter",
     "O Art. 1º, §1º da Resolução COFFITO 414/2012 lista oito itens: "
     "identificação do paciente; história clínica; exame clínico/físico; "
     "exames complementares; diagnóstico e prognóstico fisioterapêuticos; "
     "plano terapêutico; evolução; e identificação do profissional.", R414),
    ("prontuario eletronico e permitido pela norma",
     "O Art. 2º da Resolução COFFITO 414/2012 diz que o registro pode ser "
     "manuscrito ou eletrônico, conforme a instituição.", R414),
    ("o que o registro eletronico exige em cada entrada",
     "O parágrafo único do Art. 2º da Resolução COFFITO 414/2012 exige "
     "que, no formato eletrônico, o profissional informe nome completo e "
     "número de registro no CREFITO logo após cada registro.", R414),
    ("letra ilegivel tambem e irregularidade",
     "O Art. 2º da Resolução COFFITO 414/2012 exige que o registro seja "
     "legível, claro e use terminologia própria da profissão.", R414),
    ("de quem e o prontuario",
     "Pela Resolução COFFITO 414/2012, o prontuário pertence ao "
     "cliente/paciente e só pode ser divulgado com autorização dele, por "
     "dever legal ou justa causa.", R414),
    ("o paciente pode pedir copia do proprio prontuario",
     "A Resolução COFFITO 414/2012 determina que o prontuário permaneça "
     "disponível para acesso do paciente ou de seu representante, que "
     "pode receber cópias autênticas.", R414),
    ("negar acesso ao prontuario e vedado",
     "A Resolução COFFITO 414/2012 veda negar ao paciente o acesso ao seu "
     "prontuário ou deixar de dar as explicações necessárias, salvo "
     "quando isso gerar risco ao paciente ou a terceiros.", R414),
    ("por quanto tempo guardar o prontuario",
     "O Art. 6º, I da Resolução COFFITO 414/2012 fixa guarda de no mínimo "
     "cinco anos a contar do último registro, prazo que pode ser ampliado "
     "por lei, decisão judicial ou necessidade específica.", R414),
    ("a guarda e responsabilidade de quem",
     "O Art. 6º da Resolução COFFITO 414/2012 põe a guarda do prontuário "
     "sob responsabilidade do fisioterapeuta ou da instituição onde a "
     "assistência foi prestada.", R414),
    ("onde o prontuario pode ficar guardado",
     "O Art. 6º, II da Resolução COFFITO 414/2012 exige que o prontuário "
     "seja mantido em local que garanta sigilo e privacidade.", R414),
    ("jogar prontuario velho no lixo nao resolve",
     "O Art. 6º, III da Resolução COFFITO 414/2012 determina que, vencido "
     "o prazo de guarda, a destruição do prontuário seja feita de forma "
     "que garanta o sigilo das informações.", R414),
    ("copia digitalizada depois do prazo de guarda",
     "O Art. 6º, IV da Resolução COFFITO 414/2012 permite armazenar cópia "
     "digitalizada do prontuário mesmo depois de vencido o prazo legal de "
     "guarda.", R414),
    ("no atendimento domiciliar, o prontuario fica na casa do paciente",
     "O Art. 6º, V da Resolução COFFITO 414/2012 determina que, no "
     "atendimento domiciliar, o prontuário seja guardado no próprio "
     "domicílio do paciente, com orientação de sigilo à família.", R414),
    ("a copia que protege o fisioterapeuta no domiciliar",
     "O Art. 6º, VI da Resolução COFFITO 414/2012 permite ao "
     "fisioterapeuta manter cópia do prontuário no atendimento "
     "domiciliar, com assinatura atestando que a assistência foi "
     "prestada.", R414),
    ("plano terapeutico tem que dizer quantos atendimentos",
     "O Art. 1º, §1º, VI da Resolução COFFITO 414/2012 exige que o plano "
     "terapêutico traga recursos, métodos, técnicas, objetivos e a "
     "quantidade provável de atendimentos.", R414),
    ("diagnostico fisioterapeutico e item obrigatorio",
     "O Art. 1º, §1º, V da Resolução COFFITO 414/2012 lista diagnóstico e "
     "prognóstico fisioterapêuticos entre os itens do prontuário.", R414),
    ("estagiario registra, mas nao sozinho",
     "O Art. 1º, §2º da Resolução COFFITO 414/2012 exige que o registro "
     "feito em estágio traga identificação e assinatura do responsável "
     "técnico, supervisor ou preceptor, além do estagiário.", R414),
    ("dado de paciente nao e dado comum",
     "O Art. 5º, II da Lei 13.709/2018 (LGPD) classifica dado referente à "
     "saúde como dado pessoal sensível, categoria com proteção mais "
     "rigorosa que a do dado pessoal comum.", LGPD),
    ("por que planilha aberta e caderno nao servem para dado de saude",
     "Como a LGPD (Lei 13.709/2018, Art. 5º, II) trata dado de saúde como "
     "dado pessoal sensível, o cuidado com acesso e sigilo precisa ser "
     "maior do que o dispensado a um cadastro comum.", LGPD),
]

CARREIRA = [
    "autonomo ou abrir cnpj: o que muda na rotina",
    "o primeiro consultorio: o que realmente precisa no comeco",
    "atender em casa, em clinica ou nos dois",
    "quantos pacientes cabem numa semana sem adoecer",
    "a agenda do fisioterapeuta que tambem da aula",
    "quando contratar o primeiro colega",
    "dividir sala alugada: combinados que evitam briga",
    "o fisioterapeuta que faz tudo e nao cresce",
    "escolher uma especialidade ou atender de tudo",
    "o tempo invisivel entre um atendimento e outro",
    "como organizar a semana quando o volume oscila",
    "sair do plano de saude e viver de particular",
    "a conversa de reajuste com paciente antigo",
    "trabalhar sozinho sem perder a referencia tecnica",
    "o que delegar primeiro quando a agenda lota",
    "folga de verdade: ferias de quem atende sozinho",
    "o boca a boca ainda e o maior canal, e por que",
    "indicacao de medico: como construir sem depender",
    "o custo de comecar o dia sem saber quem vem",
    "quando a clinica para porque so voce sabe onde esta tudo",
]


def main():
    dados = json.load(open(ARQ, encoding="utf-8"))
    pautas = dados["pautas"]
    existentes = {p["id"] for p in pautas}

    # tudo que ja existia e gestao
    for p in pautas:
        p.setdefault("familia", "gestao")

    novas = []
    for i, (tema, fato, fonte) in enumerate(REGULACAO, 1):
        novas.append({"id": f"regulacao-{i:03d}", "eixo": "regulacao",
                      "familia": "regulacao", "tema": tema,
                      "fato": fato, "fonte": fonte, "status": "livre"})
    for i, tema in enumerate(CARREIRA, 1):
        novas.append({"id": f"carreira-{i:03d}", "eixo": "carreira",
                      "familia": "carreira", "tema": tema,
                      "status": "livre"})

    acrescentadas = [p for p in novas if p["id"] not in existentes]
    pautas.extend(acrescentadas)
    json.dump(dados, open(ARQ, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    from collections import Counter
    c = Counter(p["familia"] for p in pautas)
    print(f"{len(acrescentadas)} pautas novas. Banco com {len(pautas)}.")
    for fam, n in sorted(c.items()):
        livres = sum(1 for p in pautas
                     if p["familia"] == fam and p.get("status") == "livre")
        print(f"  {fam:10} {n:3} no total, {livres:3} livres")


if __name__ == "__main__":
    main()
