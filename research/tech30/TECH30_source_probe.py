# -*- coding: utf-8 -*-
"""TECH30 industry-source EXPERIMENT ONLY.
Run as a separate SuperMind research strategy; NEVER place orders.
Do not replace the live TECH30 strategy with this probe.
"""
from mindgo_api import *

# Each question is deliberately short. 'set_attr' values are literal,
# and results are read from context rather than the get_iwencai return value.
SOURCES = (
    ("semi_material", "半导体材料概念股"),
    ("semi_equipment", "半导体设备概念股"),
    ("semi_packaging", "先进封装概念股"),
    ("ai_server", "AI服务器概念股"),
    ("liquid_cooling", "液冷服务器概念股"),
    ("data_power", "数据中心电源概念股"),
    ("ups_power", "UPS电源概念股"),
    ("copper_connection", "高速铜连接概念股"),
    ("pcb", "PCB概念股"),
    ("ccl", "覆铜板概念股"),
    ("passives", "被动元件概念股"),
    ("power_devices", "功率半导体概念股"),
    ("industrial_sensor", "工业传感器概念股"),
    ("machine_vision", "机器视觉硬件概念股"),
    ("servo", "伺服系统概念股"),
)

def allowed(s):
    return ((s.startswith('600') and s.endswith('.SH')) or
            (s.startswith('00') and s.endswith('.SZ')))

def init(context):
    set_benchmark('000300.SH')
    get_iwencai("半导体材料概念股", set_attr="semi_material")
    get_iwencai("半导体设备概念股", set_attr="semi_equipment")
    get_iwencai("先进封装概念股", set_attr="semi_packaging")
    get_iwencai("AI服务器概念股", set_attr="ai_server")
    get_iwencai("液冷服务器概念股", set_attr="liquid_cooling")
    get_iwencai("数据中心电源概念股", set_attr="data_power")
    get_iwencai("UPS电源概念股", set_attr="ups_power")
    get_iwencai("高速铜连接概念股", set_attr="copper_connection")
    get_iwencai("PCB概念股", set_attr="pcb")
    get_iwencai("覆铜板概念股", set_attr="ccl")
    get_iwencai("被动元件概念股", set_attr="passives")
    get_iwencai("功率半导体概念股", set_attr="power_devices")
    get_iwencai("工业传感器概念股", set_attr="industrial_sensor")
    get_iwencai("机器视觉硬件概念股", set_attr="machine_vision")
    get_iwencai("伺服系统概念股", set_attr="servo")
    context.probe_done = False
    log.info("TECH30_EXPAND_INIT research_only no_orders")

def before_trading(context):
    if context.probe_done:
        return
    # Explicit attribute access avoids getattr() sandbox rejections.
    groups = [
        ("semi_material", context.semi_material),
        ("semi_equipment", context.semi_equipment),
        ("semi_packaging", context.semi_packaging),
        ("ai_server", context.ai_server),
        ("liquid_cooling", context.liquid_cooling),
        ("data_power", context.data_power),
        ("ups_power", context.ups_power),
        ("copper_connection", context.copper_connection),
        ("pcb", context.pcb),
        ("ccl", context.ccl),
        ("passives", context.passives),
        ("power_devices", context.power_devices),
        ("industrial_sensor", context.industrial_sensor),
        ("machine_vision", context.machine_vision),
        ("servo", context.servo),
    ]
    merged = set()
    semi = set()
    hardware = set()
    for name, raw in groups:
        symbols = set(s for s in list(raw) if allowed(s))
        log.info("TECH30_EXPAND_SOURCE %s count=%d sample=%s" %
                 (name, len(symbols), str(sorted(symbols)[:3])))
        merged.update(symbols)
        if name.startswith("semi_"):
            semi.update(symbols)
        else:
            hardware.update(symbols)
    log.info("TECH30_EXPAND_SUMMARY total=%d semi=%d hardware=%d overlap=%d" %
             (len(merged), len(semi), len(hardware), len(semi & hardware)))
    # No trade actions; no inferred 'industry leader' classification.
    context.probe_done = True

def handle_bar(context, bar_dict):
    pass
