# -*- coding: utf-8 -*-
"""查清 quality_state / quality_solver 为何被 DISABLED_LEGACY_VOLUME_ONLY。

【发现】
在 cawcc_r2 的 ha/co 两个端点项目下，730 天全部为：
  quality_solver_status = not_applicable
  quality_state_status  = DISABLED_LEGACY_VOLUME_ONLY
  quality_state_enabled = False

说明模型的**质量状态（动态盐分追踪）路径未启用**，走的是"legacy volume-only"路径。
这与文档中反复提到的"volume-only 路径内部不一致"（主稿 §7.7a）直接相关。

【要查】
1. 是什么配置项控制 quality_state_enabled？
2. 该配置在 project.json 里是什么值？
3. 若启用，CoC 与 CAWCC 会怎样变化？——这可能是一个重要的敏感性检验。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
HERE = Path(__file__).resolve().parent
OUT = HERE / "_quality_state_config.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    # 1. 源码里找控制开关
    import subprocess
    src = ROOT / "src" / "aiuwm"
    hits = []
    for f in src.rglob("*.py"):
        txt = f.read_text(encoding="utf-8", errors="replace")
        if "DISABLED_LEGACY_VOLUME_ONLY" in txt or "quality_state" in txt:
            for i, ln in enumerate(txt.splitlines(), 1):
                if ("DISABLED_LEGACY_VOLUME_ONLY" in ln or "quality_state_enabled" in ln
                        or "quality_state" in ln and "=" in ln and "def" not in ln):
                    hits.append(f"{f.relative_to(ROOT)}:{i}: {ln.strip()[:120]}")
    w("=== 源码中 quality_state 相关行 ===")
    for h in hits[:40]:
        w("  " + h)

    # 2. project.json 里的配置
    for d in ("ha", "co"):
        p = ROOT / "examples" / "cawcc_r2" / d / "project.json"
        cfg = json.loads(p.read_text(encoding="utf-8"))
        w(f"\n\n=== {d}/project.json 中 quality 相关键 ===")
        s = json.dumps(cfg, ensure_ascii=False, indent=1)
        for ln in s.splitlines():
            if "quality" in ln.lower() or "state" in ln.lower():
                w("  " + ln.strip()[:140])

    Path(HERE / "_quality_state_config.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
