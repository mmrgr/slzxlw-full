"""Pass 2: resolve remaining WaterMet contexts to neutral wording."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src")

def edit(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = ROOT / rel
    if not p.exists():
        print("MISSING FILE:", rel)
        return
    try:
        t = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        t = p.read_text(encoding="gb18030")
        enc = "gb18030"
    else:
        enc = "utf-8"
    n = 0
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new)
            n += 1
        else:
            print(f"  MISS [{rel}]: {old[:60]}")
    p.write_text(t, encoding=enc)
    print(f"ok {rel}: {n}/{len(pairs)}")

# ---- frontend identifiers ----
edit("frontend/src/App.tsx", [
    ("'watermet-theme'", "'aiuwm-theme'"),
    ("不是有效的 WaterMet² 项目", "不是有效的 AI-UWM 项目"),
])
edit("frontend/src/components/canvas/ModelCanvas.tsx", [
    ("{ watermet: WaterNode }", "{ aiuwm: WaterNode }"),
    ("{ watermet: WaterEdge }", "{ aiuwm: WaterEdge }"),
    ("'application/watermet-node'", "'application/aiuwm-node'"),
    ("type: 'watermet',", "type: 'aiuwm',"),
    ("{{ type: 'watermet', animated: true }}", "{{ type: 'aiuwm', animated: true }}"),
])
edit("frontend/src/components/canvas/Palette.tsx", [
    ("'application/watermet-node'", "'application/aiuwm-node'"),
])
edit("frontend/src/engine/adapters/projectAdapter.ts", [("type: 'watermet',", "type: 'aiuwm',")])
edit("frontend/src/store/useProjectStore.ts", [("type: 'watermet',", "type: 'aiuwm',")])
edit("frontend/src/types/nodes.ts", [
    ("Node<UWMNodeData, 'watermet'>", "Node<UWMNodeData, 'aiuwm'>"),
    ("Edge<UWMEdgeData, 'watermet'>", "Edge<UWMEdgeData, 'aiuwm'>"),
])
edit("frontend/src/components/advanced/AdvancedPage.tsx", [
    ("直接调用 WaterMet² 计算引擎", "直接调用 AI-UWM 计算引擎"),
])
edit("frontend/src/components/datagrid/DataCenter.tsx", [
    ("驱动 WaterMet² 的日尺度数据", "驱动 AI-UWM 的日尺度数据"),
])
edit("frontend/src/components/simulation/SimulationPage.tsx", [
    ("开始运行 WaterMet² 日尺度质量平衡", "开始运行 AI-UWM 日尺度质量平衡"),
])
edit("frontend/README.md", [
    ("WaterMet² 是日尺度城市水系统战略模型", "本框架是日尺度城市水系统战略模型"),
    ("启动 WaterMet² 模型 API", "启动 AI-UWM 模型 API"),
])
edit("frontend/src/components/dashboard/ResultsDashboard.tsx", [])

# ---- python package runtime strings ----
edit("src/aiuwm/api.py", [
    ("description=\"Local API adapter for the WaterMet² Python simulation engine.\"",
     "description=\"Local API adapter for the AI-UWM Python simulation engine.\""),
])
edit("src/aiuwm/cli.py", [
    ("description=\"开放式 WaterMet² 全功能分析引擎\"", "description=\"开放式 AI-UWM 全功能分析引擎\""),
])
edit("src/aiuwm/full_engine.py", [
    ("FAO-56 daily Penman-Monteith reference evaporation from WaterMet² climate fields.",
     "FAO-56 daily Penman-Monteith reference evaporation from AI-UWM climate fields."),
    ("污水拓扑包含环；WaterMet² 日路由要求有向无环连接",
     "污水拓扑包含环；AI-UWM 日路由要求有向无环连接"),
])
edit("tests/test_api.py", [('assert "WaterMet" in studio.text', 'assert "AI-UWM Studio" in studio.text')])
edit("scripts/run_full_validation.py", [
    ('"# WaterMet² 合成数据全流程验证报告"', '"# AI-UWM 合成数据全流程验证报告"'),
])
edit("scripts/discover_trust_archive.py", [
    ('terms = ("watermet", "dss", "uws performance", "software", "metabolism")',
     'terms = ("urban water", "dss", "uws performance", "software", "metabolism")'),
])
