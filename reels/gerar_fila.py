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
    {
        "interesse": "alto",
        "titulo": "Dez segundos num pe so",
        "partes": [
            "Seu paciente aguenta dez segundos num pé só?",
            "Estudo brasileiro: quem não aguentou teve oitenta e quatro por cento mais risco de morte.",
            "Anote na avaliação.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Seu paciente aguenta",
            "10 segundos",
            "num pé só?"
        ],
        "resposta": {
            "destaque": "84%",
            "complemento": "mais risco de morte em quem não aguentou",
            "fonte": "Araujo et al., BJSM, 2022"
        },
        "extra": {
            "titulo": "Estudo brasileiro",
            "texto": "1.702 pessoas\nde 51 a 75 anos"
        },
        "fato": "Estudo de coorte de pesquisadores da CLINIMEX (Rio de Janeiro) avaliou 1.702 pessoas de 51 a 75 anos (68% homens) entre 2008 e 2020, e 20,4% não conseguiram ficar 10 segundos apoiadas em um pé só. Em mediana de 7 anos, morreram 17,5% desse grupo contra 4,6% de quem conseguiu; ajustado por idade, sexo, IMC e comorbidades, o risco de morte por qualquer causa foi 84% maior (HR 1,84; IC95% 1,23–2,78).",
        "fonte": "Araujo et al., British Journal of Sports Medicine, 2022 (coorte)",
        "legenda": [
            "Pesquisadores da CLINIMEX (Rio de Janeiro) acompanharam 1.702 pessoas de 51 a 75 anos. 20,4% não conseguiram ficar 10 segundos apoiadas em um pé só (Araujo et al., British Journal of Sports Medicine, 2022).",
            "Em cerca de 7 anos, morreram 17,5% de quem não conseguiu, contra 4,6% de quem conseguiu. Ajustado por idade, sexo, IMC e outras doenças, o risco de morte foi 84% maior.",
            "É uma associação: o estudo não prova que treinar equilíbrio aumenta a sobrevida.",
            "Você já usa esse teste na avaliação?"
        ],
        "tags": "#equilibrio #avaliacao #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "Disco degenerado sem dor",
        "partes": [
            "Disco degenerado na ressonância explica a dor?",
            "Sem dor nenhuma, trinta e sete por cento já têm aos vinte anos.",
            "Aos oitenta, noventa e seis.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Disco degenerado",
            "na ressonância",
            "explica a dor?"
        ],
        "resposta": {
            "destaque": "96%",
            "complemento": "dos 80 anos sem dor têm degeneração",
            "fonte": "Brinjikji et al., AJNR, 2015"
        },
        "extra": {
            "titulo": "Aos 20 anos",
            "texto": "37% já têm,\nmesmo sem dor."
        },
        "fato": "Revisão sistemática com 33 estudos e 3.110 pessoas sem sintomas encontrou degeneração discal em exames de imagem em 37% dos indivíduos de 20 anos e em 96% dos de 80 anos. Na mesma comparação entre 20 e 80 anos, o abaulamento discal passou de 30% para 84%, a protrusão discal de 29% para 43% e a fissura anular de 19% para 29%.",
        "fonte": "Brinjikji et al., American Journal of Neuroradiology, 2015 (revisão sistemática)",
        "legenda": [
            "Uma revisão sistemática com 33 estudos e 3.110 pessoas SEM dor (Brinjikji et al., American Journal of Neuroradiology, 2015) encontrou degeneração discal na imagem em 37% dos indivíduos de 20 anos e em 96% dos de 80 anos.",
            "Entre 20 e 80 anos, o abaulamento discal passou de 30% para 84%, e a protrusão discal de 29% para 43%.",
            "Ou seja: esses achados são comuns em quem não sente dor, e aumentam com a idade.",
            "Você mostra esse dado para os seus pacientes?"
        ],
        "tags": "#coluna #dorlombar #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "Forca de preensao e mortalidade",
        "partes": [
            "Força de preensão prevê mortalidade?",
            "Cada cinco quilos a menos, dezesseis por cento mais risco de morte.",
            "E previu melhor que a pressão sistólica.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Força de",
            "preensão prevê",
            "mortalidade?"
        ],
        "resposta": {
            "destaque": "16%",
            "complemento": "mais risco a cada 5 kg a menos",
            "fonte": "Leong et al., The Lancet, 2015"
        },
        "extra": {
            "titulo": "Melhor que",
            "texto": "a pressão sistólica\ncomo preditor."
        },
        "fato": "No estudo PURE, com 139.691 adultos de 17 países acompanhados por mediana de 4 anos, cada 5 kg a menos de força de preensão manual se associou a risco 16% maior de morte por qualquer causa (HR 1,16; IC95% 1,13–1,20). A força de preensão foi preditora mais forte de mortalidade geral e cardiovascular do que a pressão arterial sistólica.",
        "fonte": "Leong et al., The Lancet, 2015 (estudo de coorte prospectivo PURE)",
        "legenda": [
            "No estudo PURE (Leong et al., The Lancet, 2015), 139.691 adultos de 17 países foram acompanhados por cerca de 4 anos. Cada 5 kg a menos de força de preensão se associou a risco 16% maior de morte por qualquer causa.",
            "A força de preensão foi preditora mais forte de mortalidade geral e cardiovascular do que a pressão arterial sistólica.",
            "É associação, de um estudo observacional: não quer dizer que treinar a preensão reduz a mortalidade.",
            "Você mede a preensão na avaliação?"
        ],
        "tags": "#forca #avaliacao #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "Alongamento e lesao esportiva",
        "partes": [
            "Alongar previne lesão esportiva?",
            "Em vinte e cinco ensaios, alongamento não mostrou benefício.",
            "Treino de força reduziu as lesões a menos de um terço.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Alongar previne",
            "lesão",
            "esportiva?"
        ],
        "resposta": {
            "destaque": "1/3",
            "complemento": "força reduziu lesões a menos de 1/3",
            "fonte": "Lauersen et al., BJSM, 2014"
        },
        "extra": {
            "titulo": "E o alongamento?",
            "texto": "Sem efeito\nna prevenção."
        },
        "fato": "Metanálise de 25 ensaios randomizados (26.610 participantes, 3.464 lesões) não encontrou efeito benéfico do alongamento na prevenção de lesões esportivas (RR 0,963; IC95% 0,846–1,095). O treino de força teve o maior efeito (RR 0,315; IC95% 0,207–0,480), seguido do treino proprioceptivo (RR 0,550; IC95% 0,347–0,869); segundo os autores, o treino de força reduziu as lesões esportivas a menos de 1/3 e as lesões por sobrecarga poderiam ser quase reduzidas à metade.",
        "fonte": "Lauersen et al., British Journal of Sports Medicine, 2014 (revisão sistemática e metanálise)",
        "legenda": [
            "Metanálise com 25 ensaios randomizados e 26.610 participantes (Lauersen et al., British Journal of Sports Medicine, 2014) não encontrou efeito benéfico do alongamento na prevenção de lesões esportivas.",
            "O treino de força teve o maior efeito: segundo os autores, reduziu as lesões esportivas a menos de 1/3. O treino proprioceptivo veio em seguida.",
            "O estudo avaliou prevenção de lesões. Não fala de flexibilidade nem de desempenho.",
            "No seu atendimento, força ou alongamento vem primeiro?"
        ],
        "tags": "#prevencaodelesoes #fisioesportiva #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "O nordico e os isquiotibiais",
        "partes": [
            "Qual exercício corta pela metade lesão de isquiotibiais?",
            "O nórdico: no programa, reduziu o risco em até cinquenta e um por cento.",
            "Quinze estudos.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Qual exercício",
            "corta pela metade",
            "lesão de isquiotibiais?"
        ],
        "resposta": {
            "destaque": "51%",
            "complemento": "menos risco com o nórdico no programa",
            "fonte": "van Dyk et al., BJSM, 2019"
        },
        "extra": {
            "titulo": "8.459 atletas",
            "texto": "15 estudos\nna metanálise."
        },
        "fato": "Revisão sistemática com metanálise de 15 estudos (8.459 atletas) comparou programas de prevenção com e sem o exercício nórdico para isquiotibiais: incluir o nórdico reduziu o risco de lesão de isquiotibiais em até 51% (razão de risco 0,49; IC95% 0,32–0,74). Considerando só os 8 ensaios randomizados, a razão de risco foi 0,52 (IC95% 0,32–0,85), e os autores concluem que o exercício nórdico 'essencialmente reduz pela metade' a taxa dessas lesões.",
        "fonte": "van Dyk et al., British Journal of Sports Medicine, 2019 (revisão sistemática e metanálise)",
        "legenda": [
            "Revisão sistemática com metanálise de 15 estudos e 8.459 atletas (van Dyk et al., British Journal of Sports Medicine, 2019) comparou programas de prevenção com e sem o exercício nórdico.",
            "Incluir o nórdico reduziu o risco de lesão de isquiotibiais em até 51%. Nos 8 ensaios randomizados, a redução também ficou perto da metade.",
            "O resultado vale para lesão de isquiotibiais, não para lesões em geral.",
            "O nórdico já está nos seus programas de prevenção?"
        ],
        "tags": "#isquiotibiais #fisioesportiva #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "Exercicio e quedas em idosos",
        "partes": [
            "Exercício reduz quedas em idosos?",
            "Pela Cochrane, reduz a taxa de quedas em vinte e três por cento.",
            "Combinando tipos, provavelmente trinta e quatro.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Exercício",
            "reduz quedas",
            "em idosos?"
        ],
        "resposta": {
            "destaque": "23%",
            "complemento": "menos quedas com exercício",
            "fonte": "Sherrington et al., Cochrane, 2019"
        },
        "extra": {
            "titulo": "Combinando tipos",
            "texto": "provavelmente 34%\n(certeza moderada)"
        },
        "fato": "Revisão Cochrane de 108 ensaios randomizados (23.407 participantes de 25 países, com 60 anos ou mais e vivendo na comunidade; média de 76 anos, 77% mulheres) concluiu que o exercício reduz a taxa de quedas em 23% (razão de taxas 0,77; IC95% 0,71–0,83; certeza alta) e o número de pessoas que caem ao menos uma vez em 15% (RR 0,85; IC95% 0,81–0,89). Exercícios de equilíbrio e funcionais reduzem a taxa de quedas em 24%, a combinação de tipos (em geral equilíbrio e funcionais mais resistidos) provavelmente reduz em 34% e o Tai Chi pode reduzir em 19%.",
        "fonte": "Sherrington et al., Cochrane Database of Systematic Reviews, 2019 (revisão sistemática Cochrane)",
        "legenda": [
            "Revisão Cochrane com 108 ensaios e 23.407 pessoas com 60 anos ou mais vivendo na comunidade (Sherrington et al., 2019): o exercício reduz a taxa de quedas em 23%, com certeza alta.",
            "Exercícios de equilíbrio e funcionais reduzem a taxa em 24%. A combinação de tipos, em geral equilíbrio e funcionais com resistidos, provavelmente reduz em 34%. O Tai Chi pode reduzir em 19%.",
            "Que tipo de exercício você usa com seus pacientes idosos?"
        ],
        "tags": "#idosos #quedas #fisioterapia"
    },
    {
        "interesse": "alto",
        "titulo": "Pilates ja foi marca registrada",
        "partes": [
            "Você sabia que Pilates já foi marca registrada?",
            "Em dois mil, a Justiça americana anulou a marca.",
            "Virou o nome genérico do método.",
            "Teste a FisioSync grátis."
        ],
        "pergunta": [
            "Pilates já foi",
            "marca",
            "registrada?"
        ],
        "resposta": {
            "destaque": "2000",
            "complemento": "a Justiça dos EUA anulou a marca",
            "fonte": "Pilates, Inc. v. Current Concepts, 2000"
        },
        "extra": {
            "titulo": "Desde então",
            "texto": "instrutores e fabricantes\npodem usar o nome."
        },
        "fato": "Em 19 de outubro de 2000, no caso Pilates, Inc. v. Current Concepts, Inc., a juíza Miriam Cedarbaum, do Tribunal Distrital dos EUA para o Distrito Sul de Nova York, considerou 'Pilates' o nome genérico de um método de exercício, invalidou as marcas registradas da palavra e mandou o escritório de marcas e patentes dos EUA (USPTO) cancelá-las. Com isso, nos EUA, instrutores e fabricantes passaram a poder usar o termo para descrever aulas e equipamentos.",
        "fonte": "Pilates, Inc. v. Current Concepts, Inc., 120 F. Supp. 2d 286, S.D.N.Y., 2000 (decisão judicial)",
        "legenda": [
            "Em 19 de outubro de 2000, no caso Pilates, Inc. v. Current Concepts, Inc., um tribunal federal de Nova York considerou 'Pilates' o nome genérico de um método de exercício e mandou cancelar as marcas registradas da palavra.",
            "Com isso, nos EUA, instrutores e fabricantes passaram a poder usar o termo para descrever aulas e equipamentos.",
            "A decisão vale para os Estados Unidos.",
            "Você conhecia essa história?"
        ],
        "tags": "#pilates #historia #studiodepilates"
    },
    {
        "interesse": "alto",
        "titulo": "Problema cronico de coluna no Brasil",
        "partes": [
            "Quantos brasileiros têm problema crônico de coluna?",
            "Pela PNS, vinte e um vírgula seis por cento dos adultos relatam.",
            "É muita gente pra atender.",
            "Organize a agenda com a FisioSync."
        ],
        "pergunta": [
            "Quantos brasileiros",
            "têm problema",
            "crônico de coluna?"
        ],
        "resposta": {
            "destaque": "21,6%",
            "complemento": "dos adultos relatam o problema",
            "fonte": "PNS 2019 (IBGE); Malta et al., 2022"
        },
        "extra": {
            "titulo": "Nas mulheres",
            "texto": "24,5%.\nNos homens, 18,3%."
        },
        "fato": "Na Pesquisa Nacional de Saúde 2019 (IBGE e Ministério da Saúde), 21,6% dos brasileiros de 18 anos ou mais relataram problema crônico de coluna, cerca de 34,3 milhões de pessoas. A prevalência foi de 24,5% nas mulheres e 18,3% nos homens, e subiu de 9,3% na faixa de 18 a 24 anos para 31,3% tanto entre 55 e 64 anos quanto a partir dos 65.",
        "fonte": "Malta et al., Revista Brasileira de Epidemiologia, 2022 (dados da PNS 2019/IBGE)",
        "legenda": [
            "Na Pesquisa Nacional de Saúde 2019 (IBGE e Ministério da Saúde), 21,6% dos brasileiros com 18 anos ou mais relataram problema crônico de coluna (Malta et al., Revista Brasileira de Epidemiologia, 2022).",
            "Foram 24,5% nas mulheres e 18,3% nos homens. Na faixa de 18 a 24 anos eram 9,3%; entre 55 e 64 anos, e a partir dos 65, 31,3%.",
            "Esse é o tamanho da demanda pela fisioterapia no país.",
            "Qual faixa de idade mais aparece no seu consultório?"
        ],
        "tags": "#coluna #saudepublica #fisioterapia"
    },
    {
        "titulo": "O que e o Pilates para o COFFITO",
        "partes": ["O que é o Pilates para o COFFITO?",
                   "Recurso cinesioterapêutico e mecanoterapêutico, de reeducação do movimento.",
                   "Se é terapêutico, cada sessão merece evolução no prontuário.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O que é", "o Pilates para", "o COFFITO?"],
        "resposta": {"destaque": "Recurso", "complemento": "cinesioterapêutico e mecanoterapêutico",
                     "fonte": "Resolução COFFITO nº 386/2011, Art. 1º, a"},
        "extra": {"titulo": "Se é terapêutico", "texto": "cada sessão merece\nevolução registrada."},
        "fato": ("Para o COFFITO, \"o método Pilates é um recurso cinesioterapêutico e "
                 "mecanoterapêutico que promove a educação e reeducação do movimento corporal, "
                 "composto por exercícios terapêuticos de promoção, prevenção e recuperação da "
                 "saúde físico funcional\" (Art. 1º, a)."),
        "fonte": "Resolução COFFITO nº 386/2011, Art. 1º, alínea a",
        "legenda": [
            "Para o COFFITO, \"o método Pilates é um recurso cinesioterapêutico e "
            "mecanoterapêutico que promove a educação e reeducação do movimento corporal, "
            "composto por exercícios terapêuticos de promoção, prevenção e recuperação da saúde "
            "físico funcional\" (Resolução COFFITO nº 386/2011, Art. 1º, alínea a).",
            "Promoção, prevenção e recuperação: as três frentes estão no texto da resolução.",
            "No seu estúdio, como você registra a evolução de cada aluno? Conta aqui.",
        ],
        "tags": "#pilates #fisioterapia #coffito",
    },
    {
        "titulo": "O papel do fisio no metodo Pilates",
        "partes": ["O que compete ao fisio no Pilates?",
                   "Pelo COFFITO: prescrever, induzir o tratamento e avaliar o resultado.",
                   "Para avaliar, ajuda ter cada sessão registrada.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O que compete", "ao fisio", "no Pilates?"],
        "resposta": {"destaque": "Prescrever", "complemento": "induzir o tratamento e avaliar o resultado",
                     "fonte": "Resolução COFFITO nº 386/2011, Art. 1º"},
        "extra": {"titulo": "Para avaliar", "texto": "cada sessão\nregistrada ajuda."},
        "fato": ("Segundo a Resolução COFFITO nº 386/2011, compete ao fisioterapeuta, para o "
                 "exercício do método Pilates, \"prescrever, induzir o tratamento e avaliar o "
                 "resultado a partir da utilização de recursos cinesioterapêuticos e "
                 "mecanoterapêuticos\" (Art. 1º, caput)."),
        "fonte": "Resolução COFFITO nº 386/2011, Art. 1º, caput",
        "legenda": [
            "Pela Resolução COFFITO nº 386/2011 (Art. 1º, caput), compete ao fisioterapeuta, para "
            "o exercício do método Pilates, \"prescrever, induzir o tratamento e avaliar o "
            "resultado a partir da utilização de recursos cinesioterapêuticos e "
            "mecanoterapêuticos\".",
            "A norma descreve o papel do fisioterapeuta no método, sem afirmar exclusividade.",
            "Na sua rotina, qual dessas três etapas toma mais tempo? Conta aqui.",
        ],
        "tags": "#pilates #fisioterapia #coffito",
    },
    {
        "titulo": "Estudio de Pilates e o registro no CREFITO",
        "partes": ["Estúdio de Pilates de fisioterapeuta precisa de registro?",
                   "Sim, no CREFITO da sua região.",
                   "E entra na fiscalização. Agenda e prontuário em ordem ajudam.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Estúdio de Pilates", "de fisio precisa", "de registro?"],
        "resposta": {"destaque": "Sim", "complemento": "no CREFITO da sua circunscrição",
                     "fonte": "Resolução COFFITO nº 386/2011, Art. 2º"},
        "extra": {"titulo": "Na fiscalização", "texto": "agenda e prontuário\nem ordem ajudam."},
        "fato": ("Quando indicado e administrado por fisioterapeuta, o Pilates fica vinculado ao "
                 "controle ético e fiscalizatório do Sistema COFFITO/CREFITOs, \"sendo, portando, "
                 "necessário o registro, por parte do profissional fisioterapeuta, do seu "
                 "consultório ou empresa no CREFITO de sua circunscrição\" (Art. 2º)."),
        "fonte": "Resolução COFFITO nº 386/2011, Art. 2º",
        "legenda": [
            "Quando indicado e administrado por fisioterapeuta, o Pilates fica vinculado ao "
            "controle ético e fiscalizatório do Sistema COFFITO/CREFITOs (Resolução COFFITO nº "
            "386/2011, Art. 2º).",
            "Por isso, o mesmo artigo exige que o fisioterapeuta registre o seu consultório ou "
            "empresa no CREFITO da sua circunscrição. Na dúvida, confirme os detalhes com o "
            "CREFITO da sua região.",
            "Seu estúdio já está registrado? Conta aqui.",
        ],
        "tags": "#pilates #crefito #estudiodepilates",
    },
    {
        "titulo": "Quiropraxia e osteopatia nao sao autonomas",
        "partes": ["Quiropraxia e osteopatia são autônomas da fisioterapia?",
                   "Não, pelo COFFITO. E o especialista segue o Código de Ética.",
                   "Mesma ética, mesmo cuidado com cada atendimento.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Quiropraxia e", "osteopatia são", "autônomas?"],
        "resposta": {"destaque": "Não", "complemento": "não são autônomas em relação à fisioterapia",
                     "fonte": "Resolução COFFITO nº 220/2001, Art. 6º"},
        "extra": {"titulo": "Na prática", "texto": "Código de Ética e\nProcesso Disciplinar."},
        "fato": ("A Resolução COFFITO nº 220/2001 sujeita o fisioterapeuta com título registrado ao "
                 "Código de Ética e ao Código de Processo Disciplinar, \"considerando que por "
                 "ordenamento legal, as atividades ora reconhecidas, não são autônomas em relação a "
                 "Fisioterapia\" (Art. 6º)."),
        "fonte": "Resolução COFFITO nº 220/2001, Art. 6º",
        "legenda": [
            "Pela Resolução COFFITO nº 220/2001 (Art. 6º), o fisioterapeuta com título registrado "
            "em quiropraxia ou osteopatia está sujeito ao Código de Ética e ao Código de Processo "
            "Disciplinar.",
            "O motivo está no próprio artigo: \"por ordenamento legal, as atividades ora "
            "reconhecidas, não são autônomas em relação a Fisioterapia\".",
            "Você atua com quiropraxia ou osteopatia? Conta aqui.",
        ],
        "tags": "#quiropraxia #osteopatia #coffito",
    },
    {
        "titulo": "O que o especialista em osteopatia identifica",
        "partes": ["O que o especialista em osteopatia pode identificar?",
                   "Alterações da mobilidade visceral e tensões das fáscias cranianas, entre outras.",
                   "Cada achado merece ficar registrado no prontuário.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O especialista", "em osteopatia", "identifica o quê?"],
        "resposta": {"destaque": "Visceral", "complemento": "mobilidade visceral e fáscias cranianas",
                     "fonte": "Resolução COFFITO nº 398/2011, Art. 3º, V"},
        "extra": {"titulo": "Na avaliação", "texto": "cada achado\nno prontuário."},
        "fato": ("O título é de \"Especialista Profissional em Osteopatia\" (Art. 2º) e uma das "
                 "competências é \"identificar alterações da mobilidade visceral, de tensões das "
                 "fáscias cranianas e das cavidades internas do corpo humano\" (Art. 3º, V)."),
        "fonte": "Resolução COFFITO nº 398/2011, Arts. 2º e 3º, V",
        "legenda": [
            "O título é de \"Especialista Profissional em Osteopatia\" (Resolução COFFITO nº "
            "398/2011, Art. 2º).",
            "E uma das competências desse especialista é \"identificar alterações da mobilidade "
            "visceral, de tensões das fáscias cranianas e das cavidades internas do corpo "
            "humano\" (Art. 3º, V).",
            "Como você registra a avaliação osteopática hoje? Conta aqui.",
        ],
        "tags": "#osteopatia #fisioterapia #coffito",
    },
    {
        "titulo": "Competencias do especialista em quiropraxia",
        "partes": ["O que compete ao especialista em quiropraxia?",
                   "Prescrever e aplicar ajustamentos articulares e recursos manipulativos, entre outros.",
                   "Cada técnica aplicada, na evolução. Até por áudio.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O que compete", "ao especialista", "em quiropraxia?"],
        "resposta": {"destaque": "Prescrever", "complemento": "e aplicar ajustamentos articulares",
                     "fonte": "Resolução COFFITO nº 399/2011, Art. 3º, IX"},
        "extra": {"titulo": "Na evolução", "texto": "cada técnica,\naté por áudio."},
        "fato": ("Compete ao Especialista Profissional em Quiropraxia \"prescrever e aplicar "
                 "ajustamento articulares, recursos manipulativos, recursos proprioceptivos, "
                 "adaptações funcionais, reeducação postural\" (Art. 3º, IX)."),
        "fonte": "Resolução COFFITO nº 399/2011, Art. 3º, IX",
        "legenda": [
            "Compete ao Especialista Profissional em Quiropraxia prescrever e aplicar ajustamentos "
            "articulares, recursos manipulativos, recursos proprioceptivos, adaptações funcionais "
            "e reeducação postural (Resolução COFFITO nº 399/2011, Art. 3º, IX).",
            "Qual desses recursos mais aparece na sua rotina? Conta aqui.",
        ],
        "tags": "#quiropraxia #fisioterapia #coffito",
    },
    {
        "titulo": "Atividade fisica para adultos segundo a OMS",
        "partes": ["O que a OMS recomenda para adultos?",
                   "Pelo menos cento e cinquenta minutos moderados por semana e força dois dias ou mais.",
                   "Planeje na agenda.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Quanta atividade", "física a OMS", "recomenda?"],
        "resposta": {"destaque": "150 min", "complemento": "por semana, moderada, para adultos",
                     "fonte": "OMS, Diretrizes de atividade física, 2020"},
        "extra": {"titulo": "E mais", "texto": "força muscular\nem 2 ou mais dias."},
        "fato": ("A OMS recomenda que adultos de 18 a 64 anos façam pelo menos 150–300 minutos "
                 "semanais de atividade aeróbica moderada, ou 75–150 minutos de atividade vigorosa "
                 "(ou combinação equivalente), além de fortalecimento muscular de intensidade "
                 "moderada ou maior envolvendo os grandes grupos musculares em 2 ou mais dias por "
                 "semana."),
        "fonte": ("OMS, Diretrizes sobre atividade física e comportamento sedentário, 2020 (fact "
                  "sheet \"Physical activity\", OMS Europa, 2021)"),
        "legenda": [
            "A OMS recomenda que adultos de 18 a 64 anos façam pelo menos 150 a 300 minutos por "
            "semana de atividade aeróbica moderada, ou 75 a 150 minutos de atividade vigorosa (ou "
            "uma combinação equivalente).",
            "Além disso, fortalecimento muscular de intensidade moderada ou maior, envolvendo os "
            "grandes grupos musculares, em 2 ou mais dias por semana (OMS, Diretrizes sobre "
            "atividade física e comportamento sedentário, 2020).",
            "É uma diretriz de saúde pública, não um protocolo de tratamento.",
            "Seus pacientes chegam perto dessa meta? Conta aqui.",
        ],
        "tags": "#atividadefisica #oms #fisioterapia",
    },
    {
        "titulo": "Equilibrio e forca depois dos 65",
        "partes": ["A partir dos sessenta e cinco, o que a OMS acrescenta?",
                   "Equilíbrio e força, três dias ou mais, para prevenir quedas.",
                   "Organize as sessões na agenda.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["A partir dos 65,", "o que a OMS", "acrescenta?"],
        "resposta": {"destaque": "3+ dias", "complemento": "equilíbrio e força, para prevenir quedas",
                     "fonte": "OMS, Diretrizes de atividade física, 2020"},
        "extra": {"titulo": "Multicomponente", "texto": "equilíbrio funcional\ne treino de força."},
        "fato": ("Para pessoas com 65 anos ou mais, a OMS recomenda, além das metas dos adultos, "
                 "atividade física multicomponente variada que enfatize equilíbrio funcional e "
                 "treino de força, de intensidade moderada ou maior, em 3 ou mais dias por semana, "
                 "para melhorar a capacidade funcional e prevenir quedas."),
        "fonte": "OMS, Diretrizes sobre atividade física e comportamento sedentário, 2020",
        "legenda": [
            "Para pessoas com 65 anos ou mais, a OMS recomenda, além das metas dos adultos, "
            "atividade física multicomponente variada que enfatize equilíbrio funcional e treino "
            "de força, de intensidade moderada ou maior, em 3 ou mais dias por semana.",
            "O objetivo, nas palavras da diretriz: melhorar a capacidade funcional e prevenir "
            "quedas (OMS, Diretrizes sobre atividade física e comportamento sedentário, 2020).",
            "É uma diretriz de saúde pública, não um protocolo de tratamento.",
            "Quantos dos seus pacientes têm 65 anos ou mais? Conta aqui.",
        ],
        "tags": "#idosos #prevencaodequedas #fisioterapia",
    },
    {
        "titulo": "Dor lombar em numeros",
        "partes": ["Quantas pessoas tiveram dor lombar em 2020?",
                   "Seiscentos e dezenove milhões, segundo a OMS. Principal causa de incapacidade no mundo.",
                   "Demanda grande pede agenda organizada.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Quantas pessoas", "tiveram dor lombar", "em 2020?"],
        "resposta": {"destaque": "619 mi", "complemento": "cerca de 1 em cada 13 pessoas",
                     "fonte": "OMS, 2023"},
        "extra": {"titulo": "Até 2050", "texto": "projeção de\n843 milhões de casos."},
        "fato": ("Segundo a OMS, em 2020 cerca de 1 em cada 13 pessoas — 619 milhões — teve dor "
                 "lombar, e a projeção é de 843 milhões de casos até 2050. A dor lombar é a "
                 "principal causa de incapacidade no mundo."),
        "fonte": ("OMS, comunicado de 07/12/2023 sobre as diretrizes de dor lombar crônica; fact "
                  "sheet \"Low back pain\" (2023)"),
        "legenda": [
            "Segundo a OMS, em 2020 cerca de 1 em cada 13 pessoas, ou 619 milhões, teve dor "
            "lombar. A projeção é de 843 milhões de casos até 2050.",
            "E a dor lombar é a principal causa de incapacidade no mundo (OMS, comunicado de "
            "07/12/2023 e fact sheet \"Low back pain\", 2023).",
            "Quantos pacientes com dor lombar você atende por semana? Conta aqui.",
        ],
        "tags": "#dorlombar #oms #fisioterapia",
    },
    {
        "titulo": "Atividade privativa do fisioterapeuta",
        "partes": ["O que é privativo do fisioterapeuta?",
                   "Pelo decreto-lei de 1969, executar métodos e técnicas fisioterápicos.",
                   "Cada técnica executada merece registro no prontuário.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["O que é", "privativo do", "fisioterapeuta?"],
        "resposta": {"destaque": "Privativo", "complemento": "executar métodos e técnicas fisioterápicos",
                     "fonte": "Decreto-Lei nº 938/1969, Art. 3º"},
        "extra": {"titulo": "Nível superior", "texto": "pelo Art. 2º\ndo Decreto-Lei 938."},
        "fato": ("O Decreto-Lei nº 938/1969 estabelece que o fisioterapeuta é profissional de "
                 "nível superior (Art. 2º) e que \"é atividade privativa do fisioterapeuta executar "
                 "métodos e técnicas fisioterápicos com a finalidade de restaurar, desenvolver e "
                 "conservar a capacidade física do\" paciente (Art. 3º)."),
        "fonte": "Decreto-Lei nº 938, de 13 de outubro de 1969, Arts. 2º e 3º",
        "legenda": [
            "O Decreto-Lei nº 938/1969 diz que o fisioterapeuta é profissional de nível superior "
            "(Art. 2º).",
            "E que \"é atividade privativa do fisioterapeuta executar métodos e técnicas "
            "fisioterápicos com a finalidade de restaurar, desenvolver e conservar a capacidade "
            "física do [paciente]\" (Art. 3º).",
            "Você sabia que essa definição é de 1969? Conta aqui.",
        ],
        "tags": "#fisioterapia #fisioterapeuta #legislacao",
    },
    {
        "interesse": "alto",
        "titulo": "Depoimento de paciente no post",
        "partes": ["Pode postar depoimento de paciente para se promover?",
                   "Não. O Código de Ética da fisioterapia proíbe, para autopromoção.",
                   "Divulgue sua agenda online, não depoimentos.",
                   "Teste a FisioSync grátis."],
        "pergunta": ["Pode postar", "depoimento de", "paciente?"],
        "resposta": {"destaque": "Não", "complemento": "proibido divulgar para autopromoção",
                     "fonte": "Resolução COFFITO nº 424/2013, Art. 10, V"},
        "extra": {"titulo": "Em vez disso", "texto": "divulgue sua\nagenda online."},
        "fato": ("O Código de Ética e Deontologia da Fisioterapia proíbe ao fisioterapeuta "
                 "\"divulgar, para fins de autopromoção, declaração, atestado, imagem ou carta de "
                 "agradecimento emitida por cliente/paciente/usuário ou familiar deste, em razão de "
                 "serviço profissional prestado\" (Art. 10, V)."),
        "fonte": ("Resolução COFFITO nº 424/2013 (Código de Ética e Deontologia da Fisioterapia), "
                  "Art. 10, V"),
        "legenda": [
            "O Código de Ética e Deontologia da Fisioterapia proíbe ao fisioterapeuta \"divulgar, "
            "para fins de autopromoção, declaração, atestado, imagem ou carta de agradecimento "
            "emitida por cliente/paciente/usuário ou familiar deste, em razão de serviço "
            "profissional prestado\" (Resolução COFFITO nº 424/2013, Art. 10, V).",
            "Como você divulga o seu trabalho sem depoimentos? Conta aqui.",
        ],
        "tags": "#etica #coffito #fisioterapia",
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
            "interesse": r.get("interesse", ""),
        }
        nome = f"{i:02d}-{slug(r['titulo'])}.json"
        with open(os.path.join(PASTA, nome), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"{nome:58} {palavras:2} palavras  legenda {len(legenda):4}")


if __name__ == "__main__":
    main()
