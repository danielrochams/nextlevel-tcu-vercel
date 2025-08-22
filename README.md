
NextLevel TCU Validator — Vercel (Serverless)
Como usar
1) Faça login no Vercel e importe este repositório/pasta.
2) Confirme que a pasta tem a subpasta /api com index.py e requirements.txt na raiz.
3) Deploy. O endpoint ficará disponível em:
   https://SEU-PROJ.vercel.app/health
   https://SEU-PROJ.vercel.app/check?numero=1507&ano=2024

Arquivos
/api/index.py  -> app FastAPI (ASGI) com rotas /health e /check
requirements.txt -> dependências
vercel.json -> força runtime python3.12 (serverless)

Variáveis de ambiente opcionais
PAGE_SIZE (padrão 1000)
MAX_PAGES (padrão 200)
HTTP_TIMEOUT (padrão 30)
