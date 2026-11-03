# Regras de conteúdo dos Reels — FisioSync

Decisão do Darlan em 02/11/2026: **1 Reels por dia, sobre conhecimento de
fisioterapia** (especialidades, Pilates, quiropraxia, osteopatia e toda a
lista de `temas.json`), para crescer o perfil no orgânico. O produto só
aparece no fim.

E a regra que vem junto, nas palavras dele: **"sempre vai consultar o
COFFITO pra não dizer merda e postar conhecimento fake."**

---

## 1. Tema não é fato

`temas.json` tem 408 temas. **Nenhum deles é conteúdo pronto.** "Reabilitação
vestibular" é um assunto; o vídeo precisa de uma afirmação verificável sobre
ele, com fonte.

Status de cada tema:

| status | quer dizer | pode virar vídeo? |
|---|---|---|
| `pendente` | só o assunto, sem fato | **não** |
| `fato-conferido` | tem `fato` e `fonte` oficiais | sim |
| `publicado` | já foi ao ar | não repetir |

O robô **só** monta vídeo a partir de roteiro com `fato` e `fonte`
preenchidos.

## 2. Onde conferir, em ordem de autoridade

1. **Lei federal** (texto no Planalto). Lei vale mais que resolução.
2. **COFFITO**: resoluções, acórdãos, página de especialidades.
3. **CREFITOs**: cartilhas e orientações regionais.
4. Para afirmação de **eficácia** ("X ajuda em Y"): só diretriz clínica ou
   revisão sistemática, com a referência na legenda. Sem isso, o vídeo não
   fala de eficácia.

Blog, artigo de clínica, post de outra marca e resposta de IA **não são
fonte**. A própria lista que originou `temas.json` foi gerada por IA: ela
serve de cardápio de assuntos, não de prova de nada.

## 3. Quando duas fontes oficiais discordam

Caso real, 02/11/2026: a Resolução COFFITO 414/2012 fala em guardar o
prontuário por **5 anos**; a Lei 13.787/2018 fixa **20 anos** para todo
prontuário de paciente. O CREFITO-1 orienta pelos 20; o CREFITO-12 ainda
citava os 5.

Regra: **vale a norma mais alta (a lei), o vídeo diz isso, e a legenda
manda confirmar com o CREFITO da região.** Nunca escolher a versão mais
cômoda.

Esse erro quase foi ao ar num Reels. Foi pego porque a legenda ia afirmar
algo além do fato conferido. Daí a regra seguinte.

## 4. Conferir de novo quando a peça diz mais que o fato

Um fato "conferido" cobre exatamente o que está escrito nele. Se o roteiro,
a legenda ou a tela vão afirmar qualquer coisa a mais — um número, uma
comparação, um "muita gente erra" —, isso precisa de fonte própria.

## 5. Conhecimento, não receita

- O vídeo fala **com o fisioterapeuta**, não prescreve para o paciente.
- Nada de "faça este exercício para dor lombar", dose, frequência ou
  protocolo.
- Nada de promessa de resultado.
- Quiropraxia e osteopatia aparecem como **especialidades do
  fisioterapeuta reconhecidas pelo COFFITO**. Sem atacar outras profissões
  e sem afirmar exclusividade de atuação.
- Pilates é **método**, não especialidade (a conferir na fonte antes de
  afirmar no vídeo).

## 6. O formato, travado

- Fundo branco, ciano `#18B7D8`, azul-marinho `#0B2948`.
- **No máximo 15 segundos.** Voz acelerada sempre.
- Pergunta → fato com a fonte **na tela** → consequência → como a FisioSync
  entra → chamada. A chamada só chega depois que o vídeo ligou o assunto ao
  produto.
- **Final sempre igual:** logo, "Teste grátis por 7 dias", selos **oficiais**
  do Google Play e da App Store, disponibilidade e `app.fisiosync.com.br`.
- Trilha e efeitos gerados por código (sem música de terceiro).
- Conferido quadro a quadro: vídeo com quadro quebrado não sai.
- A legenda termina com uma pergunta para comentário e de 3 a 5 hashtags,
  incluindo `#FisioSync`.

## 7. Ritmo

1 vídeo por dia. Alternar os grupos de `temas.json` para não cair dois dias
seguidos no mesmo assunto. Quando sobrarem menos de 7 roteiros prontos, é
hora de conferir fatos novos.

## 6. Ligação e fecho variado (decisão do Darlan, 03/11/2026)

A narração é uma linha só: **pergunta → dado → o que isso muda na prática →
pedido que nasce do assunto**. Nada de "teste grátis" caindo do nada.

- O pedido final quase sempre é **mandar para alguém ou salvar**
  ("Manda pro colega que só alonga", "Salva pra lembrar na próxima
  avaliação"). Envio e salvamento são o que faz o Reels crescer.
- A FisioSync só entra na **fala** quando o assunto leva a ela (agenda,
  prontuário, avaliação registrada). O selo "teste grátis por 7 dias", as
  lojas e o site ficam sempre na **tela** final.
- Dois Reels seguidos nunca terminam com a mesma frase (o `gerar_fila.py`
  barra).
- O que a tela mostra em cada bloco é o que a voz está dizendo naquele
  momento, na mesma ordem.
- Nada de "marque um amigo" ou "curta": é isca de engajamento e a Meta
  derruba o alcance.

## 7. Filtro de interesse (03/11/2026)

Só vai ao ar o que um fisioterapeuta com 5 anos de prática **aprenderia**,
ou **mandaria para um colega ou paciente**. Norma que o profissional já
conhece ("quiropraxia é especialidade") é verdadeira, mas é chata: fica
fora. Estudos e diretrizes entram, com o número exato da fonte e os
cuidados ("se associou", não "causa").
