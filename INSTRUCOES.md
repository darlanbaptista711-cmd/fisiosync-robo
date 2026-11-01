# Instruções permanentes do projeto — FisioSync

Este arquivo vale para todas as criações futuras. Quem for mexer no robô,
pessoa ou IA, lê isto primeiro.

## Onde estão as referências aprovadas

Pasta `referencias/`. As imagens `aprovada_*.png` são enviadas **dentro da
requisição de geração**, como imagem de referência, e não citadas por
caminho no texto do prompt. Citar caminho não funciona.

O arquivo `referencias/REFERENCIAS.md` descreve cada uma: o que observar,
o que não copiar, os problemas antigos a evitar e os critérios para uma
peça ser considerada pronta.

Para registrar uma peça nova como referência:

```
python aprovar.py gerado\<arquivo>.png "o que funcionou nesta peça"
```

O fluxo envia as duas primeiras em ordem alfabética. Apague as que não
representam mais o padrão, em vez de acumular.

## O processo, na ordem

1. Escolher o tema, olhando `historico.json` para não repetir.
2. Definir a mensagem principal.
3. Pensar em três conceitos visuais distintos e escolher o mais claro.
   Escrever o conceito em uma frase. "Objetos 3D premium" não é conceito.
4. Escolher o layout entre os cinco de `layouts.py`, de acordo com o
   conceito.
5. Escrever o prompt visual específico, com elemento principal, função de
   cada elemento secundário, relação entre eles, enquadramento, escala,
   espaço negativo, materiais, iluminação, sombras e o que evitar.
6. Gerar a ilustração ou fotografia, enviando as referências aprovadas.
7. Compor texto, logo, selos e site por código, com arquivos oficiais.
8. Conferir a arte em tamanho de celular, contra a lista de critérios.

Não reaproveitar prompt genérico trocando só o nome do tema.

## O que é fixo

- Fundo branco puro `#FFFFFF`
- Ciano `#18B7D8`, azul-marinho `#0B2948`, cinza-claro `#E8EEF2`
- A marca é feminina: **a FisioSync**
- Logo oficial de `logo.png`, nunca redesenhada
- Selos oficiais de `selo_google_play.png` e `selo_app_store.png`
- Em toda peça: logo, "Teste grátis por 7 dias",
  "Disponível no Google Play e na App Store.", os dois selos e
  `app.fisiosync.com.br`
- Feed 1080x1350 com margem de 80. Story 1080x1920 com 80 nas laterais,
  250 no topo e 350 na base.
- Produção em 2160x2700 e 2160x3840, reduzindo proporcionalmente.

### Arquivos por peça: dois, não três

- `*_2160x2700.png` ou `*_2160x3840.png` — produção, sem perda, para
  arquivar e reaproveitar.
- `*_1080x1350.jpg` ou `*_1080x1920.jpg` — publicação. **A API do
  Instagram só aceita JPEG**, então é este que sobe.

Não gerar PNG de 1080: ele não é publicado nem serve de arquivo, porque
o de 2160 já cobre isso. Era só peso em disco.

## Famílias de conteúdo e a mistura

O banco tem três famílias. O sorteio garante **1 post a cada 3 fora da
gestão** (`CICLO_FAMILIA` em `pautas.py`):

| família | o que é | fato obrigatório |
|---|---|---|
| `gestao` | dor de rotina da clínica: faltas, agenda, prontuário, dinheiro | não |
| `regulacao` | o que a norma exige sobre registro, guarda e sigilo | **sim** |
| `carreira` | decisões de profissão: autônomo, primeiro consultório, volume | não |

### Conteúdo factual não se escreve de cabeça

Pauta de `regulacao` carrega no próprio banco o campo **`fato`** (o
texto conferido) e **`fonte`** (a norma). A IA escreve **em volta** do
fato; ela nunca é a origem dele.

Três travas, nesta ordem:

1. Pauta de `regulacao` sem `fato` e `fonte` preenchidos **não entra no
   sorteio** (`_tem_fato` em `pautas.py`).
2. O prompt entrega o fato e proíbe citar qualquer outro número, ano,
   prazo, percentual ou artigo de lei. Pauta sem fato proíbe número de
   qualquer tipo.
3. Antes de montar a arte, `conferir_numeros()` varre título, apoio e
   legenda. Número que não está no fato nem na lista da casa dispara
   uma reescrita; se insistir, **a peça não é publicada**.

Também proibido neste tipo de post: dizer que a FisioSync garante
conformidade legal. O software organiza o registro; quem responde pela
norma é o profissional.

Para acrescentar pauta de regulação: confira o fato em **fonte oficial**
(site do COFFITO, Planalto), escreva `fato` e `fonte`, e só então
cadastre. Fato conferido em blog não serve.

## Texto cortado: nunca

Em 01/11/2026 foi publicado um post cujo apoio terminava em **"e deixar
claras as condições do"**. Frase cortada no meio, no ar, no perfil.

A causa era `quebrar(...)[:maximo]` dentro de `titulo()` e `apoio()`:
o texto era quebrado em linhas e as linhas que sobravam eram **jogadas
fora em silêncio**. A arte ficava bonita e mentirosa.

Regra permanente, nesta ordem:

1. **O corpo diminui até o texto caber inteiro.** É o que faz
   `LY.caber()`, que reduz o tamanho da fonte em passos de 1 até as
   linhas caberem no espaço.
2. **Se não couber nem no menor corpo, a peça não é publicada.**
   `LY.caber()` levanta `TextoNaoCabe`, o `postador.py` aborta com erro
   e a janela continua pendente — a próxima tentativa gera outro texto.
3. **Nenhum caminho do código corta texto para caber.** Se aparecer um
   `[:n]` novo em cima de `quebrar()`, é bug.

Antes disso, na geração: o apoio é limitado a 14 palavras e 110
caracteres no prompt, e `encurtar()` apara o que passar — sempre no fim
de uma frase ou de uma oração, nunca no meio de uma, e sempre deixando
pontuação final.

Publicar atrasado é aceitável. Publicar cortado, não.

## O que é proibido

- Placeholder de selo, selo desenhado, logo inventada
- Black Friday, preço, desconto ou cupom neste fluxo orgânico
- Inventar tela, recurso, integração, depoimento, estatística ou resultado
- Sugerir que a evolução por áudio dispensa revisão profissional
- Orientação clínica, protocolo ou promessa de tratamento
- Dado real de paciente
- "Comente SIM", "marque três amigos" e pedidos artificiais
- Mais de uma chamada para ação na mesma peça

## Tratamento visual

Não é obrigatório usar fotografia ultrarrealista. A referência aprovada é
ilustração 3D publicitária. Escolher por peça, entre os seis tratamentos de
`ESTILOS_VISUAIS` no `postador.py`, o que comunica melhor a ideia.

Qualidade não vem de escrever "premium", "4K" ou "ultrarrealista". Vem de
especificar enquadramento, materiais, iluminação, sombras e composição.

## Estrutura do código

- `marca.py` — só o que nunca muda: cores, textos, logo, selos, margens
- `layouts.py` — as cinco composições e o espaço negativo que cada uma exige
- `molde.py` — escolhe o layout e monta a peça
- `postador.py` — conteúdo, geração, publicação e histórico
- `humanizador.py` — limpa a legenda e aponta o que a IA deve reescrever
- `referencias/` — padrão de qualidade aprovado
- `historico.json` — tema, objetivo, estilo, layout e conceito de cada post

## Janelas de publicação

Duas por dia, em horário de Brasília:

- **manhã**, das 10h às 16h, alvo 12h
- **tarde**, das 17h às 23h, alvo 18h30

O agendador do GitHub é melhor esforço, não promessa: em 31/10/2026 ele
atrasou a janela da manhã em quase quatro horas e pulou a da tarde. Por
isso o workflow **tenta várias vezes dentro de cada janela**, e quem
decide publicar é o `postador.py`: se a janela de hoje já tem post
`publicado` no histórico, ele encerra em segundos, sem gerar imagem, sem
chamar API e sem gastar pauta.

Consequência prática: o horário exato pode variar, mas **sai um post por
janela, todo dia**. Nunca dois.

A trava não vale para `--previa`, `--tema` nem `--brief`: esses são
comandos manuais e sempre rodam.

## Histórico editorial

`historico.json` guarda, por publicação: data, **janela**, tema,
**pauta**, **eixo**, público, situação, mensagem, chamada, conceito,
composição, estilo, objetivo, arquivos e **status**.

`tema` é o título reescrito pela IA. `pauta` é a frase original do banco
e `eixo` é o assunto dela. **Essa distinção não é detalhe.** Enquanto o
histórico guardava só o `tema`, o banco nunca reconhecia a pauta de
volta: nada era marcado como usado, o rodízio de eixo nunca saía do
lugar, e em 31/10/2026 as duas publicações do dia saíram da **mesma
pauta** com títulos diferentes.

Rodízio: antes de sortear, o robô olha o `eixo` dos **6 últimos** posts e
prefere o eixo que está há mais tempo sem aparecer. Com 8 eixos e 2 posts
por dia, isso cobre os três últimos dias.

Status possíveis: `rascunho`, `aprovado`, `publicado`, `rejeitado`.

- Prévia grava como `rascunho`.
- Publicação grava como `publicado`.
- **`aprovado` só o Darlan marca.** O robô nunca se autoaprova. A revisão
  interna dele é apenas a lista de critérios; aprovação é decisão humana.

Feed e story da mesma publicação compartilham **um único registro**. A
correção de uma peça rejeitada pertence ao registro original.

Antes de planejar, comparar o **significado** da proposta com o histórico,
não só o título. Sinônimo, título novo ou troca de objeto não é tema novo.
Várias versões de "organize sua agenda" são o mesmo tema.

Se não houver tema novo sustentado pelas informações confirmadas, dizer
isso. Não inventar funcionalidade para encher calendário.

## Padrão travado em 31/10/2026

As peças `aprovada_02_padrao-feed.png` e `aprovada_03_padrao-story.png`
foram aprovadas pelo Darlan e definem o padrão obrigatório.

**A ordem dos elementos é sempre esta, nos dois formatos:**

1. Logo oficial, centralizada no topo. Sempre primeiro.
2. Sobretítulo curto, em caixa alta espaçada.
3. Chamada em duas cores, azul-marinho e ciano.
4. Apoio curto.
5. Ilustração com os efeitos em ciano atrás.
6. Teste grátis por 7 dias.
7. Selos oficiais, disponibilidade e site.

Só dois layouts entram no sorteio automático: `calibrado`, com
ilustração, e `tipografico`, quando a mensagem funciona só com texto.
Os outros cinco continuam no código, mas fora da escolha, porque
quebram essa ordem. O `detalhe`, por exemplo, põe a foto antes da logo.

O story não é o feed esticado: mesma ordem, composição própria.

## Logo: regra permanente

A logo oficial fica **sempre centralizada no topo**, no centro horizontal da
arte inteira, acima da chamada. Nunca no canto esquerdo ou direito.

- Centralizada pelo **conteúdo visível**: as margens transparentes do
  arquivo são cortadas antes de medir, senão a centralização sai torta.
- Largura entre **35% e 42%** da largura da arte. O padrão é 38%, na
  constante `LOGO_LARGURA` do `layouts.py`.
- Símbolo, lettering, assinatura Gestão Inteligente, cores e proporções
  preservados. Nenhum filtro sobre a logo ou sobre os selos.
- No story, dentro da área segura, abaixo dos primeiros 250 px.
- Espaço equilibrado entre a logo e o título.

Vale para os cinco layouts. Quem implementa é a função `logo()` do
`layouts.py`, e ela ignora qualquer posição horizontal que recebe.

## Efeitos em ciano

Em `efeitos.py`. Entram **atrás** da ilustração, nunca sobre texto, logo
ou selos. Para isso, o fundo da ilustração vira transparente por
preenchimento a partir das bordas, não por limiar fixo: limiar deixa um
retângulo claro visível, que é o defeito que o cartão arredondado tinha.

Recursos disponíveis: forma orgânica suave, halo de profundidade, ondas
e linha curva.

Escolher **dois ou três** que conversem com o tema, nunca todos. Hoje a
regra automática é: forma orgânica e halo sempre, e o terceiro depende do
assunto. Ondas só entram em temas de áudio, voz ou gravação. Para os
demais, entra a linha curva.

Sem neon, brilho exagerado, confete ou partícula solta. O efeito valoriza
o objeto; se competir com ele, está forte demais.

## Famílias de composição

Escolher pela mensagem, nunca alternando mecanicamente:

- **A. Sequência visual** — poucos elementos conectados explicando um processo
- **B. Elemento principal em destaque** — um objeto dominante, texto integrado
- **C. Composição editorial** — tipografia forte com representação precisa
- **D. Conteúdo educativo** — poucos pontos úteis com ilustração de apoio
- **E. Contexto profissional** — materiais da rotina com acabamento publicitário

Centralizar é permitido e funciona. Assimetria tem que produzir equilíbrio,
não deixar metade da arte vazia.

Nunca automaticamente: imagem em cartão arredondado, duas colunas iguais,
foto isolada no topo com parágrafo institucional embaixo, ou vão vazio entre
a mensagem e o rodapé.

## Briefing pronto

Quando a direção de arte vier definida de fora, passe o arquivo:

```
python postador.py --previa --so-feed --brief brief_<nome>.json
```

O robô usa o briefing como está, sem reinventar tema, conceito ou copy.

## Quando algo falhar

Identificar o motivo e revisar conceito, geração ou composição. Ideia fraca
não se resolve aumentando resolução, nitidez ou sombra.
