/**
 * Gera a narracao do Reel na ElevenLabs e mede a duracao.
 *
 * A duracao do audio manda no video: as cenas sao esticadas para caber
 * exatamente na narracao, em vez de o video ter um tamanho fixo e o
 * audio sobrar ou faltar.
 *
 * Grava:
 *   remotion/public/audio/narracao.mp3
 *   remotion/public/dados-reel.json   (roteiro + duracao de cada cena)
 *   remotion/public/images/app/*.png  (as capturas)
 */

import { execFileSync } from "node:child_process";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const RAIZ = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const CAPTURAS = path.join(RAIZ, "reels/capturas");
const PUB = path.join(RAIZ, "remotion/public");

const CHAVE = process.env.ELEVENLABS_API_KEY;
let VOZ = process.env.ELEVENLABS_VOICE_ID;
let DONO_VOZ = null;   // public_owner_id, quando a voz vem da biblioteca
const MODELO = process.env.ELEVENLABS_MODEL || "eleven_multilingual_v2";

const FPS = 30;

// Estrutura de Reel curto: gancho, demonstracao, chamada.
// O video inteiro tem que caber entre 15 e 20 segundos.
const MIN_SEG = 8;
const MAX_SEG = 15;   // pedido do Darlan: no maximo 15s, sempre
const GANCHO = 2.0;   // segundos de gancho, antes das telas
const FECHO = 2.2;    // segundos de chamada no fim

const log = (m) => console.log(`[narrar] ${m}`);
const morrer = (m) => {
  console.error(`\n[narrar] ABORTANDO: ${m}\n`);
  process.exit(1);
};

/**
 * Modelos em ordem de preferencia. O v3 e bem mais expressivo e aceita
 * marcacoes de emocao como [animado], que nao sao faladas: mudam o
 * jeito de falar. Se a conta nao tiver acesso a ele, cai para o v2
 * sozinho, sem quebrar a rodada.
 */
const MODELOS = (process.env.ELEVENLABS_MODEL || "eleven_v3,eleven_multilingual_v2")
  .split(",").map((m) => m.trim()).filter(Boolean);

function pedidoPara(modelo, texto) {
  if (modelo === "eleven_v3") {
    return {
      // a marcacao vai no comeco e vale para a fala inteira
      text: `[excited] ${texto}`,
      model_id: modelo,
      // no v3 a estabilidade e 0 (criativo), 0,5 ou 1. Criativo e o
      // mais animado. Velocidade fica com o atempo, depois.
      voice_settings: { stability: 0.0, similarity_boost: 0.8,
                        use_speaker_boost: true },
    };
  }
  return {
    text: texto,
    model_id: modelo,
    voice_settings: {
      stability: Number(process.env.VOZ_ESTABILIDADE ?? 0.25),
      similarity_boost: Number(process.env.VOZ_SIMILARIDADE ?? 0.8),
      style: Number(process.env.VOZ_ESTILO ?? 0.6),
      use_speaker_boost: true,
      // voz acelerada sempre. 1,2 e o teto da API.
      speed: Number(process.env.VOZ_VELOCIDADE ?? 1.2),
    },
  };
}

async function gerarAudio(texto, destino, jaTentouAdicionar = false, idx = 0) {
  const modelo = MODELOS[idx];
  if (!modelo) morrer("nenhum modelo de voz aceitou o pedido.");
  log(`modelo de voz: ${modelo}`);

  const r = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${VOZ}?output_format=mp3_44100_128`,
    {
      method: "POST",
      headers: { "xi-api-key": CHAVE, "Content-Type": "application/json" },
      body: JSON.stringify(pedidoPara(modelo, texto)),
    }
  );

  if (r.ok) {
    const audio = Buffer.from(await r.arrayBuffer());
    if (audio.length < 2000) morrer("o audio veio vazio.");
    await writeFile(destino, audio);
    log(`audio salvo (${modelo}), ${(audio.length / 1024).toFixed(0)} KB`);
    return;
  }

  const corpo = await r.text();
  if (r.status === 401 && !/permission/i.test(corpo)) {
    morrer("a ElevenLabs recusou a chave (401). Confira ELEVENLABS_API_KEY.");
  }

  // voz da biblioteca publica que ainda nao esta na conta
  if (!jaTentouAdicionar && DONO_VOZ && /voice.*not.*found|voice_not_found/i.test(corpo)) {
    log("voz ainda nao esta na sua conta; adicionando da biblioteca");
    const a = await fetch(
      `https://api.elevenlabs.io/v1/voices/add/${DONO_VOZ}/${VOZ}`,
      {
        method: "POST",
        headers: { "xi-api-key": CHAVE, "Content-Type": "application/json" },
        body: JSON.stringify({ new_name: `FisioSync ${VOZ.slice(0, 6)}` }),
      });
    if (!a.ok) morrer(`nao consegui adicionar a voz (HTTP ${a.status}).`);
    return gerarAudio(texto, destino, true, idx);
  }

  // qualquer outra recusa: tenta o proximo modelo da lista
  if (idx + 1 < MODELOS.length) {
    log(`${modelo} recusou (HTTP ${r.status}): ${corpo.slice(0, 160)}`);
    log(`tentando ${MODELOS[idx + 1]}`);
    return gerarAudio(texto, destino, jaTentouAdicionar, idx + 1);
  }
  morrer(`ElevenLabs devolveu HTTP ${r.status}.\n  ${corpo.slice(0, 400)}`);
}

function duracaoDe(arquivo) {
  const saida = execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    arquivo,
  ]).toString().trim();
  const s = parseFloat(saida);
  if (!Number.isFinite(s) || s <= 0) morrer("nao consegui medir o audio.");
  return s;
}

async function main() {
  if (!CHAVE) morrer("falta ELEVENLABS_API_KEY no ambiente.");
  try {
    const escolha = JSON.parse(
      await readFile(path.join(RAIZ, "reels/voz.json"), "utf-8"));
    if (escolha.voice_id) {
      VOZ = escolha.voice_id;
      DONO_VOZ = escolha.public_owner_id || null;
      log(`voz escolhida em reels/voz.json: ${escolha.nome || VOZ}`);
    }
  } catch { /* sem voz.json: usa a do cofre */ }
  if (!VOZ) morrer("falta ELEVENLABS_VOICE_ID no ambiente.");

  const arqRoteiro = process.env.ROTEIRO || "reels/roteiro.json";
  log(`roteiro: ${arqRoteiro}`);
  const roteiro = JSON.parse(
    await readFile(path.join(RAIZ, arqRoteiro), "utf-8")
  );

  await mkdir(path.join(PUB, "audio"), { recursive: true });
  await mkdir(path.join(PUB, "images/app"), { recursive: true });

  // Roteiro de dica nao usa tela do app: a mensagem e o conteudo.
  const cenas = roteiro.cenas ?? [];
  for (const cena of cenas) {
    await copyFile(
      path.join(CAPTURAS, cena.imagem),
      path.join(PUB, "images/app", cena.imagem)
    );
  }
  log(cenas.length
    ? `${cenas.length} capturas copiadas para o video`
    : "roteiro sem telas do app");

  const mp3 = path.join(PUB, "audio/narracao.mp3");
  log(`gerando narracao com a voz ${VOZ}`);
  await gerarAudio(roteiro.narracao, mp3);

  let fala = duracaoDe(mp3);

  // Se mesmo com a voz no maximo da API o video passar de 15s, acelera
  // o audio pronto com atempo, que mantem o tom da voz. Ate 25% a mais
  // ainda soa como voz rapida; passou disso, o texto e que esta longo.
  const cabe = MAX_SEG - 0.4;
  if (fala > cabe) {
    const fator = fala / cabe;
    if (fator > 1.25) {
      const palavras = roteiro.narracao.trim().split(/\s+/).length;
      morrer(`a fala tem ${fala.toFixed(1)}s e o maximo e ${MAX_SEG}s. ` +
        `Acelerar ${Math.round((fator - 1) * 100)}% estragaria a voz.\n` +
        `  Corte para umas ${Math.floor(palavras / fator)} palavras no roteiro.`);
    }
    log(`acelerando a fala ${Math.round((fator - 1) * 100)}% para caber em ${MAX_SEG}s`);
    const tmp = mp3.replace(/\.mp3$/, ".rapido.mp3");
    execFileSync("ffmpeg", ["-v", "error", "-y", "-i", mp3,
      "-filter:a", `atempo=${fator.toFixed(4)}`, "-b:a", "128k", tmp]);
    execFileSync("mv", [tmp, mp3]);
    fala = duracaoDe(mp3);
  }

  // A narracao e continua e cobre os tres blocos. O video acompanha a
  // fala: nada de video fixo com audio sobrando ou faltando.
  const total = Math.min(MAX_SEG, Math.max(fala + 0.4, GANCHO + FECHO + 3));
  const palavras = roteiro.narracao.trim().split(/\s+/).length;
  log(`narracao: ${palavras} palavras, ${fala.toFixed(1)}s`);
  log(`video: ${total.toFixed(1)}s`);

  if (total > MAX_SEG) {
    morrer(
      `o video daria ${total.toFixed(1)}s e o limite combinado e ${MAX_SEG}s.\n` +
      `  A narracao tem ${palavras} palavras. Corte para umas ` +
      `${Math.floor(palavras * (MAX_SEG - 1) / total)} no roteiro.json.`
    );
  }
  if (total < MIN_SEG) {
    morrer(
      `o video daria so ${total.toFixed(1)}s e o minimo combinado e ${MIN_SEG}s.\n` +
      `  A narracao tem ${palavras} palavras. Alongue um pouco no roteiro.json.`
    );
  }

  // O miolo e o que sobra entre o gancho e o fecho.
  const miolo = total - GANCHO - FECHO;
  if (miolo < 4) morrer(`so sobraram ${miolo.toFixed(1)}s de miolo.`);
  const porCena = cenas.length ? miolo / cenas.length : miolo;
  log(`gancho ${GANCHO}s | miolo ${miolo.toFixed(1)}s | fecho ${FECHO}s`);

  await writeFile(
    path.join(PUB, "dados-reel.json"),
    JSON.stringify(
      {
        fps: FPS,
        duracaoTotal: total,
        framesTotal: Math.round(total * FPS),
        framesGancho: Math.round(GANCHO * FPS),
        framesPorCena: Math.round(porCena * FPS),
        framesFecho: Math.round(FECHO * FPS),
        narracao: roteiro.narracao,
        gancho: roteiro.gancho ?? null,
        cenas: cenas,
        fecho: roteiro.fecho ?? null,
        pergunta: roteiro.pergunta ?? null,
        resposta: roteiro.resposta ?? null,
        extra: roteiro.extra ?? null,
        fonte: roteiro.fonte ?? "",
        proporcoes: roteiro.proporcoes ?? null,
      },
      null,
      1
    ),
    "utf-8"
  );
  log("dados-reel.json gravado");
}

main().catch((e) => morrer(e.stack || e.message));
