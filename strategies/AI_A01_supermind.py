# -*- coding: utf-8 -*-
"""AI_A01 / Relative Strength Rotation / SuperMind research backtest.
Only 600*.SH and 00*.SZ ordinary shares; 50k paper capital.
NO LIVE TRADING: verify platform fills and filters first.
"""
from mindgo_api import *
import math

CAPITAL = 50000.0
MAX_VALUE = 20000.0
MAX_HOLDINGS = 2
SCAN_LIMIT = 160
MIN_AVG_TURNOVER = 2e8

def allowed(s):
    return ((s.startswith('600') and s.endswith('.SH')) or
            (s.startswith('00') and s.endswith('.SZ')))

def as_closes(s):
    d = history(s, ['close', 'turnover'], 65, '1d', False, 'pre', is_panel=1)
    if d is None or len(d) < 61:
        return None
    return d

def features(d):
    close = [float(v) for v in d['close'].values]
    turnover = [float(v) for v in d['turnover'].values]
    if min(close[-61:]) <= 0:
        return None
    r20 = close[-1] / close[-21] - 1.0
    r5 = close[-1] / close[-6] - 1.0
    avg_turn = sum(turnover[-20:]) / 20.0
    rets = [close[i] / close[i-1] - 1 for i in range(len(close)-20, len(close))]
    mu = sum(rets) / len(rets)
    vol = math.sqrt(sum((x-mu)**2 for x in rets) / len(rets))
    if not (r20 > 0 and -.03 <= r5 <= .08 and avg_turn >= MIN_AVG_TURNOVER):
        return None
    return {'r20':r20, 'vol':vol}

def ordinal_scores(items):
    if not items:
        return []
    by_ret = sorted(items, key=lambda z: (z[1]['r20'], z[0]))
    by_vol = sorted(items, key=lambda z: (z[1]['vol'], z[0]))
    rnk_r = {s:i for i,(s,_) in enumerate(by_ret)}
    rnk_v = {s:i for i,(s,_) in enumerate(by_vol)}
    n = max(1,len(items)-1)
    return sorted([(rnk_r[s]/float(n)-rnk_v[s]/float(n),s)
                   for s,_ in items],key=lambda z:(-z[0],z[1]))

def init(context):
    set_benchmark('000300.SH')
    set_commission(PerShare(type='stock',cost=0.0002))
    set_slippage(PriceSlippage(0.005))
    set_volume_limit(0.25,0.5)
    get_iwencai('非ST，市值大于100亿',set_attr='a01_pool')
    context.a01_week = ''
    context.a01_targets = []
    context.a01_last_actions = {}
    log.info('A01 INIT VERSION=1.0 RESEARCH_ONLY capital=50000')

def before_trading(context):
    today = get_datetime().date()
    year,week,_ = today.isocalendar()
    week_key = '%04d-W%02d'%(year,week)
    if week_key == context.a01_week:
        return
    context.a01_week = week_key
    universe = sorted(set(s for s in list(context.a01_pool) if allowed(s)))
    if len(universe)>SCAN_LIMIT:
        start = ((year*53+week)*SCAN_LIMIT)%len(universe)
        universe = (universe+universe)[start:start+SCAN_LIMIT]
    good = []
    errors = 0
    for s in universe:
        try:
            f = features(as_closes(s))
            if f is not None:
                good.append((s,f))
        except Exception:
            errors += 1
    ranked = ordinal_scores(good)
    context.a01_targets = [s for _,s in ranked[:MAX_HOLDINGS]]
    log.info('A01 RANK week=%s scanned=%d eligible=%d errors=%d targets=%s'%
             (week_key,len(universe),len(good),errors,str(context.a01_targets)))

def existing_positions(context):
    return context.portfolio.stock_account.positions

def submit_once(context,symbol,delta,when,reason):
    key = str(when.date())+':'+symbol
    if key in context.a01_last_actions or delta==0:
        return False
    context.a01_last_actions[key]=reason
    oid=order(symbol,int(delta))
    log.info('A01 ORDER time=%s symbol=%s qty=%d oid=%s reason=%s'%
             (str(when),symbol,delta,str(oid),reason))
    return oid is not None

def handle_bar(context,bar_dict):
    now=get_datetime()
    clock=(now.hour,now.minute)
    if clock not in ((9,32),(14,50)):
        return
    positions=existing_positions(context)
    held=list(positions.keys())
    sold=False
    for s in held:
        p=positions[s]
        if int(p.amount)<=0 or int(p.available_amount)<=0:
            continue
        reason=None
        if clock==(9,32) and s not in context.a01_targets:
            reason='weekly_unranked'
        if clock==(14,50):
            quote=get_current([s])
            if s in quote:
                price=float(quote[s].close)
                cost=float(p.cost_basis)
                if cost>0 and price/cost-1.0<=-0.08:
                    reason='close_below_minus_8pct'
        if reason is not None:
            if submit_once(context,s,-int(p.available_amount),now,reason):
                sold=True
    if sold or clock!=(9,32):
        return
    if len(held)>=MAX_HOLDINGS:
        return
    cash=min(float(context.portfolio.available_cash),CAPITAL)
    for s in context.a01_targets:
        if s in held or len(held)>=MAX_HOLDINGS:
            continue
        quote=get_current([s])
        if s not in quote:
            continue
        b=quote[s]
        if b.is_st or b.is_paused:
            continue
        price=float(b.close)
        if price<=0 or price>=float(b.high_limit)*.999:
            continue
        budget=min(MAX_VALUE,cash-30.0)
        shares=int(budget/(price*1.012)/100)*100
        if shares<=0:
            continue
        if submit_once(context,s,shares,now,'weekly_top_rank'):
            held.append(s)
            cash-=shares*price*1.012
            if cash<=0:
                break

def on_trade(context,trade):
    log.info('A01 FILL symbol=%s qty=%s price=%s order_id=%s exec_id=%s'%
             (str(trade.order_book_id),str(trade.last_quantity),
              str(trade.last_price),str(trade.order_id),str(trade.exec_id)))

def on_order(context,odr):
    log.info('A01 ORDER_EVENT %s'%str(odr))

def after_trading(context):
    today=get_datetime().date()
    log.info('A01 CLOSE date=%s nav=%.2f cash=%.2f positions=%s'%
             (str(today),float(context.portfolio.portfolio_value),
              float(context.portfolio.available_cash),
              str(list(existing_positions(context).keys()))))
