import os
import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Query
import akshare as ak

app = FastAPI(title='A-share Market Snapshot', version='0.1')
TZ = ZoneInfo('Asia/Shanghai')
TTL = int(os.getenv('CACHE_SECONDS', '120'))
_cache = {}
_lock = threading.Lock()

WATCH = {'600641': '先导', '600522': '中天科技', '002245': '蔚蓝锂芯'}

def snapshot(name, loader):
    now = time.monotonic()
    with _lock:
        item = _cache.get(name)
        if item and now - item['monotonic'] < TTL:
            return item['data']
    try:
        data = loader()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'{name} upstream unavailable: {type(exc).__name__}') from exc
    with _lock:
        _cache[name] = {'monotonic': time.monotonic(), 'data': data}
    return data

def stamp():
    return datetime.now(TZ).isoformat(timespec='seconds')

def records(df, columns, limit=None):
    keep = [c for c in columns if c in df.columns]
    out = df[keep].copy()
    out = out.where(out.notna(), None)
    return out.head(limit).to_dict(orient='records')

@app.get('/health')
def health():
    return {'status': 'ok', 'server_time_beijing': stamp(), 'note': 'health does not verify market feed'}

@app.get('/v1/market')
def market():
    def load():
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            raise ValueError('empty market data')
        change = df['涨跌幅'].apply(lambda x: float(x) if x is not None else 0)
        volume = df['成交额'].apply(lambda x: float(x) if x is not None else 0)
        return {'collected_at_beijing': stamp(), 'source': 'AKShare/Eastmoney', 'upstream_quote_time': None,
                'quote_freshness_verified': False, 'stock_count': len(df),
                'up': int((change > 0).sum()), 'down': int((change < 0).sum()), 'flat': int((change == 0).sum()),
                'up_9_5pct': int((change >= 9.5).sum()), 'down_9_5pct': int((change <= -9.5).sum()),
                'turnover_yuan_sum': float(volume.sum()),
                'watchlist': records(df[df['代码'].astype(str).isin(WATCH)], ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额','换手率','最高','最低','今开','昨收'])}
    return snapshot('market', load)

@app.get('/v1/sectors')
def sectors(limit: int = Query(20, ge=1, le=100)):
    def load():
        df = ak.stock_board_industry_name_em()
        if df.empty:
            raise ValueError('empty sector data')
        return {'collected_at_beijing': stamp(), 'source': 'AKShare/Eastmoney', 'upstream_quote_time': None,
                'quote_freshness_verified': False,
                'leaders': records(df.sort_values('涨跌幅', ascending=False), ['板块名称','涨跌幅','总市值','换手率','上涨家数','下跌家数','领涨股票','领涨股票-涨跌幅'], limit),
                'laggards': records(df.sort_values('涨跌幅', ascending=True), ['板块名称','涨跌幅','总市值','换手率','上涨家数','下跌家数','领涨股票','领涨股票-涨跌幅'], limit)}
    return snapshot(f'sectors_{limit}', load)

@app.get('/v1/stock/{symbol}')
def stock(symbol: str):
    if len(symbol) != 6 or not symbol.isdigit():
        raise HTTPException(status_code=400, detail='symbol must be six digits')
    def load():
        df = ak.stock_zh_a_spot_em()
        matched = df[df['代码'].astype(str) == symbol]
        if matched.empty:
            raise HTTPException(status_code=404, detail='symbol not found')
        return {'collected_at_beijing': stamp(), 'source': 'AKShare/Eastmoney', 'upstream_quote_time': None,
                'quote_freshness_verified': False, 'data': records(matched, ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额','换手率','最高','最低','今开','昨收'])[0]}
    return snapshot('stock_'+symbol, load)
