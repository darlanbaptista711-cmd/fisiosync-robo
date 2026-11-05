/**
 * Reel de dica/curiosidade, fundo branco.
 *
 * Nao mostra tela do app: a mensagem e o conteudo. Mesma identidade das
 * artes do feed, fundo branco puro, ciano #18B7D8 e azul-marinho
 * #0B2948.
 *
 * O NUMERO QUE APARECE GRANDE VEM DO BANCO, NAO DA IA.
 *
 * O roteiro carrega "fato" e "fonte" conferidos em fonte oficial, e a
 * fonte e exibida na propria tela. Conteudo de curiosidade sem fonte
 * visivel e so chute com cara de autoridade, e num perfil de produto de
 * saude isso custa caro.
 *
 * Estrutura:
 *   pergunta  -> o gancho, uma duvida real de quem toca clinica
 *   resposta  -> o numero grande, com a norma escrita embaixo
 *   extra     -> um segundo fato da mesma resolucao
 *   fecho     -> logo, teste gratis e site
 */

import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import dados from "../public/dados-reel.json";
import { FONTE as fontFamily } from "./fonte";

const CIANO = "#18B7D8";
const MARINHO = "#0B2948";
const CINZA = "#E8EEF2";
const BRANCO = "#FFFFFF";

/** Forma organica em ciano, atras do texto. Nunca por cima. */
const Forma: React.FC<{ y?: number; tamanho?: number; forca?: number }> = ({
  y = 0,
  tamanho = 1150,
  forca = 0.16,
}) => {
  // Deriva lenta e continua. Sem isso a forma congela depois do spring
  // e o Reel parece travado: a diferenca entre quadros vira zero.
  const frame = useCurrentFrame();
  const vai = Math.sin(frame / 26);
  return (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    <div
      style={{
        width: tamanho,
        height: tamanho,
        borderRadius: "48% 52% 55% 45% / 50% 46% 54% 50%",
        background: `radial-gradient(circle, ${CIANO} 0%, rgba(24,183,216,0) 68%)`,
        opacity: forca,
        transform: `translateY(${y + vai * 26}px) translateX(${
          Math.cos(frame / 34) * 20
        }px) scale(${1 + vai * 0.035})`,
      }}
    />
  </AbsoluteFill>
  );
};

const Palco: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Respiro de 1,5% ao longo do bloco: imperceptivel como efeito,
  // suficiente para o quadro nunca ser identico ao anterior.
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const zoom = interpolate(frame, [0, durationInFrames], [1, 1.015], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: BRANCO }}>
      <AbsoluteFill
        style={{
          // soco de camera: cada bloco entra 7% maior e assenta em 8
          // quadros, que da o "impacto" do corte
          transform: `scale(${zoom * interpolate(frame, [0, 8], [1.07, 1], {
            extrapolateRight: "clamp",
          })})`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ----------------------------- PERGUNTA ----------------------------- */

const Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const p = dados.pergunta ?? { rotulo: "", linhas: [] };
  const saida = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  return (
    <Palco>
      <AbsoluteFill style={{ opacity: saida }}>
        <Forma y={-120} forca={0.18} />
        <AbsoluteFill
          style={{
            justifyContent: "center",
            padding: "0 95px",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
            <div
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 30,
                letterSpacing: 7,
                color: CIANO,
                textTransform: "uppercase",
                opacity: spring({ frame, fps, config: { damping: 18 } }),
              }}
            >
              {p.rotulo}
            </div>
            {p.linhas.map((linha: string, i: number) => {
              const s = spring({
                frame: frame - 3 - i * 5,
                fps,
                config: { damping: 16, stiffness: 260 },
              });
              return (
                <div
                  key={linha}
                  style={{
                    fontFamily,
                    fontWeight: 900,
                    fontSize: 96,
                    lineHeight: 1.04,
                    letterSpacing: -2.5,
                    color: i === p.linhas.length - 1 ? CIANO : MARINHO,
                    opacity: s,
                    transform: `translateY(${interpolate(
                      s,
                      [0, 1],
                      [40, 0]
                    )}px)`,
                  }}
                >
                  {linha}
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    </Palco>
  );
};

/* ----------------------------- RESPOSTA ----------------------------- */

/**
 * Conta de 0 ate o numero do destaque ("5 anos" -> 0, 1, 2... 5 anos).
 * Se o destaque nao comecar com numero, mostra o texto como esta.
 */
const Contador: React.FC<{ texto: string }> = ({ texto }) => {
  const frame = useCurrentFrame();
  const m = /^(\d+)(.*)$/.exec(texto || "");
  if (!m) return <>{texto}</>;
  const alvo = Number(m[1]);
  const atual = Math.round(
    interpolate(frame, [2, 14], [0, alvo], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return (
    <>
      {atual}
      {m[2]}
    </>
  );
};

const Resposta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const r = dados.resposta ?? {
    destaque: "",
    complemento: "",
    fonte: "",
  };
  const s = spring({ frame, fps, config: { damping: 13, stiffness: 240 } });
  const texto = spring({
    frame: frame - 5,
    fps,
    config: { damping: 17, stiffness: 230 },
  });

  return (
    <Palco>
      <Forma y={-60} tamanho={1250} forca={0.2} />
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          padding: "0 90px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 26,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              // numero curto fica enorme; palavra longa ("Do paciente")
              // diminui para caber nos 900px uteis em vez de vazar da tela
              fontSize: Math.min(230, Math.floor(1500 / Math.max(1, (r.destaque || "").length))),
              lineHeight: 1,
              letterSpacing: (r.destaque || "").length > 5 ? -4 : -10,
              whiteSpace: "nowrap",
              color: CIANO,
              opacity: s,
              transform: `scale(${interpolate(s, [0, 1], [0.62, 1])})`,
            }}
          >
            <Contador texto={r.destaque} />
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: 48,
              lineHeight: 1.25,
              color: MARINHO,
              opacity: texto,
              transform: `translateY(${interpolate(texto, [0, 1], [26, 0])}px)`,
            }}
          >
            {r.complemento}
          </div>

          {/* a fonte fica na tela: dado sem origem nao sai daqui */}
          <div
            style={{
              fontFamily,
              fontWeight: 600,
              fontSize: 28,
              color: MARINHO,
              opacity: texto * 0.75,
              background: CINZA,
              padding: "18px 34px",
              borderRadius: 999,
              marginTop: 14,
            }}
          >
            {r.fonte}
          </div>
        </div>
      </AbsoluteFill>
    </Palco>
  );
};

/* ------------------------------ EXTRA ------------------------------- */

const Extra: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = dados.extra ?? { titulo: "", texto: "" };
  const s = spring({ frame, fps, config: { damping: 16, stiffness: 240 } });

  return (
    <Palco>
      <Forma y={120} tamanho={1050} forca={0.17} />
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          padding: "0 95px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 30,
            opacity: s,
            transform: `translateY(${interpolate(s, [0, 1], [38, 0])}px)`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 30,
              letterSpacing: 7,
              color: CIANO,
              textTransform: "uppercase",
            }}
          >
            {e.titulo}
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 86,
              lineHeight: 1.12,
              letterSpacing: -2,
              color: MARINHO,
              whiteSpace: "pre-line",
            }}
          >
            {e.texto}
          </div>
        </div>
      </AbsoluteFill>
    </Palco>
  );
};

/* ------------------------------ FECHO ------------------------------- */

const Fecho: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 16, stiffness: 220 } });
  const pulso = spring({
    frame: frame - 6,
    fps,
    config: { damping: 10, stiffness: 170 },
  });
  const f = dados.fecho ?? {
    chamada: "Teste grátis por 7 dias",
    site: "app.fisiosync.com.br",
  };

  return (
    <Palco>
      <Forma forca={0.14} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 36,
            opacity: s,
            transform: `scale(${interpolate(s, [0, 1], [0.9, 1])})`,
          }}
        >
          {/* frase de conclusao: o que a voz diz neste quadro (03/11/2026).
              Tela e voz andam juntas; sem ela, o quadro e so a marca. */}
          {(f as any).frase ? (
            <div
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 64,
                lineHeight: 1.12,
                color: MARINHO,
                textAlign: "center",
                maxWidth: 900,
                marginBottom: 18,
              }}
            >
              {(f as any).frase}
            </div>
          ) : null}
          {/* fonte de novo no fim (05/11/2026): quem assiste ate o final
              sai sabendo de onde veio o dado */}
          {(f as any).frase && dados.resposta?.fonte ? (
            <div
              style={{
                fontFamily,
                fontWeight: 600,
                fontSize: 27,
                color: MARINHO,
                opacity: 0.72,
                textAlign: "center",
                maxWidth: 900,
                marginBottom: 22,
              }}
            >
              Fonte: {dados.resposta.fonte}
            </div>
          ) : null}
          {/* fundo branco: a logo oficial entra direta, sem placa */}
          <Img
            src={staticFile("images/logo.png")}
            style={{ width: (f as any).frase ? 470 : 620, objectFit: "contain" }}
          />
          <div
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 50,
              color: BRANCO,
              background: CIANO,
              padding: "32px 70px",
              borderRadius: 999,
              transform: `scale(${interpolate(pulso, [0, 1], [0.82, 1])})`,
              boxShadow: `0 22px 55px rgba(24, 183, 216, 0.4)`,
            }}
          >
            {f.chamada}
          </div>
          {/* selos OFICIAIS das lojas, nunca desenhados: mesmos arquivos
              das artes do feed, na mesma altura visual */}
          <div style={{ display: "flex", gap: 22, alignItems: "center" }}>
            <Img src={staticFile("images/selo_google_play.png")}
                 style={{ height: 88, width: "auto" }} />
            <Img src={staticFile("images/selo_app_store.png")}
                 style={{ height: 88, width: "auto" }} />
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 500,
              fontSize: 30,
              color: "rgba(11, 41, 72, 0.62)",
            }}
          >
            Disponível no Google Play e na App Store.
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 42,
              color: CIANO,
            }}
          >
            {f.site}
          </div>
        </div>
      </AbsoluteFill>
    </Palco>
  );
};

/* ------------------------------- VIDEO ------------------------------ */

/** Faixa ciano que varre a tela na diagonal e esconde o corte. */
const Varredura: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const x = interpolate(frame, [0, durationInFrames], [-175, 115], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          top: "-25%",
          left: `${x}%`,
          width: "160%",
          height: "150%",
          background: `linear-gradient(90deg, rgba(24,183,216,0) 0%, ${CIANO} 30%, ${CIANO} 70%, rgba(24,183,216,0) 100%)`,
          transform: "skewX(-16deg)",
        }}
      />
    </AbsoluteFill>
  );
};

/** Barra fina no topo enchendo ate o fim: segura o olho no Reel. */
const Progresso: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: 12,
          width: `${(frame / durationInFrames) * 100}%`,
          background: CIANO,
          borderRadius: "0 8px 8px 0",
        }}
      />
    </AbsoluteFill>
  );
};

export const ReelDica: React.FC = () => {
  const total = dados.framesTotal;
  const fecho = dados.framesFecho;
  const corpo = total - fecho;
  // As proporcoes acompanham o texto: cada bloco dura o tanto que a
  // narracao leva para falar dele. Vem do roteiro.
  const [pa, pb] = (dados as any).proporcoes ?? [0.3, 0.38];
  const a = Math.round(corpo * pa);  // pergunta
  const b = Math.round(corpo * pb);  // resposta
  const c = corpo - a - b;           // extra
  const cortes = [a, a + b, a + b + c];
  const VARRE = 12;  // quadros da varredura

  // trilha baixa sob a voz e mais alta no fecho, quando a voz acaba
  const volumeTrilha = (f: number) =>
    interpolate(
      f,
      [0, 6, cortes[2], cortes[2] + 10, total - 18, total],
      [0, 0.13, 0.13, 0.3, 0.3, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

  return (
    <AbsoluteFill style={{ background: BRANCO, fontFamily }}>
      <Audio src={staticFile("audio/musica.mp3")} volume={volumeTrilha} />
      <Audio src={staticFile("audio/narracao.mp3")} />

      <Sequence durationInFrames={a + 8}>
        <Pergunta />
      </Sequence>
      <Sequence from={a} durationInFrames={b + 8}>
        <Resposta />
      </Sequence>
      <Sequence from={a + b} durationInFrames={c + 8}>
        <Extra />
      </Sequence>
      <Sequence from={a + b + c}>
        <Fecho />
      </Sequence>

      {/* em cada corte: varredura ciano + som de passagem */}
      {cortes.map((corte) => (
        <Sequence key={`v${corte}`} from={corte - VARRE / 2} durationInFrames={VARRE}>
          <Varredura />
        </Sequence>
      ))}
      {cortes.map((corte) => (
        <Sequence key={`w${corte}`} from={Math.max(0, corte - 9)}>
          <Audio src={staticFile("audio/whoosh.mp3")} volume={0.55} />
        </Sequence>
      ))}

      {/* estalo no numero e na chamada */}
      <Sequence from={a + 3}>
        <Audio src={staticFile("audio/pop.mp3")} volume={0.6} />
      </Sequence>
      <Sequence from={cortes[2] + 7}>
        <Audio src={staticFile("audio/pop.mp3")} volume={0.5} />
      </Sequence>

      <Progresso />
    </AbsoluteFill>
  );
};
