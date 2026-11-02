/**
 * Publica um Reels no Instagram pela Graph API.
 *
 * Usa o UPLOAD DIRETO (resumable) da Meta: o arquivo sobe do proprio
 * runner, sem precisar hospedar o video numa URL publica.
 *
 * Fluxo:
 *   1. cria o container REELS com a legenda
 *   2. sobe o mp4 para rupload.facebook.com
 *   3. espera o Instagram processar (status_code FINISHED)
 *   4. publica e grava em reels/historico-reels.json
 *
 * Trava contra post duplicado: se o mesmo roteiro ja foi publicado,
 * nao publica de novo, a nao ser com FORCAR=1.
 *
 * Ambiente: IG_USER_ID, IG_ACCESS_TOKEN, VIDEO, ROTEIRO
 */

import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";

const GRAPH = "https://graph.facebook.com/v23.0";
const ID = process.env.IG_USER_ID;
const TOKEN = process.env.IG_ACCESS_TOKEN;
const VIDEO = process.env.VIDEO;
const ROTEIRO = process.env.ROTEIRO;
const HIST = "reels/historico-reels.json";

const log = (m) => console.log(`[publicar] ${m}`);
const morrer = (m) => {
  console.error(`\n[publicar] ABORTANDO: ${m}\n`);
  process.exit(1);
};
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

async function graph(caminho, params = {}, metodo = "POST") {
  const corpo = new URLSearchParams({ ...params, access_token: TOKEN });
  const url = metodo === "GET" ? `${GRAPH}/${caminho}?${corpo}` : `${GRAPH}/${caminho}`;
  const r = await fetch(url, metodo === "GET" ? {} : { method: "POST", body: corpo });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) {
    const e = j.error || {};
    if (e.code === 190) morrer("o token do Instagram expirou ou foi revogado (erro 190).");
    morrer(`Graph API ${caminho}: HTTP ${r.status} ${e.message || JSON.stringify(j).slice(0, 300)}`);
  }
  return j;
}

/**
 * Trava pela FONTE DA VERDADE: o proprio Instagram.
 *
 * Em 02/11/2026 o Reels das 20h saiu duas vezes (20:00 e 20:03): uma
 * largada de reserva ficou na fila e comecou com uma copia do historico
 * anterior ao registro do primeiro post. O historico em arquivo pode
 * estar velho; o perfil no Instagram nao.
 *
 * Devolve o link do Reels igual publicado nas ultimas 36h, ou null.
 */
async function jaNoInstagram(legenda) {
  const r = await fetch(`${GRAPH}/${ID}/media?` + new URLSearchParams({
    fields: "caption,timestamp,media_product_type,permalink", limit: "15",
    access_token: TOKEN }));
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) {
    // sem conseguir conferir, NAO publica: duplicado e pior que atraso
    morrer(`nao consegui conferir o perfil antes de publicar: ${JSON.stringify(j.error || {}).slice(0, 200)}`);
  }
  const inicio = legenda.slice(0, 80);
  const limite = Date.now() - 36 * 3600 * 1000;
  const igual = (j.data || []).find((m) =>
    m.media_product_type === "REELS" &&
    Date.parse(m.timestamp) >= limite &&
    (m.caption || "").trim().slice(0, 80) === inicio);
  return igual ? igual.permalink || igual.timestamp : null;
}

/**
 * Momento da capa: no meio do bloco da resposta, quando o numero ja
 * terminou de contar. Com tempo fixo (3,8s) a capa do Reels "oito itens"
 * pegou a contagem no 7.
 */
function capaMs(roteiro) {
  try {
    const dur = parseFloat(execFileSync("ffprobe", ["-v", "error", "-show_entries",
      "format=duration", "-of", "default=nw=1:nk=1", VIDEO]).toString());
    const fps = 30, total = Math.round(dur * fps), fecho = Math.round(2.2 * fps);
    const corpo = total - fecho;
    const [pa, pb] = roteiro.proporcoes ?? [0.3, 0.38];
    const a = Math.round(corpo * pa), b = Math.round(corpo * pb);
    // a contagem acaba 14 quadros depois do inicio do bloco
    const quadro = a + Math.max(24, Math.round(b * 0.6));
    return Math.round((quadro / fps) * 1000);
  } catch {
    return roteiro.capa_ms ?? 3000;
  }
}

async function lerHistorico() {
  try { return JSON.parse(await readFile(HIST, "utf-8")); } catch { return []; }
}

async function main() {
  for (const [k, v] of Object.entries({ IG_USER_ID: ID, IG_ACCESS_TOKEN: TOKEN, VIDEO, ROTEIRO })) {
    if (!v) morrer(`falta ${k} no ambiente.`);
  }
  const roteiro = JSON.parse(await readFile(ROTEIRO, "utf-8"));
  const legenda = (roteiro.legenda || "").trim();
  if (!legenda) morrer("o roteiro nao tem legenda.");
  if (legenda.length > 2200) morrer(`legenda com ${legenda.length} caracteres; o limite e 2200.`);

  const hist = await lerHistorico();
  if (hist.some((h) => h.titulo === roteiro.titulo) && process.env.FORCAR !== "1") {
    log(`"${roteiro.titulo}" ja foi publicado. Nada a fazer.`);
    return;
  }

  const noAr = await jaNoInstagram(legenda);
  if (noAr && process.env.FORCAR !== "1") {
    log(`este Reels ja esta no perfil (${noAr}). Nao vou publicar de novo.`);
    return;
  }

  const video = await readFile(VIDEO);
  log(`video: ${VIDEO} (${(video.length / 1e6).toFixed(1)} MB)`);

  // 1) container
  const c = await graph(`${ID}/media`, {
    media_type: "REELS",
    upload_type: "resumable",
    caption: legenda,
    share_to_feed: "true",
    thumb_offset: String(capaMs(roteiro)),
  });
  log(`container criado: ${c.id}`);

  // 2) upload direto
  const destino = c.uri || `https://rupload.facebook.com/ig-api-upload/v23.0/${c.id}`;
  const up = await fetch(destino, {
    method: "POST",
    headers: {
      Authorization: `OAuth ${TOKEN}`,
      offset: "0",
      file_size: String(video.length),
    },
    body: video,
  });
  const upj = await up.json().catch(() => ({}));
  if (!up.ok || upj.success === false) {
    morrer(`upload recusado: HTTP ${up.status} ${JSON.stringify(upj).slice(0, 300)}`);
  }
  log("video enviado, aguardando o Instagram processar");

  // 3) processamento: a Meta pede consulta espacada, ate uns minutos
  let status = "";
  for (let i = 0; i < 30; i++) {
    await espera(10000);
    const s = await graph(c.id, { fields: "status_code,status" }, "GET");
    status = s.status_code;
    log(`  status: ${status}`);
    if (status === "FINISHED") break;
    if (status === "ERROR" || status === "EXPIRED") {
      morrer(`o Instagram recusou o video: ${s.status || status}`);
    }
  }
  if (status !== "FINISHED") morrer("o processamento passou de 5 minutos.");

  // 4) publica
  const pub = await graph(`${ID}/media_publish`, { creation_id: c.id });
  const info = await graph(pub.id, { fields: "permalink" }, "GET").catch(() => ({}));
  log(`PUBLICADO: ${info.permalink || pub.id}`);

  hist.push({
    data: new Date().toISOString(),
    // dia em Brasilia: e por ele que a trava de "ja publicou hoje" confere
    data_brasilia: new Date(Date.now() - 3 * 3600 * 1000).toISOString().slice(0, 10),
    janela: process.env.JANELA_REELS || "",
    titulo: roteiro.titulo,
    tipo: roteiro.tipo || "dica",
    media_id: pub.id,
    link: info.permalink || "",
    fonte: roteiro.fonte || "",
  });
  await writeFile(HIST, JSON.stringify(hist, null, 2), "utf-8");
}

main().catch((e) => morrer(e.stack || e.message));
