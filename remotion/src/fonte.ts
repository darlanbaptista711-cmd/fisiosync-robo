/**
 * Carrega a fonte da marca e SEGURA o render ate ela estar pronta.
 *
 * POR QUE ISTO EXISTE
 *
 * O primeiro Reel de dica piscava. Comparando quadro a quadro, o 80
 * saiu sem o texto, com um buraco branco no lugar, e o 81 saiu
 * completo. Dezenas de quadros assim, alternando, entre 2,6s e 4,8s.
 *
 * Causa: loadFont() comeca a baixar a fonte e devolve na hora. O
 * Remotion renderiza varios quadros em paralelo, e os que chegam antes
 * do download terminar sao pintados sem ela. Como cada processo tem o
 * seu proprio tempo, uns saem certos e outros nao: isso e o pisca-pisca.
 *
 * delayRender() diz ao Remotion para nao comecar enquanto a fonte nao
 * terminar de carregar; continueRender() libera. Sem este par, qualquer
 * fonte da web e sorteio.
 */

import { continueRender, delayRender } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const espera = delayRender("carregando a fonte da marca");

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["400", "500", "600", "700", "800", "900"],
  subsets: ["latin"],
});

waitUntilDone()
  .then(() => continueRender(espera))
  .catch((e) => {
    // libera mesmo em caso de erro: melhor um video com fonte de
    // reserva do que um render travado para sempre
    console.error("[fonte] falhou o carregamento:", e);
    continueRender(espera);
  });

export const FONTE = fontFamily;
