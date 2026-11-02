/**
 * Renderiza o Reel com as telas reais do app.
 *
 * O audio ENTRA no render (muted: false). O script antigo renderizava
 * mudo e dependia de um mux posterior; aqui a narracao ja faz parte da
 * composicao, entao sai pronto.
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition, openBrowser } from "@remotion/renderer";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SAIDA = process.env.SAIDA || "/tmp/reel-fisiosync.mp4";

const bundled = await bundle({
  entryPoint: path.resolve(__dirname, "../src/index.ts"),
  webpackOverride: (config) => config,
});

const browser = await openBrowser("chrome", {
  browserExecutable: process.env.PUPPETEER_EXECUTABLE_PATH ?? undefined,
  // pintura por software (SwiftShader via ANGLE): no runner sem GPU e
  // o modo que entrega o mesmo quadro toda vez. O padrao deixava,
  // de vez em quando, um quadro fotografado antes de terminar de pintar.
  chromiumOptions: { gl: "swangle" },
  chromeMode: "chrome-for-testing",
});

const composition = await selectComposition({
  serveUrl: bundled,
  id: process.env.COMPOSICAO || "reel-app",
  puppeteerInstance: browser,
});

console.log(
  `[render] ${composition.width}x${composition.height}, ` +
  `${composition.durationInFrames} frames @ ${composition.fps}fps = ` +
  `${(composition.durationInFrames / composition.fps).toFixed(1)}s`
);

await renderMedia({
  composition,
  serveUrl: bundled,
  codec: "h264",
  audioCodec: "aac",
  outputLocation: SAIDA,
  puppeteerInstance: browser,
  muted: false,
  // um processo so: sem disputa de memoria entre abas, menos quadro
  // fotografado pela metade
  concurrency: 1,
  onProgress: ({ progress }) => {
    if (Math.round(progress * 100) % 20 === 0) {
      process.stdout.write(`\r[render] ${Math.round(progress * 100)}%`);
    }
  },
});

await browser.close({ silent: true });
console.log(`\n[render] pronto: ${SAIDA}`);
