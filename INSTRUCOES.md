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

## Histórico editorial

`historico.json` guarda, por publicação: data, tema, público, situação,
mensagem, chamada, conceito, composição, estilo, objetivo, arquivos e
**status**.

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
