# Auditoria de veracidade — @fisiosyncapp

Data: 05/11/2026. Auditor independente: não escrevi nenhum destes textos e não editei nenhum arquivo do repositório.

## Como foi feito, e o que não consegui

**Escopo A**: 18 roteiros de `reels/fila/` com `interesse == "alto"` cujo `titulo` não está em `reels/historico-reels.json`. São os itens 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 e 45. Ficaram fora o 15 e o 16, já publicados, e o 21, marcado como `baixo-reels`.

Para cada roteiro comparei a narração, cada tela, o fecho e a legenda com o `fato`. Depois conferi o `fato` na fonte. O vídeo divide a tela em blocos (`proporcoes` em `gerar_fila.py` e `ReelDica.tsx`), e cada parte da fala corresponde a um bloco:

| Parte da fala | Tela no mesmo momento |
|---|---|
| parte 1 | `pergunta` |
| parte 2 | `resposta` |
| parte 3 | `extra` |
| parte 4 | `fecho.frase` |

**Escopo B**: 17 pautas de `pautas.json` com `interesse == "alto"` e `status == "livre"`.

**Limitações de acesso.** O proxy recusa curl (HTTP 403) para PubMed, eutils, PMC, Crossref, PEDro, normasbrasil, legisweb, planalto, cdc.gov e outros. Toda a conferência foi feita com WebFetch em páginas que a ferramenta conseguiu abrir: PEDro, QxMD, repositórios institucionais, páginas de editoras, cópias do DOU na BVS SES-SP, normasbrasil e a AAFP.

A ferramenta só devolve trechos literais de até 125 caracteres, e o restante vem parafraseado. Por isso:
- conferi cada número-chave em pelo menos duas páginas independentes sempre que foi possível;
- marquei como **NÃO VERIFICADO** o que não consegui ver;
- o PubMed e o PMC não abriram (página vazia ou captcha), com uma exceção: o artigo de Johnson (2020) abriu no PMC.

---

## Resumo

| # | Item | Veredito | Gravidade | Problema em uma linha |
|---|---|---|---|---|
| 17 | Força de preensão e mortalidade | CORRIGIR | moderada | Fala e tela dão associação (coorte) sem dizer que é associação |
| 18 | Alongamento e lesão esportiva | CORRIGIR | **grave** | "Em vinte e cinco ensaios, alongar não mostrou benefício": 25 é a metanálise inteira; o dado de alongamento vem de **3** ensaios |
| 19 | O nórdico e os isquiotibiais | OK | – | – |
| 20 | Exercício e quedas em idosos | CORRIGIR | moderada | "idosos" sem "da comunidade" (a revisão só incluiu idosos que vivem na comunidade) |
| 22 | Problema crônico de coluna no Brasil | CORRIGIR | **grave** | "Demanda não falta" e "Esse é o tamanho da demanda pela fisioterapia" não estão no fato e não são o que o dado mede |
| 23 | Regras de Ottawa (**MP4 já pronto**) | CORRIGIR | **grave** | "Até quarenta por cento menos raio-x" apresenta estimativa dos autores como resultado medido; fala ("até 40") difere da tela ("30% a 40%") |
| 24 | Hérnia extrusa | CORRIGIR | menor | Falta "lombar"; legenda afirma sobre o estudo o que só foi lido no resumo |
| 25 | FIFA 11+ | CORRIGIR | **grave** | "Guarda essa pra pré-temporada": o FIFA 11+ é aquecimento de todo treino, no mínimo 2x/semana |
| 26 | Meniscectomia x cirurgia simulada | CORRIGIR | menor | "Meniscectomia" sem "parcial"; falta "sem artrose"; legenda tem superlativo sem fonte |
| 27 | Sentar e levantar 30 s | OK | – | – |
| 28 | Fascite plantar | CORRIGIR | **grave** | Fecho "Elevação de calcanhar, uma perna, toalha nos dedos." é receita de exercício e omite a carga progressiva que define a intervenção |
| 29 | Infiltração no cotovelo de tenista | CORRIGIR | **grave** | "Alívio rápido" e "Infiltração alivia rápido" não estão no fato |
| 30 | O que previne dor lombar | CORRIGIR | menor | Fecho ambíguo ("informação" sozinha não preveniu); legenda com afirmações fora do fato |
| 31 | Patelofemoral | CORRIGIR | **grave** | "Revisão ... com catorze ensaios: quadril mais joelho foi superior": 14 é a revisão inteira, não a comparação; "Pesquisa da UFMG" fora do fato |
| 32 | Descompressão subacromial | OK | – | Só ajustes opcionais |
| 33 | TUG sozinho | CORRIGIR | moderada | Sensibilidade de 31% sem o corte (≥13,5 s) e sem a população (idosos da comunidade) |
| 34 | Kinesio Taping | CORRIGIR | menor | "lombalgia" sem "crônica inespecífica"; legenda com afirmação sem fonte |
| 45 | Depoimento de paciente | CORRIGIR | menor | "Vale também para as redes sociais" não está no fato (a norma sustenta: Art. 47) |

Total do escopo A: **15 CORRIGIR**, **3 OK** e nenhum fato com número errado. Os erros estão no que o roteiro diz **além** do fato ou **ao lado** dele: atribuição de nº de estudos, população, estimativa tratada como resultado, causalidade e frases de fecho.

---

## Escopo A — detalhe por item

### 17 · Força de preensão e mortalidade — CORRIGIR (moderada)

**Fato x fonte: confere.** Leong et al., Lancet 2015, conferido em dois repositórios: AKU eCommons e UiTM.
- 139.691 analisados, de 142.861 inscritos, em 17 países;
- mediana de 4,0 anos de seguimento;
- HR 1,16 (1,13–1,20) por 5 kg a menos;
- *"Grip strength was a stronger predictor of all-cause and cardiovascular mortality than systolic blood pressure."*

Os participantes tinham **35 a 70 anos** (domicílios com alguém de 35–70). O fato e a legenda dizem só "adultos".

**Problemas**
- **Associação apresentada como efeito.** Fala: "Cada cinco quilos a menos, dezesseis por cento mais risco de morte." Tela (resposta): "16% / mais risco de morte a cada 5 kg a menos". Fala e tela não dizem "associação", e a estrutura "cada X a menos → Y% mais risco" soa causal. A ressalva existe só na legenda, mas a regra da casa (REGRAS §8.3) pede "se associou" no que vai ao ar.
- Recomendado: incluir "35 a 70 anos" no fato e na legenda.

**Correção sugerida**
- Narração (30 palavras): "Quanto diz a preensão? Cada cinco quilos a menos se associou a dezesseis por cento mais risco de morte. Previu melhor que a pressão sistólica. Anota essa pra próxima avaliação."
- Tela, complemento: "mais risco de morte associado a cada 5 kg a menos".

### 18 · Alongamento e lesão esportiva — CORRIGIR (grave)

**Fato x fonte: os números conferem**, mas o fato está incompleto.

Lauersen et al., BJSM 2014, conferido no PEDro 39522 e no manuscrito dos autores (repositório NIH Noruega):
- 25 ensaios, 26.610 participantes, 3.464 lesões;
- alongamento RR 0,963 (0,846–1,095); força RR 0,315 (0,207–0,480); propriocepção 0,550;
- frase dos autores: *"Strength training reduced sports injuries to less than 1/3"*.

O manuscrito diz que o estimador de alongamento é *"based on three studies"*: Jamtvedt 2010 (adultos recrutados pela internet), Pope 1998 e Pope 2000 (**recrutas do exército**). O de força tem 4 estudos.

**Problemas**
1. Fala: **"Em vinte e cinco ensaios, alongar não mostrou benefício."** Atribuição errada. Os 25 são a metanálise inteira; o resultado do alongamento vem de 3 ensaios, 2 deles com militares.
2. Fecho: **"Na prevenção, a força vem primeiro."** É uma ordem de prioridade que o estudo não testou. A comparação entre estratos não foi testada formalmente, e o estrato de força tem 4 ensaios. O fato só sustenta "o treino de força teve o maior efeito".
3. Pergunta (fala e tela): "Alongamento previne lesão?" O estudo é sobre lesão esportiva, e a versão original do roteiro dizia "lesão esportiva".
4. Legenda: "o alongamento costuma ser a primeira lembrança" é afirmação sobre prática comum sem fonte (REGRAS §4).

**Correção sugerida**
- Narração (29 palavras): "Alongamento previne lesão esportiva? Numa metanálise, alongar não mostrou benefício. Treino de força reduziu as lesões a menos de um terço. Na prevenção, a força teve o maior efeito."
- Tela, pergunta: "Alongamento / previne lesão / esportiva?". Fecho.frase: "Na prevenção, a força teve o maior efeito."
- Fato: acrescentar "(estrato de alongamento: 3 ensaios, 2 com recrutas militares; força: 4 ensaios)".
- Legenda: trocar a primeira frase por algo neutro, por exemplo "Alongar previne lesão esportiva? Uma metanálise olhou para isso."

### 19 · O nórdico e os isquiotibiais — OK

van Dyk et al., BJSM 2019, conferido em três páginas: QxMD, PEDro 56553 e a página do BJSM.
- 15 estudos, 8.459 atletas;
- RR 0,49 (0,32–0,74), "up to 51%";
- 8 ensaios randomizados: RR 0,52 (0,32–0,85);
- *"The NHE essentially halves the rate of hamstring injuries..."*

Fala, telas e legenda são fiéis. "51% menos risco" sem "até" na tela é aceitável, porque é a estimativa pontual.

### 20 · Exercício e quedas em idosos — CORRIGIR (moderada)

**Fato x fonte: confere.** Sherrington et al., Cochrane 2019, conferido na QxMD e no resumo para leigos da Cochrane:
- 108 ensaios, 23.407 participantes, 25 países, média de 76 anos, 77% mulheres;
- taxa de quedas RaR 0,77 (0,71–0,83), certeza alta;
- pessoas que caem: RR 0,85;
- equilíbrio e funcionais: 24%;
- combinação de tipos: *"probably reduce ... by 34%"*, certeza moderada;
- Tai Chi: *"may reduce ... by 19%"*.

Não achei versão mais nova da revisão.

**Problema.** Fala e tela: "Quanto o exercício reduz quedas **em idosos**?" A revisão só incluiu *"people aged 60+ years living in the community"*. A generalização para idosos institucionalizados ou hospitalizados não tem apoio nesta fonte. A legenda está correta.

**Correção sugerida**
- Narração (30 palavras): "Quanto o exercício reduz quedas em idosos da comunidade? Na Cochrane, vinte e três por cento na taxa de quedas. Combinando tipos, provavelmente trinta e quatro. Equilíbrio e força, juntos."
- Tela, pergunta: "...em idosos / da comunidade?".
- Opcional: "Equilíbrio e força, juntos" sugere que a combinação supera equilíbrio sozinho, o que a revisão não comparou diretamente. Pode ficar, mas não deve virar "o melhor".

### 22 · Problema crônico de coluna no Brasil — CORRIGIR (grave)

**Fato x fonte: confere.** Malta et al., *Rev Bras Epidemiol* 2022; 25:e220032, PDF na SciELO:
- 21,6% (21,0–22,1);
- mulheres 24,5%; homens 18,3%;
- 18–24 anos: 9,3%; 55–64 anos e 65+: 31,3%;
- 88.531 respondentes.

Os autores alertam: *"Como se trata de prevalências autorreferidas, os valores podem ter sido superestimados."*

**Problemas**
- Fecho (fala e tela): **"Demanda não falta."**
- Legenda: **"Esse é o tamanho da demanda pela fisioterapia no país."**
- Nenhuma das duas frases está no fato. A prevalência autorreferida de problema de coluna não é demanda por fisioterapia: nem toda pessoa com o problema precisa ou procura fisioterapia, e os próprios autores falam em possível superestimação. Um fisioterapeuta pode chamar isso de enganoso. É exatamente o tipo de afirmação "a mais" que a REGRAS §4 proíbe sem fonte.

**Correção sugerida**
- Fecho (fala e tela): "É autorrelato, não diagnóstico." A narração fica com 30 palavras.
- Legenda: trocar a frase da demanda por "É autorrelato: os autores alertam que os valores podem estar superestimados." Incluir essa frase no fato, com a fonte.

### 23 · Regras de Ottawa no tornozelo — CORRIGIR (grave; prioridade)

`reels/prontos/23-regras-de-ottawa-no-tornozelo.mp4` **já foi renderizado com o texto atual**, ainda não foi publicado e precisa ser refeito.

**Fato x fonte: confere.** Bachmann et al., BMJ 2003, conferido em três páginas:
- QxMD e UvA DARE: 27 estudos e 15.581 pacientes na metanálise; probabilidade de fratura abaixo de 1,4% com prevalência de 15%; *"near-100% sensitivity"*;
- AAFP 2003: *"The pooled sensitivity from all studies was 97.6 percent (95 percent confidence interval [CI], 96.4 to 98.9)"*;
- sobre os 30–40%: na QxMD, *"estimated that using the rules could reduce unnecessary radiographs by 30–40%"*; na AAFP, *"could reduce radiograph use by 30 to 40 percent"*.

**Problemas**
1. Fala: **"Até quarenta por cento menos raio-x desnecessário."** É uma **estimativa/projeção** dos autores ("should/could reduce"), mas foi apresentada como resultado observado. A fala também corta o piso de 30%.
2. Fala e tela divergem no mesmo bloco: a fala diz "até quarenta", a tela diz "30% a 40%". A tela também apresenta o número como resultado.
3. Menor: a fala diz "sensibilidade de quase noventa e oito por cento" sem dizer "para fratura" (a tela diz). A legenda diz "a chance de fratura com a regra negativa **ficou** abaixo de 1,4%", mas é um cálculo hipotético para prevalência de 15%; o certo é "seria".

**Correção sugerida**
- Narração (30 palavras): "Paciente com entorse pedindo raio-x? Pelas regras de Ottawa, sensibilidade de quase noventa e oito por cento. Estimativa: trinta a quarenta por cento menos raio-x desnecessário. Salva pra próxima entorse."
- Tela, extra: título "Estimativa: 30% a 40%", texto "menos raio-x / desnecessário."
- Legenda: "ficou" → "seria".

### 24 · Hérnia extrusa e regressão espontânea — CORRIGIR (menor)

**Fato x fonte: confere.** Chiu et al., Clin Rehabil 2015, conferido na QxMD e na BVB:
- 31 estudos incluídos, 9 usados no cálculo;
- regressão espontânea: 96% sequestro, 70% extrusão, 41% protrusão, 13% abaulamento;
- resolução completa: 43% e 15%;
- só hérnia **lombar** em tratamento conservador.

**Problemas**
- Fala e tela: "Laudo com hérnia extrusa assusta?" Falta "lombar"; o achado não se aplica a hérnia cervical.
- A fala não diz que a regressão é na imagem. A legenda diz.
- Legenda: "**o estudo** não diz em quanto tempo ela aconteceu". Quem escreveu leu só o resumo; a observação do lote 2 diz "o resumo não ... diz". Não consegui ler o texto completo (SAGE, pago), então essa afirmação sobre o estudo inteiro está **NÃO VERIFICADA**.

**Correção sugerida**
- Narração (29 palavras): "Laudo com hérnia lombar extrusa assusta? Numa revisão, setenta por cento das extrusões regrediram espontaneamente na imagem. Nos sequestros, noventa e seis. Dado bom pra ter na primeira consulta."
- Tela, pergunta: "Laudo com / hérnia lombar / extrusa assusta?".
- Legenda: "o resumo do estudo não informa em quanto tempo".

### 25 · FIFA 11+ no futebol amador — CORRIGIR (grave)

**Fato x fonte: confere.**
- Thorborg et al., BJSM 2017, conferido no PEDro 49470 e em Aalborg: 6 ensaios randomizados por conglomerado no futebol recreativo/sub-elite; FIFA 11+ (4 ensaios) IRR 0,61 (0,48–0,77); FIFA 11 (2 ensaios) 0,99 (0,80–1,23).
- Sadigursky et al. 2017, conferido no DOAJ: 6 ensaios, 6.344 jogadores, RR 0,70 (0,52–0,93); conclusão: *"The FIFA 11+ warm-up program reduced the risk of injury ... by 30%"*.

**Problemas**
1. Fecho (fala e tela): **"Guarda essa pra pré-temporada."** O material oficial da FIFA diz que o programa *"should be performed, as a standard warm-up, at the start of each training session at least twice a week"*. É aquecimento de rotina, durante a temporada inteira. "Pré-temporada" acrescenta um momento de uso que não está no fato e contradiz o desenho do programa. Um fisioterapeuta pode chamar isso de enganoso.
2. Legenda: "Um programa de aquecimento" não está no fato, embora a fonte sustente; incluir no fato.
3. Legenda: "autores de Salvador (BA)". **NÃO VERIFICADO**: as páginas que abri não mostram as afiliações, e o PDF da Springer foi bloqueado.

**Correção sugerida**
- Fecho: "Vale pro aquecimento do time." A narração fica com 30 palavras.
- Fato: acrescentar "programa de aquecimento (Sadigursky 2017)".

### 26 · Meniscectomia x cirurgia simulada — CORRIGIR (menor)

**Fato x fonte: confere.** Sihvonen et al., NEJM 2013, conferido na Epistemonikos, na DynaMed e na HospiMedica:
- *"multicenter, randomized, double-blind, sham-controlled"*;
- 146 pacientes de 35–65 anos, menisco **medial** degenerativo, **sem artrose**;
- Lysholm 21,7 x 23,3 (−1,6; −7,2 a 4,0);
- nenhuma diferença nos desfechos principais em 12 meses.

**Problemas**
- Fala e tela: "**Meniscectomia** em lesão degenerativa funciona?". O procedimento testado foi a **meniscectomia parcial artroscópica**, e a população era sem artrose. Do jeito que está, a frase generaliza para qualquer meniscectomia e para joelho com artrose.
- "Duplo-cego, no New England." O nome da revista está cortado.
- Legenda: "Um dos estudos mais citados sobre menisco degenerativo." Superlativo sem fonte (REGRAS §4).

**Correção sugerida**
- Narração (26 palavras): "Meniscectomia parcial em lesão degenerativa, sem artrose, funciona? Contra cirurgia simulada, sem diferença em doze meses. Os dois grupos melhoraram parecido. Duplo-cego, no New England Journal."
- Legenda: "Um ensaio com cirurgia simulada sobre menisco degenerativo."

### 27 · Sentar e levantar em 30 segundos — OK

Conferido em duas cópias da folha oficial do CDC STEADI (NJ.gov e CDC Stacks 157303), ambas de **2017**, com tabela idêntica:
- 60–64: <14 / <12;
- 65–69: <12 / <11;
- 70–74: <12 / <10;
- 75–79: <11 / <10;
- 80–84: <10 / <9;
- 85–89: <8 / <8;
- 90–94: <7 / <4.

A folha diz *"A below average score indicates a risk for falls"*. A cadeira tem assento de 17", os braços ficam cruzados, e se o paciente usar os braços a nota é zero. Fala, telas e legenda são fiéis.

### 28 · Fascite plantar e fortalecimento — CORRIGIR (grave)

**Fato x fonte: confere.** Rathleff et al., SJMSS 2015;25(3):e292–300, conferido no texto completo (cópia da Braceworks), na Natural Medicine Journal e no PEDro (só a citação):
- 48 pacientes, diagnóstico por ultrassom;
- palmilha + alongamento x palmilha + força em dias alternados;
- FFI 29 pontos menor aos 3 meses (6–52; p = 0,016);
- sem diferença aos 1, 6 e 12 meses.

O protocolo do texto completo:
- carga progressiva: *"started at a 12 repetition maximum (RM) for three sets"*, depois 10RM×4 e 8RM×5;
- *"increased the load by using a backpack with books"*;
- 3 s subindo, 2 s parado, 3 s descendo.

**Problemas**
1. Fecho (fala e tela): **"Elevação de calcanhar, uma perna, toalha nos dedos."**
   - É uma instrução de exercício na tela final, o que as INSTRUCOES ("Orientação clínica, protocolo ... proibido") e a REGRAS §5 vetam.
   - Omite o que define a intervenção testada: **alta carga progressiva** (RM, mochila com carga), dias alternados e palmilha nos dois grupos. Elevação de calcanhar com toalha sem essa progressão não é a intervenção que teve o resultado.
2. Legenda: "o alongamento costuma ser a primeira escolha" é afirmação sobre prática sem fonte (REGRAS §4).

**Correção sugerida**
- Fecho (fala e tela): "Ensaio pequeno, com quarenta e oito pacientes." A narração fica com 29 palavras.
- Legenda: trocar a primeira frase por algo neutro.

### 29 · Infiltração no cotovelo de tenista — CORRIGIR (grave)

**Fato x fonte: confere.** Coombes et al., JAMA 2013, conferido no manuscrito dos autores (CORE) e no comunicado da JAMA (ScienceDaily):
- 165 pacientes, quadro unilateral com mais de 6 semanas;
- 83% x 96% recuperados ou muito melhores em 1 ano;
- recorrência 54% x 12% (44/81 x 10/81, todos os pacientes de cada braço da injeção), definida como *"complete recovery/much improvement at 4 or 8 weeks, but not later"*;
- a fisioterapia não mudou os resultados de 1 ano.

**Problemas**
- Tela e fala: **"Alívio rápido nem sempre se sustenta."**
- Legenda: **"Infiltração alivia rápido o cotovelo de tenista."**
- O fato **não** contém o benefício de curto prazo da infiltração. A fonte tem esse dado: em 4 semanas, sem fisioterapia, 71% (30/42) com corticoide contra 10% (4/41) com placebo. Mas ele não foi levado ao fato.
- A frase da legenda é uma afirmação geral de eficácia, e a REGRAS §2.4 exige revisão sistemática ou diretriz para isso.

**Correção sugerida.** Uma das duas opções:
- (a) Acrescentar ao fato o resultado de 4 semanas com a fonte (Coombes 2013, Tabela 2) e reescrever a legenda como resultado do ensaio: "No ensaio, a infiltração foi melhor em 4 semanas. E depois de um ano?"
- (b) Fala e tela: "**Melhora inicial** nem sempre se sustenta." A narração fica com 30 palavras, e a frase é sustentada pela própria definição de recorrência no fato. Legenda: "Infiltração no cotovelo de tenista: e depois de um ano?"

### 30 · O que previne dor lombar — CORRIGIR (menor)

**Fato x fonte: confere.** Steffens et al., JAMA Intern Med 2016, conferido no resumo (chiro.org) e no texto completo (cópia da Braceworks):
- 21 ensaios, 30.850 participantes;
- exercício + educação: RR 0,55 (0,41–0,74), qualidade moderada, curto prazo, **4 ensaios**;
- exercício sozinho: 0,65, qualidade baixa a muito baixa;
- educação sozinha: 1,03; cintas: 1,01; palmilhas: 1,01;
- longo prazo, exercício + educação: 0,73 (0,55–0,96), 2 ensaios, qualidade baixa;
- afiliação: *"Department of Physiotherapy, Federal University of Minas Gerais"* para Steffens, Pereira, Oliveira e Teixeira-Salmela.

**Problemas**
1. Fecho (fala e tela): **"Na prevenção, movimento e informação."** Pode ser lido como duas estratégias eficazes cada uma. Mas a educação **sozinha** não preveniu (RR 1,03).
2. Legenda, afirmações fora do fato. As duas são verdadeiras, mas precisam entrar no fato:
   - "com pesquisadores da UFMG";
   - "No longo prazo, o efeito de exercício com educação diminuiu."
3. Legenda: "Uma metanálise ... **respondeu**" exagera a certeza. Para cintas e palmilhas a evidência é de qualidade baixa a muito baixa.
4. Tela: o destaque "**Não**" é categórico para evidência baixa ou muito baixa. O complemento ("não pareceram prevenir") atenua, mas o destaque é o que se lê.

**Correção sugerida**
- Fecho: "Educação sozinha não pareceu prevenir." A narração fica com 27 palavras.
- Legenda: "respondeu" → "investigou".
- Fato: incluir UFMG e o resultado de longo prazo.
- Tela, complemento: "não pareceram prevenir (evidência fraca)".

### 31 · Patelofemoral: quadril e joelho — CORRIGIR (grave)

**Fato x fonte: confere.** Nascimento et al., JOSPT 2018, conferido no repositório da UFMG (Departamento de Fisioterapia; DOI 10.2519/jospt.2018.7365):
- *"The review included 14 trials involving 673 participants."*;
- contra nenhum treino ou placebo: dor −3,3;
- *"In addition, hip and knee strengthening was superior to knee strengthening alone"*: dor −1,5 (−2,3 a −0,8), atividade DMP 0,7 (0,2 a 1,3);
- *"Results were maintained beyond the intervention period."*;
- sem mudança de força.

**Problemas**
1. Fala: **"Revisão brasileira com catorze ensaios: quadril mais joelho foi superior."** Atribuição errada. 14 ensaios e 673 participantes são a revisão inteira, que inclui comparações contra nenhum treino ou placebo. A superioridade sobre fortalecer só o joelho veio de um subconjunto. A observação do próprio lote 2 já alertava para isso.
2. Fecho (fala e tela): **"Pesquisa da UFMG, vale conhecer."** O fato diz "pesquisadores brasileiros", não UFMG. O repositório da UFMG hospeda o trabalho, mas a afiliação de cada autor no artigo não foi conferida, por mim nem no fato. A legenda repete "pesquisadores da UFMG".

**Correção sugerida**
- Narração (29 palavras): "Dor patelofemoral: fortalece só o joelho? Numa revisão brasileira, quadril mais joelho foi superior a só joelho. Para dor e atividade, com efeito mantido. Revisão com pesquisadores da UFMG."
- Incluir a UFMG no fato com a fonte (repositório UFMG), ou voltar a "pesquisadores brasileiros".

### 32 · Descompressão subacromial e placebo — OK

**Fato x fonte: confere.** Beard et al., Lancet 2018 (CSAW), conferido no White Rose eprints e no NIHR Evidence:
- 313 pacientes, 32 hospitais do Reino Unido;
- dor há ≥3 meses, manguito íntegro, após exercício e ≥1 infiltração;
- escore de Oxford aos 6 meses: 32,7 x 34,2 (−1,3; −3,9 a 1,3);
- contra nenhum tratamento: +2,8 e +4,2, *"not clinically important"*.

Ajustes opcionais, que não mudam o veredito:
- a tela final mostra o ano por extenso ("em dois mil e dezoito"); na tela, o melhor é "em 2018";
- a legenda diz "mudou a conversa sobre dor subacromial", afirmação de impacto sem fonte;
- vale lembrar a alta não adesão (23%, 42% e 12% não receberam o tratamento sorteado).

### 33 · TUG sozinho e risco de queda — CORRIGIR (moderada)

**Fato x fonte: confere.** Barry et al., BMC Geriatr 2014, conferido no repositório da Univ. Limerick:
- 25 estudos na revisão, 10 na metanálise;
- corte ≥13,5 s; sensibilidade 0,31 (0,13–0,57); especificidade 0,74 (0,52–0,88);
- *"should not be used in isolation"*, em idosos **da comunidade**.

**Problemas**
- Fala e tela: "sensibilidade de trinta e um por cento" e "31% de sensibilidade para prever quedas", **sem o ponto de corte** e **sem a população**. A sensibilidade depende do corte: o STEADI do CDC, por exemplo, usa ≥12 s. Quem usa outro corte vai aplicar o 31% errado.
- Legenda: "um dos testes mais usados" é afirmação sem fonte.

**Correção sugerida**
- Narração (30 palavras): "Só o TUG pra risco de queda? Corte de treze e meio segundos: sensibilidade de trinta e um por cento. Em idosos da comunidade, capacidade limitada. Melhor não usar isolado."
- Tela, complemento: "de sensibilidade (corte de 13,5 s)". Tela, extra: "Em idosos da comunidade / capacidade limitada."

### 34 · Kinesio Taping e a tensão da fita — CORRIGIR (menor)

**Fato x fonte: confere.** Parreira et al., J Physiother 2014, conferido no PEDro 39922 e na Macquarie:
- 148 pessoas com dor lombar **crônica inespecífica**;
- 8 sessões em 4 semanas, 10–15% de tensão, com dobras, contra fita sem tensão;
- dor −0,4 (−1,3 a 0,4); incapacidade −0,3 (−1,9 a 1,3);
- *"These results challenge the proposed mechanism of action"*;
- pequena diferença na percepção global de efeito: 1,4 (0,3 a 2,5).

**Problemas**
- Fala: "pacientes com lombalgia". Falta "crônica" (inespecífica).
- "Estudo brasileiro" (fala, tela e fato): os nomes dos autores são brasileiros, mas **não consegui verificar** a afiliação no artigo. As páginas que abri não a mostram.
- Legenda: "A tensão da fita é o centro do método." Afirmação sem fonte.

**Correção sugerida**
- Narração (28 palavras): "...com lombalgia crônica, não mudou dor nem incapacidade..."
- Conferir a afiliação no PDF antes de manter "brasileiro".

### 45 · Depoimento de paciente no post — CORRIGIR (menor: fato incompleto)

**Fato x fonte: confere.** O Art. 10, V da Resolução COFFITO 424/2013 foi conferido no normasbrasil. Ali o início do inciso aparece literal: *"divulgar, para fins de autopromoção, declaração, atestado, imagem ou carta de agradecimento emitida por"*. O restante foi lido em paráfrase e é coerente com a citação do fato.

**Vigência.** A Res. 552/2022 alterou só o Art. 9º, VII e revogou os Arts. 37 e 39. Não encontrei norma posterior que mude o Art. 10, V; as Res. 610/2025 e 630/2025 tratam de outros temas. Um programa de disciplina da UFG de 2026 ainda usa a 424/2013 como norma de publicidade.

**Problema.** Fala e tela: **"Vale também para as redes sociais."** Isso não está no fato. A norma sustenta a frase:
- Art. 47: *"A utilização da Rede Mundial de Computadores (Internet) para fins profissionais deve seguir os preceitos deste Código e demais normatizações pertinentes."*;
- Art. 46: *"em qualquer meio de comunicação"*.

Mas a regra da casa exige que isso esteja no fato.

**Correção sugerida.** Acrescentar o Art. 47 ao fato e à fonte. A narração pode ficar como está.

---

## Observações gerais

1. **Onde corrigir.** Os JSON da fila são gerados por `reels/gerar_fila.py` (ROTEIROS + AJUSTES; o `main()` sobrescreve `reels/fila/*.json`). Corrigir só o JSON se perde na próxima geração. A correção tem que ir para o `gerar_fila.py`.
2. **MP4 pronto.** `reels/prontos/23-regras-de-ottawa-no-tornozelo.mp4` tem o erro do item 23 e não deve ser publicado como está.
3. **Padrões que se repetiram**, e que valem uma trava automática ou uma pergunta fixa na revisão:
   - **"N ensaios" da revisão inteira colado num resultado de subgrupo** (itens 18 e 31).
   - **População, condição ou corte omitidos na fala e na tela, embora presentes na legenda**: "idosos" sem "da comunidade" (20), TUG sem corte (33), "lombalgia" sem "crônica" (34), "hérnia" sem "lombar" (24), meniscectomia sem "parcial" e sem "sem artrose" (26). A legenda não corrige o que a voz disse: pouca gente lê a legenda.
   - **"Se associou" só na legenda**, não na fala nem na tela (17).
   - **Estimativa ou projeção dita como resultado** (23).
   - **Ganchos e fechos com afirmações sem fonte** ("costuma ser a primeira escolha", "mais citados", "mais usados", "demanda", "pré-temporada", "alívio rápido"). A REGRAS §4 proíbe isso, e foram as frases escritas "em volta" do fato que mais erraram.
4. **Sincronia fala/tela (técnico).** O fecho na tela dura 2,2 s fixos (`FECHO` em `narrar.mjs`), e os blocos 1–3 são esticados sobre `fala − 1,8 s`. Quando a 4ª frase falada passa de cerca de 1,8 s, as telas ficam atrasadas em relação à voz. Exemplos: o item 28, que no texto atual tem 8 palavras na 4ª frase, e o item 32, com 8 palavras. Não muda o conteúdo, mas contraria "a tela mostra o que a voz diz naquele momento".

---

## Escopo B — banco do feed (`pautas.json`, alto + livre)

| id | Veredito | Conferência / problema |
|---|---|---|
| regulacao-016 | OK | Res. 414/2012, Art. 1º, §1º, VI, literal no normasbrasil: *"...bem como o quantitativo provável de atendimento"*. Sem revogação encontrada. A Lei 13.787/2018 mexe só no prazo de guarda (Art. 6º), não neste inciso. |
| etica-101 | OK | Art. 15, III, literal: *"divulgar e prometer terapia infalível, secreta ou descoberta cuja eficácia não seja comprovada"*. Sem alteração. |
| etica-104 | OK | Art. 41, II, literal (TCLE para uso de dados ou termo de liberação de imagem). Sem alteração. |
| etica-107 | OK, com ressalva | A cópia do DOU (BVS SES-SP) confirma a Res. 552/2022: Art. 4º, II revoga *"os artigos 37 e 39"*; Art. 2º dá ao Art. 9º, VII a redação *"cumprir os Parâmetros Assistenciais."* A Res. 561/2022 (RBPF, DOU de 30/01/2023), Art. 12, §2º, diz que o referencial *"não obriga o profissional e nem mesmo deverá atribuir responsabilidade ético-disciplinar"*, o que é coerente com a pauta. Atenção: o resumo da página consolidada do normasbrasil dá os Arts. 36 a 39 como revogados, o que conflita com o DOU; vale o DOU (só 37 e 39). **NÃO VERIFICADO**: a redação original do Art. 39 ("preço ínfimo" = abaixo do Referencial). |
| regulacao-102 | OK | Res. 464/2016, Art. 1º, a, b, c, literal no normasbrasil e citado no Parecer CREFITO-4 nº 002/2025. Sem revogação encontrada. Nota opcional: a lei hoje chama "aposentadoria por invalidez" de "aposentadoria por incapacidade permanente" (EC 103/2019); a norma usa o nome antigo. |
| regulacao-106 | OK | Res. 444/2014, Anexo II, Quadro 1: 2 consultas/h e 12 pacientes por turno de 6 h. Cuidado de redação: a norma diz "quantitativo de pacientes assistidos por turno", sem "até"; o "até" do tema e o "atende" do fato são interpretação. |
| regulacao-107 | OK, parcial | Anexo III, Quadro 1: 1 consulta/h e 6 pacientes por turno. **NÃO VERIFICADO**: o qualificador "cuidados mínimos, intermediários ou semi-intensivos". |
| pilates-101 | OK | Anexo II, Quadro 5: 1 consulta/h e *"Grupo de 6 clientes/pacientes por hora"*. |
| quiropraxia-osteopatia-104 | OK | Anexo II, Quadro 3: 2 consultas/h e 8 pacientes por turno. Não achei norma que substitua os Parâmetros. As Res. 610/2025 (CBDF-1) e 630/2025 (títulos de especialista) não tocam neles. |
| evid-005 | OK | Studenski 2011, conferido na MitoFit: 34.485 participantes, 9 coortes, 17.528 mortes, HR 0,88 (0,87–0,90) por 0,1 m/s, 19–87% (homens) e 35–91% (mulheres) aos 75 anos. |
| evid-006 | OK, com ressalva | O comunicado da OMS de 07/12/2023 cita tração e cintas, coletes e suportes contra o uso de rotina e *"14 interventions that are not recommended"*. A Healio confirma ultrassom terapêutico e TENS. Ressalva: as aspas em 'podem ser oferecidos' não reproduzem a redação literal da OMS ("recommends"/condicional). Tirar as aspas ou citar a redação original. |
| evid-007 | OK | Correia 2021, conferido no OUCI: 582 adultos de 18–65 anos, CROM, em pé OR 1,00 (0,98–1,02), *"not associated"*. Afiliação UNISUAM coerente com o repositório da UNISUAM, mas não lida no artigo. |
| evid-008 | OK | Leagle: S.D.N.Y., 19/10/2000, juíza Cedarbaum, 120 F. Supp. 2d 286. Stites: *"generic"* e *"directed the ... USPTO to cancel the marks"*. |
| evid-009 | OK | ATSU: *"founded in Kirksville in 1892"*; *"first class of five women and 16 men ... graduated in 1894"*. AACOM (2026): *"six women alongside 15 men"*. A divergência já está registrada no fato. |
| evid-010 | OK | Johnson, J Chiropr Humanit 2020 (PMC8074684): data atribuída por Palmer (18/09/1895) e contestada (*"may have been on a different day or even the following year"*); *"deaf for 17 years"*. O depoimento do próprio Lillard não foi conferido por mim. |
| evid-011 | OK | Hupperets 2009, conferido no PEDro: 522 participantes, 12–70 anos, até 2 meses após a entorse, 56/256 x 89/266, RR 0,63 (0,45–0,88), *"35% reduction"*, NNT 9. |
| evid-012 | CORRIGIR (menor) | Lawford 2024 (resumo oficial da Cochrane Library): 139 ensaios, 12.468 participantes, dor 13,14 ("may"), função 12,53 ("likely"), sem diferença entre tipos. Os efeitos são **"immediately post-intervention"**, e o fato omite o momento. Acrescentar "logo após a intervenção". |

---

## Fontes efetivamente lidas

- Bachmann 2003: https://www.aafp.org/pubs/afp/issues/2003/0815/p745a.html · https://www.qxmd.com/r/12595378 · https://dare.uva.nl/id/a87bd999-7ac9-4035-b4a7-6f309045a5f6
- Leong 2015: https://ecommons.aku.edu/pakistan_fhs_mc_chs_chs/338 · https://update.library.uitm.edu.my/Record/2-s2.0-84937641667/Description
- Lauersen 2014: https://search.pedro.org.au/search-results/record-detail/39522 · https://nih.brage.unit.no/nih-xmlui/bitstream/handle/11250/279729/AndersenBJSM2014.pdf?sequence=1
- van Dyk 2019: https://search.pedro.org.au/search-results/record-detail/56553 · https://bjsm.bmj.com/content/53/21/1362.abstract · QxMD 30808663
- Sherrington 2019: https://read.qxmd.com/read/30703272/exercise-for-preventing-falls-in-older-people-living-in-the-community · https://www.cochrane.org/CD012424/EXERCISE_exercise-preventing-falls-older-people-living-community
- Malta 2022: https://scielosp.org/pdf/rbepid/2022.v25/e220032/pt
- CDC STEADI: https://www.nj.gov/humanservices/doas/forms/STEADI-Assessment-30Sec-508.pdf · https://stacks.cdc.gov/view/cdc/157303/cdc_157303_DS1.pdf
- Chiu 2015: https://www.qxmd.com/r/25009200 · https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_proquest_miscellaneous_1652453727
- Thorborg 2017: https://search.pedro.org.au/search-results/record-detail/49470 · https://vbn.aau.dk/en/publications/effect-of-specific-exercise-based-football-injury-prevention-prog
- Sadigursky 2017: https://doaj.org/article/00aad083476b47949ba9852a60d5eecc
- FIFA 11+: https://lida.sport-iat.de/ta/Record/4036295?lng=en · https://cdn3.sportngin.com/attachments/document/0113/0197/FIFA11-PLUS-Ref-Manual.pdf
- Sihvonen 2013: https://epistemonikos.org/en/documents/41e1bfd9ac7188cf118786af1c21811976dc6e6d · https://about.ebsco.com/clinical-decisions/dynamed-solutions/about/ebm-focus/arthroscopic-partial-meniscectomy-does-not
- Rathleff 2015: https://www.naturalmedicinejournal.com/journal/strength-training-regimen-effective-treating-plantar-fasciitis · texto completo na Braceworks (braceworks.ca, PDF de 2016/04) · https://search.pedro.org.au/search-results/record-detail/42802
- Coombes 2013: https://core.ac.uk/download/15156994.pdf · https://www.sciencedaily.com/releases/2013/02/130205162119.htm
- Steffens 2016: https://chiro.org/LINKS/ABSTRACTS/Prevention_of_Low_Back_Pain.shtml · https://braceworks.ca/wp-content/uploads/2016/01/Preventio-of-Low-Back-Pain-JAMA-2015.pdf
- Nascimento 2018: https://repositorio.ufmg.br/handle/1843/46540
- Beard 2018: https://eprints.whiterose.ac.uk/186506 · https://evidence.nihr.ac.uk/alert/a-surgical-procedure-for-shoulder-pain-is-less-effective-than-previously-thought
- Barry 2014: https://pure.ul.ie/en/publications/is-the-timed-up-and-go-test-a-useful-predictor-of-risk-of-falls-i/
- Parreira 2014: https://search.pedro.org.au/search-results/record-detail/39922 · https://researchers.mq.edu.au/en/publications/kinesio-taping-to-generate-skin-convolutions-is-not-better-than-s/
- Res. COFFITO 424/2013: https://www.normasbrasil.com.br/norma/resolucao-424-2013_257114.html · programa UFG 2026: https://files.cercomp.ufg.br/weby/up/1332/o/2026_2_IPT0234_-_%C3%89TICA_E_FISIOTERAPIA.pdf
- Res. 552/2022 (DOU): https://ses.sp.bvs.br/wp-content/uploads/2022/08/U_RS-COFFITO-552_120822.pdf
- Res. 561/2022 (DOU): https://ses.sp.bvs.br/wp-content/uploads/2023/01/U_RS-COFFITO-561_280322.pdf · Cartilha RBPF: https://crefito4.org.br/site/wp-content/uploads/2024/02/Cartilha_RBPF_2024_.pdf
- Res. 630/2025: https://www.legisweb.com.br/legislacao/?id=483613 · Res. 610/2025: https://www.normasbrasil.com.br/norma/resolucao-610-2025_475412.html
- Res. 464/2016: https://www.normasbrasil.com.br/norma/resolucao-464-2016_324103.html · https://crefito4.org.br/site/wp-content/uploads/2025/05/Parecer-002-2025-Parecer-sobre-Prerrogativa-Profissional-Atestados-Laudos-e-Pareceres.pdf
- Res. 444/2014: https://www.normasbrasil.com.br/norma/resolucao-444-2014_275977.html
- Res. 414/2012: https://www.normasbrasil.com.br/norma/resolucao-414-2012_240928.html
- Hupperets 2009: https://search.pedro.org.au/search-results/record-detail/23915
- Studenski 2011: https://mitofit.org/index.php/Studenski_2011_JAMA
- Lawford 2024: https://cochranelibrary.com/cdsr/doi/10.1002/14651858.CD004376.pub4/pdf/CDSR/CD004376/CD004376_abstract.pdf
- OMS 2023: https://www.who.int/news/item/07-12-2023-who-releases-guidelines-on-chronic-low-back-pain · https://www.healio.com/news/primary-care/20231220/new-who-guidance-on-lower-back-pain-advises-against-tens-lumbar-support
- Correia 2021: https://ouci.dntb.gov.ua/works/4ORvgg27
- Pilates: https://leagle.com/decision/2000406120fsupp2d2861381 · https://www.stites.com/resources/trademarkology/pilates-a-deep-stretch-of-trademark-law/
- ATSU: https://www.atsu.edu/contact/history · AACOM 2026: https://www.aacom.org/news-reports/news/2026/09/08/the-women-who-walked-through-still's-door
- Johnson 2020: https://pmc.ncbi.nlm.nih.gov/articles/PMC8074684
