import os
import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title='A-share Multi-source Snapshot', version='0.2')
TZ = ZoneInfo('Asia/Shanghai')
TTL = int(os.getenv('CACHE_SECONDS', '45'))
WATCH = {'600641': '先导', '600522': '中天科技', '002245': '蔚蓝锂芯', '600028': '中国石化'}
_cache = {}
_lock = threading.Lock()


def stamp():
    return datetime.now(TZ).isoformat(timespec='seconds')


def prefix(symbol):
    if len(symbol) != 6 or not symbol.isdigit():
        raise ValueError('symbol must be six digits')
    return ('sh' if symbol.startswith(('6', '9')) else 'bj' if symbol.startswith(('4', '8')) else 'sz') + symbol


def num(value):
    try:
        return float(value) if value not in ('', '-', None) else None
    except (ValueError, TypeError):
        return None


def tencent(symbols):
    codes = [prefix(s) for s in symbols]
    response = requests.get('https://qt.gtimg.cn/q=' + ','.join(codes), timeout=8,
                            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'})
    response.raise_for_status()
    response.encoding = 'gbk'
    result = {}
    for line in response.text.split(';'):
        if '="' not in line:
            continue
        left, raw = line.split('="', 1)
        data = raw.rstrip('"\r\n').split('~')
        if len(data) < 46 or not data[2].isdigit():
            continue
        symbol = data[2]
        if symbol not in symbols:
            continue
        # Tencent quote protocol: indexes are source-specific; never infer exchange timestamp from collection time.
        result[symbol] = {
            'symbol': symbol, 'name': data[1], 'price': num(data[3]),
            'previous_close': num(data[4]), 'open': num(data[5]),
            'volume_hands': num(data[6]), 'change': num(data[31]),
            'change_pct': num(data[32]), 'high': num(data[33]), 'low': num(data[34]),
            'turnover_10k_yuan': num(data[37]), 'quote_time_raw': data[30],
            'source': 'Tencent/qt.gtimg.cn',
        }
    if not result:
        raise ValueError('Tencent returned no parseable quote records')
    return result


def mootdx_quotes(symbols):
    from mootdx.quotes import Quotes
    client = Quotes.factory(market='std', multithread=False)
    try:
        query = [{'market': 1 if s.startswith(('6', '9')) else 0, 'code': s} for s in symbols]
        df = client.quotes(symbol=query)
        if df is None or df.empty:
            raise ValueError('mootdx returned empty quotes')
        result = {}
        for _, row in df.iterrows():
            code = str(row.get('code', ''))
            if code not in symbols:
                continue
            result[code] = {'symbol': code, 'name': WATCH.get(code), 'price': num(row.get('price')),
                            'previous_close': num(row.get('last_close')), 'open': num(row.get('open')),
                            'high': num(row.get('high')), 'low': num(row.get('low')),
                            'volume': num(row.get('vol')), 'source': 'mootdx/TDX',
                            'quote_time_raw': None}
        if not result:
            raise ValueError('mootdx returned no matching symbols')
        return result
    finally:
        client.close()


def get_quotes(symbols):
    errors = {}
    for source, fn in [('tencent', tencent), ('mootdx', mootdx_quotes)]:
        try:
            data = fn(symbols)
            return {'source': source, 'data': data, 'errors': errors,
                    'collected_at_beijing': stamp(), 'quote_freshness_verified': False}
        except Exception as exc:
            errors[source] = f'{type(exc).__name__}: {str(exc)[:160]}'
    raise HTTPException(status_code=503, detail={'message': 'all quote sources failed', 'sources': errors})


def cached(key, loader):
    now = time.monotonic()
    with _lock:
        item = _cache.get(key)
        if item and now - item['at'] < TTL:
            return item['value']
    value = loader()
    with _lock:
        _cache[key] = {'at': time.monotonic(), 'value': value}
    return value


@app.get('/')
def root():
    return {'service': 'A-share multi-source quotes', 'version': '0.2',
            'routes': ['/health', '/v1/sources', '/v1/market', '/v1/stock/600641', '/v1/sectors']}


@app.get('/health')
def health():
    return {'status': 'ok', 'server_time_beijing': stamp(), 'note': 'does not verify quote feeds'}


@app.get('/v1/sources')
def sources():
    statuses = {}
    for name, fn in [('tencent', tencent), ('mootdx', mootdx_quotes)]:
        try:
            value = fn(['600028'])
            statuses[name] = {'ok': bool(value), 'sample': value.get('600028')}
        except Exception as exc:
            statuses[name] = {'ok': False, 'error': f'{type(exc).__name__}: {str(exc)[:180]}'}
    return {'checked_at_beijing': stamp(), 'sources': statuses}


@app.get('/v1/market')
def market():
    # This is a WATCHLIST snapshot, not market-wide breadth. No fabricated market totals.
    result = cached('watchlist', lambda: get_quotes(list(WATCH)))
    return {**result, 'scope': 'watchlist_only', 'watchlist': list(result['data'].values()),
            'market_breadth_available': False, 'sector_ranking_available': False}


@app.get('/v1/stock/{symbol}')
def stock(symbol: str):
    try:
        prefix(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = cached('stock_' + symbol, lambda: get_quotes([symbol]))
    if symbol not in result['data']:
        raise HTTPException(status_code=404, detail='symbol not found')
    return {**result, 'data': result['data'][symbol]}


@app.get('/v1/sectors')
def sectors(limit: int = Query(20, ge=1, le=100)):
    raise HTTPException(status_code=501, detail='sector rankings are not yet supported by verified sources; no fabricated rankings')
