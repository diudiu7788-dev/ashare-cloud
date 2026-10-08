# A-share multi-source cloud service v0.2

Replaces Eastmoney-only AKShare collection with **Tencent Finance (HTTP)** and **mootdx (TDX TCP)** fallback. Tencent is tried first; mootdx is tried if it fails. Both need actual cloud connectivity testing.

## Deploy to existing Render service
Replace `main.py`, `requirements.txt`, `Dockerfile`, and `README.md` in the existing GitHub repository root, commit changes, and wait for Render automatic redeployment. Dockerfile remains unchanged.

## Test
- `/health`: FastAPI is alive; **not** proof of live quote data.
- `/v1/sources`: tries Tencent and mootdx independently and reports connection errors or sample China Petroleum quote.
- `/v1/market`: watchlist snapshot ONLY, **not** full-market breadth or sector statistics.
- `/v1/stock/600641`: individual quote.
- `/v1/sectors`: HTTP 501 until a verifiable sector feed is implemented.

All data has `collected_at_beijing` but **quote_freshness_verified=false**. Inspect `quote_time_raw` when available; do not assume it is fresh just because collection succeeded. Tencent quote fields are parsed from its unofficial protocol, which may change. Tencent volume is reported in hands and turnover in 10k CNY; mootdx volume units are source-specific. This is an experimental, unofficial data service, not a trading execution system. The service may not be reachable by ChatGPT's web browsing tool even if it is publicly available in a normal browser.

Set `CACHE_SECONDS=45` on Render if desired. Public endpoints are unauthenticated: do not add account credentials, holdings, or private information.


## v0.3 MCP integration
Deploy these updated files to the same Render service. Existing REST endpoints remain.
MCP endpoint: `https://ashare-cloud.onrender.com/mcp/` (Streamable HTTP, no authentication).
The endpoint is read-only but publicly accessible. Only use public market data; do not add account secrets.
After deployment, connect it from ChatGPT Plugins > Add custom MCP server > URL.
MCP tools: get_ashare_watchlist, get_ashare_stock, get_ashare_source_status.
Test using MCP initialize/tools/list rather than opening /mcp/ in a browser.
