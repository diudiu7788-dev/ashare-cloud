# A-share Cloud Snapshot (prototype)

Python + AKShare + FastAPI read-only JSON API. Deploy via a Docker-compatible cloud platform (Render, Railway, Fly.io, or VPS). Choose a region that can reach Eastmoney. Note: free instances may sleep and upstream sites can rate-limit or block cloud IPs.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /health`: process health only
- `GET /v1/market`: A-share breadth and default watchlist
- `GET /v1/sectors?limit=20`: industry leaders/laggards
- `GET /v1/stock/600641`: single-stock snapshot

**Important:** `collected_at_beijing` is *server fetch time*, NOT exchange quote time. AKShare Eastmoney functions do not guarantee a verified exchange timestamp. `quote_freshness_verified` remains false. Treat market data as unverified freshness until cross-checked with a timestamped exchange/provider feed. `up_9_5pct` is a rough count, NOT an accurate limit-up count across boards and ST stocks. Turnover sum is a rough cross-sectional sum, not validated exchange total. Never publish this endpoint with sensitive credentials; add auth/rate limiting before wide exposure.

## Deployment
Create a new Docker web service from this directory/repository; set `CACHE_SECONDS=120`, expose the platform-provided `PORT`, then check `/health` and `/v1/market` independently. If `/v1/market` gives 503, try another region or upstream provider. Public read-only endpoints should be rate-limited.
