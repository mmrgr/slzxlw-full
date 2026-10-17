"""日志集中化 (2026-10-16 整理轮).

【目标】把散落在各目录的**历史日志**集中到 `_logs/`, 并生成总索引;
       **但不移动仍被脚本写入的日志**, 否则会破坏写出路径。

【为什么不能一律搬走】
机械核验显示: 研究目录内 22 个 `.log` 中只有 4 个仍被脚本以 `open(...,"w")` 写入
(`t19*.log` ← `T19*.py`)。其余 18 个是**冻结的历史记录**。
若把 `t19.log` 搬走, `T19_db_sensitivity.py` 下次运行会在原处**重新生成**一份,
造成"同一日志两处存在"的混乱。

【策略】
  1. 逐日志判定: 是否仍被任何脚本写入 (扫描 `open(...,'w')` 与文件名);
  2. **仍被写入** -> 原地保留, 在索引中标注 `active`;
  3. **冻结**   -> 复制到 `_logs/<来源目录>/` 并在原地留 **软链接式指针文件**
                  (`<原名>.moved.md`), 说明真实位置 —— 这样即使有人按旧路径找,
                  也能立刻知道新位置, 且**原文件名不被复用**;
  4. 生成 `_logs/LOG_INDEX.md`: 一行一日志 (来源 / 大小 / 行数 / 状态 / 摘要首行)。

【纪律】
  · 不删除任何日志 (全部保留原文);
  · 不改任何脚本的写出路径;
  · 索引中记录原文 SHA-256 前 12 位, 便于校验搬移无损。
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent          # 算力中心
LOGS = ROOT / "_logs"
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "_archive_2026-10-16", "_logs",
             "_prev_2026-10-16", ".venv", "dist", ".next"}


def sha(p: Path, n=12) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:n]


def main() -> None:
    t0 = time.time()
    LOGS.mkdir(exist_ok=True)

    # ---------- 1. 扫描全部 .log ----------
    logs = [p for p in ROOT.rglob("*.log")
            if not any(s in p.parts for s in SKIP_DIRS)]
    print(f"发现 .log = {len(logs)}")

    # ---------- 2. 判定哪些仍被脚本写入 ----------
    srcs = [p for p in ROOT.rglob("*.py")
            if not any(s in p.parts for s in SKIP_DIRS)]
    active: set[str] = set()
    for lg in logs:
        for s in srcs:
            try:
                t = s.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if lg.name in t and ("open(" in t):
                # 粗判: 文件名出现在含 open( 的脚本中, 且该处附近有 "w"
                import re
                for m in re.finditer(re.escape(lg.name), t):
                    seg = t[max(0, m.start() - 200): m.start() + 200]
                    if re.search(r'open\([^)]*["\']w', seg):
                        active.add(lg.name)
                        break
    print(f"仍被脚本写入(原地保留) = {len(active)}: {sorted(active)}")

    # ---------- 3. 搬移冻结日志 ----------
    moved, kept = [], []
    rows = []
    for lg in sorted(logs):
        rel = lg.relative_to(ROOT)
        src_dir = str(rel.parent).replace("\\", "/")
        is_active = lg.name in active
        try:
            text = lg.read_text(encoding="utf-8", errors="replace")
            nlines = text.count("\n") + 1
            head = next((l.strip() for l in text.splitlines() if l.strip()), "")[:100]
        except Exception:
            nlines, head = -1, "(不可读)"
        size = lg.stat().st_size
        h = sha(lg)

        if is_active:
            kept.append(str(rel))
            rows.append((src_dir, lg.name, size, nlines, "active (原地保留)", h, head))
            continue

        # 目标: _logs/<src_dir>/<name>
        dest_dir = LOGS / src_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / lg.name
        if dest.exists():
            dest = dest_dir / f"{lg.stem}__dup{lg.suffix}"
        shutil.copy2(lg, dest)                       # 复制而非移动, 保证零风险
        # 原地留指针说明
        note = lg.with_suffix(lg.suffix + ".moved.md")
        note.write_text(
            f"# 此日志已集中到 `_logs/`\n\n"
            f"- 原路径: `{rel}`\n"
            f"- 现路径: `_logs/{src_dir}/{dest.name}`\n"
            f"- SHA-256(前12): `{h}`\n"
            f"- 大小: {size} bytes / {nlines} 行\n"
            f"- 原因: 整理轮集中历史日志; 原文**未被删除**。\n"
            f"- 若某脚本仍按旧名写出本文件, 会在原处**重新生成**(这是预期行为)。\n",
            encoding="utf-8")
        moved.append((str(rel), f"_logs/{src_dir}/{dest.name}"))
        rows.append((src_dir, lg.name, size, nlines, "archived -> _logs/", h, head))

    # ---------- 4. 生成索引 ----------
    total_bytes = sum(r[2] for r in rows if r[2] > 0)
    total_lines = sum(r[3] for r in rows if r[3] > 0)
    md = [
        "# 日志总索引 (LOG_INDEX)",
        "",
        "> 自动生成: `python _logs/consolidate_logs.py`",
        f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- 日志总数 **{len(rows)}**",
        f"- 仍未脚本写入(原地保留) **{len([r for r in rows if r[4].startswith('active')])}**",
        f"- 已归档到 `_logs/` **{len([r for r in rows if r[4].startswith('archived')])}**",
        f"- 合计 {total_bytes/1024:.1f} KB / {total_lines} 行",
        "",
        "## 为何部分日志留在原地",
        "",
        "机械核验: 只有仍被脚本以 `open(...,'w')` 写入的日志才原地保留 ——",
        "若搬走, 脚本下次运行会在原处**重新生成**, 造成同一日志两处存在。",
        "冻结的历史日志则复制到 `_logs/`, 并在原地留下 `<原名>.moved.md` 指针。",
        "",
        "## 清单",
        "",
        "| 来源目录 | 日志名 | 大小(B) | 行数 | 状态 | sha256(12) | 首行 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for src_dir, name, size, nlines, status, h, head in rows:
        head_clean = head.replace("|", "\\|")[:70]
        md.append(f"| `{src_dir}` | `{name}` | {size} | {nlines} | {status} | `{h}` | {head_clean} |")
    md += [
        "",
        "## 说明",
        "",
        "- 原文**全部保留**, 无删除; 归档为**复制**操作, 可随时回滚。",
        "- 原地 `<原名>.moved.md` 文件说明真实位置, 避免按旧路径找不到。",
        "- 引擎目录 `07_代码_AI-UWM引擎/**/validation_artifacts/**` 下的日志属",
        "  **引擎自带验证产物**, 一并纳入本索引但保留在其原位语义下(见上表来源列)。",
        "",
    ]
    (LOGS / "LOG_INDEX.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n归档 {len(moved)} 个; 原地保留 {len(kept)} 个")
    print(f"索引: {LOGS/'LOG_INDEX.md'}")
    print(f"用时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
