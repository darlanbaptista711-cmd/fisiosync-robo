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

  const video = await readFile(VIDEO);
  log(`video: ${VIDEO} (${(video.length / 1e6).toFixed(1)} MB)`);

  // 1) container
  const c = await graph(`${ID}/media`, {
    media_type: "REELS",
    upload_type: "resumable",
    caption: legenda,
    share_to_feed: "true",
    thumb_offset: String(roteiro.capa_ms ?? 3000),
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
