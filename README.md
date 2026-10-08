# A-share cloud v0.4 — dependency fix

Fixes the Render pip ResolutionImpossible error by removing mootdx 0.11.0 and pandas>=2.2, which were incompatible. The Tencent quote source is retained; neither pandas nor mootdx is needed by this version.

Deploy: replace the four files at the root of the existing GitHub repository (main.py, requirements.txt, Dockerfile, README.md). Keep the existing Render service and Docker deployment. Wait for Deploy live.

Check: GET /health should return status ok. GET /v1/market returns Tencent watchlist quotes. The MCP endpoint is /mcp/ and requires an MCP client; ordinary browser GET may return an MCP protocol error even if working. For MCP protocol verification, POST initialize with proper Accept headers, then call tools/list. Do not treat a browser GET as sufficient.

Limitations: this version only covers watchlist quotes, not full-market breadth or sectors. Tencent upstream may be delayed or unavailable; collected_at_beijing is not an exchange quote timestamp. /v1/sectors returns HTTP 501 intentionally.
