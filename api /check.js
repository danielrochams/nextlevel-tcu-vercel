// /api/check.js — Vercel Serverless Function (Node.js)

const TCU_ENDPOINT = "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos"

// Permite ajuste por variável de ambiente se você quiser
const PAGE_SIZE = Number(process.env.PAGE_SIZE || 1000)
const MAX_PAGES = Number(process.env.MAX_PAGES || 200)

// pequeno utilitário para backoff
const sleep = ms => new Promise(r => setTimeout(r, ms))

export default async function handler(req, res) {
  try {
    const numero = String(req.query.numero || "").trim()
    const ano = String(req.query.ano || "").trim()
    const colegiado = String(req.query.colegiado || "").trim()
    const relatorHint = String(req.query.relator_hint || "").trim()

    if (!numero || !ano) {
      return res.status(400).json({ ok: false, reason: "Parâmetros obrigatórios: numero e ano" })
    }

    let inicio = 0
    let tentativas = 0

    while (tentativas < MAX_PAGES) {
      const url = new URL(TCU_ENDPOINT)
      url.searchParams.set("inicio", String(inicio))
      url.searchParams.set("quantidade", String(PAGE_SIZE))

      let resp
      try {
        resp = await fetch(url.toString(), { headers: { accept: "application/json" } })
      } catch {
        tentativas++
        await sleep(200 * tentativas)
        continue
      }

      if (!resp.ok) {
        tentativas++
        await sleep(200 * tentativas)
        continue
      }

      const data = await resp.json()
      if (!Array.isArray(data) || data.length === 0) break

      for (const item of data) {
        const n = String(item?.numeroAcordao ?? "")
        const a = String(item?.anoAcordao ?? "")
        if (n === numero && a === ano) {
          const hit = {
            ok: true,
            numero: n,
            ano: a,
            colegiado: item?.colegiado || null,
            relator: item?.relator || null,
            dataSessao: item?.dataSessao || null,
            urlAcordao: item?.urlAcordao || null,
            urlPDF: item?.urlArquivoPDF || item?.urlArquivo || null,
            source: "TCU Dados Abertos",
            raw_json: item
          }

          if (colegiado && !String(hit.colegiado || "").toLowerCase().includes(colegiado.toLowerCase())) {
            hit.ok = false
            hit.reason = "Colegiado divergente"
          }

          if (relatorHint && !String(hit.relator || "").toLowerCase().includes(relatorHint.toLowerCase())) {
            hit.ok = false
            hit.reason = "Relator divergente"
          }

          return res.status(200).json(hit)
        }
      }

      inicio += PAGE_SIZE
      tentativas++
    }

    return res.status(200).json({ ok: false, reason: "Acórdão não localizado no TCU", numero, ano })
  } catch (err) {
    return res.status(500).json({ ok: false, reason: "Erro interno", error: String(err) })
  }
}

