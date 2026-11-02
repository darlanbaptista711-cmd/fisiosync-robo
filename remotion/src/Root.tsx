import { Composition } from "remotion";
import { ReelDica } from "./ReelDica";
import dados from "../public/dados-reel.json";

// So o Reel de conhecimento, fundo branco. A duracao vem do audio: o
// reels/narrar.mjs mede a narracao e grava em dados-reel.json.
export const RemotionRoot: React.FC = () => (
  <Composition
    id="reel-dica"
    component={ReelDica}
    durationInFrames={dados.framesTotal}
    fps={dados.fps}
    width={1080}
    height={1920}
  />
);
