#!/usr/bin/env python3
"""
Gera a fila de Reels: um roteiro por fato CONFERIDO em fonte oficial.

Cada roteiro e escrito aqui a mao, nao por IA na hora de publicar. A IA
nao inventa conteudo de saude: ela so empresta a voz.

A narracao e dividida em 4 partes (pergunta, resposta, extra, fecho) e
o tempo de cada bloco na tela sai do tamanho de cada parte: cada bloco
fica no ar o tanto que a voz leva para falar dele.

Fontes conferidas em 02/11/2026:
  - coffito.gov.br, pagina de especialidades
  - Resolucoes COFFITO 219/2000, 220/2001, 337/2007, 401/2011, 402/2011
    e 414/2012 (texto em normasbrasil.com.br / normaslegais.com.br)
  - Lei 13.709/2018 (LGPD), Art. 5, II
  - Senado (Radio Senado): 13 de outubro e o Decreto-Lei de 1969

Uso: python3 reels/gerar_fila.py   -> grava reels/fila/NN-*.json
"""

import json
import os
import re
import unicodedata

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fila")

CTA_LEGENDA = ("Teste a FisioSync grátis por 7 dias: app.fisiosync.com.br\n"
               "Disponível no Google Play e na App Store.")

# Envio por DM e o sinal que o Instagram mais valoriza para mostrar um
# Reels a quem ainda nao segue a conta. O convite e natural para quem
# fala com colegas de profissao.
CONVITE_ENVIO = "Conhece um fisio que precisa ver isso? Manda pra ele."

# Hashtags proprias sempre na frente. O limite do Instagram e 5 por post
# desde dez/2025, e hashtag nao da alcance; a serie existe para agrupar
# os videos e ser o lugar onde quem gostou acha os outros.
HASHTAGS_PROPRIAS = ["#FisioSync", "#FisioSyncExplica"]

R414 = "Resolução COFFITO nº 414/2012"

ROTEIROS = [
    {
        "titulo": "As 16 especialidades da fisioterapia",
        "partes": ["Quantas especialidades a fisioterapia tem?",
                   "Pelo COFFITO, dezesseis. Da acupuntura à terapia intensiva.",
                   "Seja qual for a sua, agenda e prontuário num lugar só.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Quantas", "especialidades a", "fisioterapia tem?"],
        "resposta": {"destaque": "16", "complemento": "especialidades reconhecidas",
                     "fonte": "COFFITO, página oficial de especialidades"},
        "extra": {"titulo": "Qual é a sua?", "texto": "Agenda e prontuário\nnum lugar só."},
        "fato": ("O COFFITO reconhece 16 especialidades: Acupuntura, Aquática, Cardiovascular, "
                 "Dermatofuncional, Esportiva, Gerontologia, Trabalho, Neurofuncional, Oncologia, "
                 "Reumatologia, Respiratória, Traumato-Ortopédica, Osteopatia, Quiropraxia, "
                 "Saúde da Mulher e Terapia Intensiva."),
        "fonte": "COFFITO, página de especialidades (coffito.gov.br)",
        "legenda": [
            "A fisioterapia tem 16 especialidades reconhecidas pelo COFFITO:",
            "Acupuntura, Aquática, Cardiovascular, Dermatofuncional, Esportiva, Gerontologia, "
            "Trabalho, Neurofuncional, Oncologia, Reumatologia, Respiratória, "
            "Traumato-Ortopédica, Osteopatia, Quiropraxia, Saúde da Mulher e Terapia Intensiva.",
            "Qual é a sua? Conta aqui nos comentários.",
        ],
        "tags": "#FisioSync #fisioterapia #coffito #especialidades",
    },
    {
        "titulo": "Os oito itens do prontuario",
        "partes": ["Quantos itens o prontuário precisa ter?",
                   "Pelo COFFITO, oito. Da identificação do paciente à do profissional.",
                   "No digital, fica tudo num lugar só.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Quantos itens", "o prontuário", "precisa ter?"],
        "resposta": {"destaque": "8", "complemento": "itens obrigatórios",
                     "fonte": f"{R414}, Art. 1º, §1º"},
        "extra": {"titulo": "Do começo ao fim", "texto": "Da identificação\ndo paciente à\ndo profissional."},
        "fato": ("O Art. 1º, §1º da Resolução COFFITO 414/2012 lista oito itens: identificação do "
                 "paciente; história clínica; exame clínico/físico; exames complementares; "
                 "diagnóstico e prognóstico fisioterapêuticos; plano terapêutico; evolução; e "
                 "identificação do profissional."),
        "fonte": R414,
        "legenda": [
            "O prontuário fisioterapêutico tem oito itens obrigatórios (Resolução COFFITO nº "
            "414/2012, Art. 1º, §1º):",
            "1. Identificação do paciente\n2. História clínica\n3. Exame clínico/físico\n"
            "4. Exames complementares\n5. Diagnóstico e prognóstico fisioterapêuticos\n"
            "6. Plano terapêutico\n7. Evolução\n8. Identificação do profissional",
            "Qual deles mais fica para trás na correria? Conta aqui.",
        ],
        "tags": "#FisioSync #fisioterapia #prontuario #coffito",
    },
    {
        "titulo": "Quiropraxia e osteopatia sao especialidades",
        "partes": ["Quiropraxia e osteopatia são especialidades da fisioterapia?",
                   "Sim. O COFFITO reconhece as duas desde 2001.",
                   "Mas só se anuncia especialista com o título registrado.",
                   "Organize a clínica com a FisioSync."],
        "pergunta": ["Quiropraxia e", "osteopatia são", "especialidades?"],
        "resposta": {"destaque": "2001", "complemento": "as duas reconhecidas pelo COFFITO",
                     "fonte": "Resolução COFFITO nº 220/2001"},
        "extra": {"titulo": "Atenção", "texto": "Especialista só\ncom título registrado."},
        "fato": ("A Resolução COFFITO nº 220, de 23/05/2001, reconhece a Quiropraxia e a Osteopatia "
                 "como especialidades do fisioterapeuta (Art. 1º). Pelo Art. 5º, o profissional só "
                 "se anuncia especialista após registrar o título no COFFITO."),
        "fonte": "Resolução COFFITO nº 220/2001",
        "legenda": [
            "Quiropraxia e osteopatia são reconhecidas pelo COFFITO como especialidades do "
            "fisioterapeuta desde 2001 (Resolução COFFITO nº 220/2001, Art. 1º).",
            "E um detalhe que muita gente pula: pelo Art. 5º, só se anuncia como especialista "
            "depois de registrar o título no COFFITO.",
            "Você atua com alguma das duas? Conta aqui nos comentários.",
        ],
        "tags": "#FisioSync #quiropraxia #osteopatia #fisioterapia #coffito",
    },
    {
        "titulo": "Dado de saude e dado sensivel",
        "partes": ["Dado de paciente é dado comum?",
                   "Não. Pela LGPD, dado de saúde é dado sensível.",
                   "Caderno aberto e planilha solta não combinam com isso.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Dado de", "paciente é", "dado comum?"],
        "resposta": {"destaque": "Sensível", "complemento": "dado de saúde, pela LGPD",
                     "fonte": "Lei nº 13.709/2018, Art. 5º, II"},
        "extra": {"titulo": "Na prática", "texto": "Caderno aberto e\nplanilha solta\nnão combinam."},
        "fato": ("O Art. 5º, II da Lei 13.709/2018 (LGPD) classifica dado referente à saúde, "
                 "vinculado a uma pessoa natural, como dado pessoal sensível."),
        "fonte": "Lei nº 13.709/2018 (LGPD)",
        "legenda": [
            "Pela LGPD (Lei nº 13.709/2018, Art. 5º, II), dado referente à saúde é dado pessoal "
            "sensível, com proteção mais rigorosa que a de um cadastro comum.",
            "Ficha em gaveta aberta, planilha compartilhada sem controle, foto de prontuário no "
            "WhatsApp: tudo isso é dado sensível circulando.",
            "Como você guarda os dados dos seus pacientes hoje? Conta aqui.",
        ],
        "tags": "#FisioSync #lgpd #fisioterapia #gestaodeclinica",
    },
    {
        "titulo": "Fisioterapeuta pode fazer acupuntura",
        "partes": ["Fisioterapeuta pode fazer acupuntura?",
                   "Pode. O COFFITO reconhece como especialidade desde 2000.",
                   "Sem exclusividade para a fisioterapia.",
                   "Organize a clínica com a FisioSync."],
        "pergunta": ["Fisioterapeuta", "pode fazer", "acupuntura?"],
        "resposta": {"destaque": "2000", "complemento": "acupuntura reconhecida como especialidade",
                     "fonte": "Resolução COFFITO nº 219/2000"},
        "extra": {"titulo": "Detalhe", "texto": "Sem exclusividade\ncorporativa."},
        "fato": ("A Resolução COFFITO nº 219, de 14/12/2000, Art. 1º: 'Sem caráter de exclusividade "
                 "corporativa, reconhecer a Acupuntura como especialidade do profissional "
                 "Fisioterapeuta'. Pelo Art. 2º, a condição de especialista é anotada na carteira "
                 "de identidade profissional."),
        "fonte": "Resolução COFFITO nº 219/2000",
        "legenda": [
            "Sim: a Resolução COFFITO nº 219/2000 reconhece a Acupuntura como especialidade do "
            "fisioterapeuta, \"sem caráter de exclusividade corporativa\" (Art. 1º).",
            "Ou seja, a resolução não reserva a técnica só para a fisioterapia. E a condição de "
            "especialista é anotada na carteira profissional (Art. 2º).",
            "Você usa acupuntura nos seus atendimentos? Conta aqui.",
        ],
        "tags": "#FisioSync #acupuntura #fisioterapia #coffito",
    },
    {
        "titulo": "De quem e o prontuario",
        "partes": ["De quem é o prontuário?",
                   "Do paciente. E ele pode pedir cópia.",
                   "No prontuário digital, tudo fica fácil de achar.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["De quem", "é o", "prontuário?"],
        "resposta": {"destaque": "Do paciente", "complemento": "e ele pode pedir cópia",
                     "fonte": R414},
        "extra": {"titulo": "Quando ele pedir", "texto": "No digital, tudo\nfica fácil de achar."},
        "fato": ("Pela Resolução COFFITO 414/2012, o prontuário pertence ao cliente/paciente, deve "
                 "permanecer disponível para acesso dele ou de seu representante, que pode receber "
                 "cópias autênticas, e é vedado negar esse acesso, salvo risco ao paciente ou a "
                 "terceiros."),
        "fonte": R414,
        "legenda": [
            "O prontuário é do paciente, não da clínica (Resolução COFFITO nº 414/2012).",
            "Ele, ou o representante dele, pode pedir acesso e cópias autênticas. Negar esse "
            "acesso é vedado, salvo quando gerar risco ao paciente ou a terceiros.",
            "Já te pediram cópia do prontuário? Conta como foi.",
        ],
        "tags": "#FisioSync #prontuario #fisioterapia #coffito",
    },
    {
        "titulo": "Fisioterapia esportiva e exclusiva",
        "partes": ["Fisioterapia esportiva é exclusiva do fisioterapeuta?",
                   "É. O COFFITO reconheceu em 2007, de exercício exclusivo.",
                   "Diferente da acupuntura, que não tem exclusividade.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Fisioterapia", "esportiva é", "exclusiva?"],
        "resposta": {"destaque": "2007", "complemento": "especialidade própria e exclusiva",
                     "fonte": "Resolução COFFITO nº 337/2007"},
        "extra": {"titulo": "Diferente da acupuntura", "texto": "que é reconhecida\nsem exclusividade."},
        "fato": ("A Resolução COFFITO nº 337, de 08/11/2007, Art. 1º, reconhece a Fisioterapia "
                 "Esportiva 'como própria e de exercício exclusivo por Fisioterapeutas'. A "
                 "Resolução 219/2000 reconhece a Acupuntura 'sem caráter de exclusividade "
                 "corporativa'."),
        "fonte": "Resoluções COFFITO nº 337/2007 e nº 219/2000",
        "legenda": [
            "A Fisioterapia Esportiva foi reconhecida pelo COFFITO em 2007 como especialidade "
            "\"própria e de exercício exclusivo por Fisioterapeutas\" (Resolução nº 337/2007).",
            "Repara na diferença: a Acupuntura foi reconhecida \"sem caráter de exclusividade "
            "corporativa\" (Resolução nº 219/2000).",
            "Você atende atleta? De qual modalidade? Conta aqui.",
        ],
        "tags": "#FisioSync #fisioterapiaesportiva #fisioterapia #coffito",
    },
    {
        "titulo": "Prontuario eletronico vale",
        "partes": ["Prontuário eletrônico vale?",
                   "Vale. O COFFITO aceita manuscrito ou eletrônico.",
                   "No eletrônico, nome e CREFITO depois de cada registro.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Prontuário", "eletrônico", "vale?"],
        "resposta": {"destaque": "Vale", "complemento": "manuscrito ou eletrônico",
                     "fonte": f"{R414}, Art. 2º"},
        "extra": {"titulo": "Mas atenção", "texto": "Nome completo e\nnº do CREFITO\napós cada registro."},
        "fato": ("A Resolução COFFITO 414/2012, Art. 2º, permite o registro manuscrito ou eletrônico. "
                 "No eletrônico, o parágrafo único exige nome completo e número de registro no "
                 "CREFITO logo após cada registro."),
        "fonte": R414,
        "legenda": [
            "Prontuário eletrônico vale, sim: a Resolução COFFITO nº 414/2012 (Art. 2º) aceita "
            "registro manuscrito ou eletrônico.",
            "Mas tem uma regra: no eletrônico, nome completo e número do CREFITO logo após cada "
            "registro (parágrafo único).",
            "Seu prontuário ainda é de papel ou já é digital? Conta aqui.",
        ],
        "tags": "#FisioSync #prontuarioeletronico #fisioterapia #coffito",
    },
    {
        "titulo": "As cinco areas da saude da mulher",
        "partes": ["Quantas áreas tem a fisioterapia na saúde da mulher?",
                   "Cinco, pela resolução do COFFITO de 2011.",
                   "Da obstetrícia à mastologia.",
                   "Organize os atendimentos com a FisioSync."],
        "pergunta": ["Fisioterapia na", "saúde da mulher:", "quantas áreas?"],
        "resposta": {"destaque": "5", "complemento": "áreas de atuação",
                     "fonte": "Resolução COFFITO nº 401/2011, Art. 5º"},
        "extra": {"titulo": "Quais?", "texto": "Da obstetrícia\nà mastologia."},
        "fato": ("A Resolução COFFITO nº 401/2011, Art. 5º, define as áreas de atuação da "
                 "Fisioterapia na Saúde da Mulher: uroginecologia e coloproctologia, ginecologia, "
                 "obstetrícia, disfunções sexuais femininas e mastologia."),
        "fonte": "Resolução COFFITO nº 401/2011",
        "legenda": [
            "A Fisioterapia na Saúde da Mulher tem cinco áreas de atuação (Resolução COFFITO nº "
            "401/2011, Art. 5º):",
            "1. Uroginecologia e coloproctologia\n2. Ginecologia\n3. Obstetrícia\n"
            "4. Disfunções sexuais femininas\n5. Mastologia",
            "Em qual delas você atua? Conta aqui nos comentários.",
        ],
        "tags": "#FisioSync #saudedamulher #fisioterapiapelvica #fisioterapia",
    },
    {
        "titulo": "Prontuario no atendimento domiciliar",
        "partes": ["No atendimento domiciliar, onde fica o prontuário?",
                   "Na casa do paciente, com orientação de sigilo à família.",
                   "E você pode guardar uma cópia para se proteger.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Atendimento", "domiciliar: onde fica", "o prontuário?"],
        "resposta": {"destaque": "Na casa", "complemento": "do paciente, com sigilo",
                     "fonte": f"{R414}, Art. 6º, V"},
        "extra": {"titulo": "E você", "texto": "pode guardar\numa cópia para\nse proteger."},
        "fato": ("Resolução COFFITO 414/2012, Art. 6º, V: no atendimento domiciliar, o prontuário "
                 "é guardado no domicílio do paciente, com orientação de sigilo ao núcleo familiar. "
                 "Art. 6º, VI: o fisioterapeuta pode manter cópia, com assinatura atestando que a "
                 "assistência foi prestada."),
        "fonte": R414,
        "legenda": [
            "No atendimento domiciliar, o prontuário fica na casa do paciente, e o fisioterapeuta "
            "orienta a família a manter sigilo (Resolução COFFITO nº 414/2012, Art. 6º, V).",
            "E, para se proteger, você pode manter uma cópia, com a assinatura do paciente ou do "
            "responsável atestando o atendimento (Art. 6º, VI).",
            "Você atende em domicílio? Como organiza isso? Conta aqui.",
        ],
        "tags": "#FisioSync #fisioterapiadomiciliar #homecare #fisioterapia",
    },
    {
        "titulo": "Terapia intensiva e suas tres areas",
        "partes": ["Fisioterapia em terapia intensiva é especialidade?",
                   "É. O COFFITO disciplinou em 2011.",
                   "Em três áreas: neonatal, pediátrica e adulta.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Terapia", "intensiva é", "especialidade?"],
        "resposta": {"destaque": "3", "complemento": "áreas: neonatologia, pediatria e adulto",
                     "fonte": "Resolução COFFITO nº 402/2011"},
        "extra": {"titulo": "Três áreas", "texto": "Neonatal,\npediátrica\ne adulta."},
        "fato": ("A Resolução COFFITO nº 402/2011 disciplina a especialidade de Fisioterapia em "
                 "Terapia Intensiva; o Art. 5º prevê as áreas de neonatologia, pediatria e adulto."),
        "fonte": "Resolução COFFITO nº 402/2011",
        "legenda": [
            "Fisioterapia em Terapia Intensiva é especialidade disciplinada pelo COFFITO desde "
            "2011 (Resolução nº 402/2011).",
            "E tem três áreas de atuação: neonatologia, pediatria e adulto (Art. 5º).",
            "Você já trabalhou em UTI? Em qual área? Conta aqui.",
        ],
        "tags": "#FisioSync #terapiaintensiva #fisioterapia #coffito",
    },
    {
        "titulo": "Estagiario e o prontuario",
        "partes": ["Estagiário pode registrar no prontuário?",
                   "Pode, mas com a assinatura do supervisor junto.",
                   "Identificação dos dois, sempre.",
                   "Organize a clínica com a FisioSync."],
        "pergunta": ["Estagiário", "pode registrar no", "prontuário?"],
        "resposta": {"destaque": "Pode", "complemento": "com a assinatura do supervisor",
                     "fonte": f"{R414}, Art. 1º, §2º"},
        "extra": {"titulo": "Sempre", "texto": "Identificação\ndos dois."},
        "fato": ("Resolução COFFITO 414/2012, Art. 1º, §2º: o registro feito em estágio deve trazer "
                 "a identificação e a assinatura do responsável técnico, supervisor ou preceptor, "
                 "além do estagiário."),
        "fonte": R414,
        "legenda": [
            "Estagiário registra no prontuário, mas não sozinho: o registro precisa trazer "
            "identificação e assinatura do supervisor, preceptor ou responsável técnico, além do "
            "estagiário (Resolução COFFITO nº 414/2012, Art. 1º, §2º).",
            "Na sua clínica tem estagiário? Marca aqui quem supervisiona.",
        ],
        "tags": "#FisioSync #fisioterapia #estagio #coffito",
    },
    {
        "titulo": "Por que 13 de outubro",
        "partes": ["Por que treze de outubro é o Dia do Fisioterapeuta?",
                   "É a data do decreto que regulamentou a profissão.",
                   "Mais de cinquenta anos depois, a clínica pode ser digital.",
                   "Teste a FisioSync."],
        "pergunta": ["Por que 13 de", "outubro é o Dia do", "Fisioterapeuta?"],
        "resposta": {"destaque": "1969", "complemento": "o decreto-lei regulamenta a profissão",
                     "fonte": "Decreto-Lei nº 938, de 13/10/1969"},
        "extra": {"titulo": "Mais de 50 anos", "texto": "e a clínica\npode ser digital."},
        "fato": ("O 13 de outubro marca a publicação, em 13/10/1969, do decreto-lei que regulamenta "
                 "a fisioterapia e a terapia ocupacional no Brasil (Decreto-Lei nº 938/1969). Desde "
                 "2015 a data é o Dia Nacional desses profissionais (Rádio Senado)."),
        "fonte": "Decreto-Lei nº 938/1969; Rádio Senado",
        "legenda": [
            "O Dia do Fisioterapeuta é 13 de outubro por um motivo: em 13 de outubro de 1969 foi "
            "publicado o decreto-lei que regulamentou a profissão (Decreto-Lei nº 938/1969).",
            "Desde 2015, a data é o Dia Nacional do Fisioterapeuta e do Terapeuta Ocupacional.",
            "Há quanto tempo você é fisio? Conta aqui.",
        ],
        "tags": "#FisioSync #fisioterapia #diadofisioterapeuta #coffito",
    },
    {
        "titulo": "O plano terapeutico e o numero de sessoes",
        "partes": ["O plano terapêutico precisa dizer quantas sessões?",
                   "Precisa. O COFFITO pede a quantidade provável de atendimentos.",
                   "Além de objetivos, recursos e técnicas.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O plano precisa", "dizer quantas", "sessões?"],
        "resposta": {"destaque": "Sim", "complemento": "a quantidade provável de atendimentos",
                     "fonte": f"{R414}, Art. 1º, §1º, VI"},
        "extra": {"titulo": "E também", "texto": "objetivos,\nrecursos e\ntécnicas."},
        "fato": ("Resolução COFFITO 414/2012, Art. 1º, §1º, VI: o plano terapêutico traz recursos, "
                 "métodos, técnicas, objetivos e a quantidade provável de atendimentos."),
        "fonte": R414,
        "legenda": [
            "O plano terapêutico precisa trazer a quantidade provável de atendimentos, além de "
            "recursos, métodos, técnicas e objetivos (Resolução COFFITO nº 414/2012, Art. 1º, "
            "§1º, VI).",
            "Você já combina o número de sessões com o paciente logo no início? Conta aqui.",
        ],
        "tags": "#FisioSync #fisioterapia #planoterapeutico #coffito",
    },
]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40]


def main():
    os.makedirs(PASTA, exist_ok=True)
    for i, r in enumerate(ROTEIROS, 1):
        partes = r["partes"]
        tamanhos = [len(p) for p in partes[:3]]
        corpo = sum(tamanhos)
        proporcoes = [round(tamanhos[0] / corpo, 3), round(tamanhos[1] / corpo, 3)]
        narracao = " ".join(partes)
        palavras = len(narracao.split())
        if palavras > 34:
            raise SystemExit(f"{r['titulo']}: {palavras} palavras, passa de 15s.")
        tematicas = [t for t in r["tags"].split()
                     if t.lower() not in {h.lower() for h in HASHTAGS_PROPRIAS}]
        tags = " ".join((HASHTAGS_PROPRIAS + tematicas)[:5])
        legenda = "\n\n".join(r["legenda"] + [CONVITE_ENVIO, CTA_LEGENDA, tags])
        if len(legenda) > 2200:
            raise SystemExit(f"{r['titulo']}: legenda com {len(legenda)} caracteres.")
        if not 3 <= tags.count("#") <= 5 or "#FisioSyncExplica" not in tags:
            raise SystemExit(f"{r['titulo']}: hashtags fora da regra (3 a 5, com as proprias).")
        dados = {
            "tipo": "dica",
            "titulo": r["titulo"],
            "narracao": narracao,
            "palavras": palavras,
            "fato": r["fato"],
            "fonte": r["fonte"],
            "conferido_em": "2026-11-02",
            "proporcoes": proporcoes,
            "pergunta": {"rotulo": "Você sabia?", "linhas": r["pergunta"]},
            "resposta": r["resposta"],
            "extra": r["extra"],
            "fecho": {"chamada": "Teste grátis por 7 dias", "site": "app.fisiosync.com.br"},
            "capa_ms": 3800,
            "legenda": legenda,
        }
        nome = f"{i:02d}-{slug(r['titulo'])}.json"
        with open(os.path.join(PASTA, nome), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"{nome:58} {palavras:2} palavras  legenda {len(legenda):4}")


if __name__ == "__main__":
    main()
