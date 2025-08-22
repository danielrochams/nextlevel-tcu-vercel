
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Query, HTTPException
import httpx
import os
import asyncio

TCU_ENDPOINT = "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos"
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "1000"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "200"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

app = FastAPI(title="NextLevel TCU Validator (Vercel)")

async def fetch_page(client: httpx.AsyncClient, inicio: int, quantidade: int):
    r = await client.get(TCU_ENDPOINT, params={"inicio": inicio, "quantidade": quantidade}, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Formato inesperado de resposta do TCU")
    return data

def norm(s: Optional[str]) -> str:
    return (s or "").strip()

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/check")
async def check(
    numero: str = Query(..., description="Número do acórdão, ex: 1507"),
    ano: str = Query(..., description="Ano do acórdão, ex: 2024"),
    colegiado: Optional[str] = Query(None, description="Colegiado esperado, ex: Plenário"),
    relator_hint: Optional[str] = Query(None, description="Trecho esperado do nome do relator"),
):
    inicio = 0
    attempts = 0
    async with httpx.AsyncClient(follow_redirects=True) as client:
        while attempts < MAX_PAGES:
            try:
                data = await fetch_page(client, inicio=inicio, quantidade=PAGE_SIZE)
            except httpx.HTTPError:
                await asyncio.sleep(min(5 + attempts, 20))
                attempts += 1
                continue

            if not data:
                break

            for item in data:
                if str(item.get("numeroAcordao")) == str(numero) and str(item.get("anoAcordao")) == str(ano):
                    hit = {
                        "ok": True,
                        "numero": str(item.get("numeroAcordao")),
                        "ano": str(item.get("anoAcordao")),
                        "colegiado": item.get("colegiado"),
                        "relator": item.get("relator"),
                        "dataSessao": item.get("dataSessao"),
                        "urlAcordao": item.get("urlAcordao"),
                        "urlPDF": item.get("urlArquivoPDF") or item.get("urlArquivo"),
                        "source": "TCU Dados Abertos",
                        "raw_json": item,
                    }
                    if colegiado and norm(colegiado).lower() not in norm(hit["colegiado"]).lower():
                        hit["ok"] = False
                        hit["reason"] = "Colegiado divergente"
                    if relator_hint and norm(relator_hint).lower() not in norm(hit["relator"]).lower():
                        hit["ok"] = False
                        hit["reason"] = "Relator divergente"
                    return hit
            inicio += PAGE_SIZE
            attempts += 1

    return {"ok": False, "reason": "Acórdão não localizado no TCU", "numero": numero, "ano": ano}
