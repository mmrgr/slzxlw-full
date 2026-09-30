"""生成可复现清单（对应外部建议 9）。

记录：解释器与关键包版本、git HEAD 与工作区状态、核心产物 SHA256、重算命令。
目的不是把大产物塞进版本管理，而是**让产物可被独立重算并校验**——
这比归档 GB 级二进制更符合可复现性原则（见评审文档对 gitignore 策略的辩证保留）。

用法：
    PYTHONPATH=src python scripts/build_reproduction_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "validation_artifacts" / "r2"
OUT = ROOT / "REPRODUCTION_MANIFEST.md"

KEY_ARTIFACTS = [
    R2 / "claim_register_R5.csv",
    R2 / "water_balance_closure.csv",
    R2 / "intervention_water_energy_carbon.csv",
    R2 / "reservoir_multiyear_ensemble.json",
    R2 / "reservoir_multiyear_ensemble_12seq.json",
    R2 / "literature_matrix_gap.csv",
    R2 / "probabilistic_status.md",
    R2 / "ha" / "probabilistic_corrected_summary.json",
    R2 / "co" / "probabilistic_corrected_summary.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        return out.stdout.strip() if out.returncode == 0 else f"<失败: {out.stderr.strip()[:60]}>"
    except Exception as exc:  # noqa: BLE001
        return f"<不可用: {exc}>"


def versions() -> list[tuple[str, str]]:
    rows = [("python", platform.python_version()), ("platform", platform.platform())]
    for name in ("numpy", "pandas", "scipy"):
        try:
            module = __import__(name)
            rows.append((name, getattr(module, "__version__", "未知")))
        except ImportError:
            rows.append((name, "未安装"))
    return rows


def main() -> int:
    lines: list[str] = []
    lines.append("# AI-UWM 可复现清单（R5）\n")
    lines.append("本清单随 `scripts/build_reproduction_manifest.py` 自动生成，请勿手改。\n")

    lines.append("## 一、运行环境\n")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    for key, value in versions():
        lines.append(f"| {key} | `{value}` |")

    lines.append("\n## 二、代码版本\n")
    head = git("log", "--oneline", "-1")
    status_lines = [line for line in git("status", "--short").splitlines() if line.strip()]
    dirty = "是（有未提交变更）" if status_lines else "否"
    lines.append(f"| 项 | 值 |")
    lines.append(f"|---|---|")
    lines.append(f"| git HEAD | `{head}` |")
    lines.append(f"| 远端 | `{git('remote', 'get-url', 'origin') or '无'}` |")
    lines.append(f"| 工作区脏 | {dirty} |")
    if status_lines:
        lines.append("\n未提交文件：\n```")
        lines.extend(status_lines)
        lines.append("```")
    lines.append(
        "\n> 注：`.gitignore` 第 10 行 `validation_artifacts/*` 使多数产物不入库——"
        "这是刻意设计（产物应由脚本重算），下方哈希用于校验重算结果是否一致。"
    )

    lines.append("\n## 三、关键产物校验（SHA256）\n")
    lines.append("| 产物 | 字节数 | SHA256（前 16 位） |")
    lines.append("|---|---|---|")
    missing_count = 0
    for path in KEY_ARTIFACTS:
        if not path.exists():
            lines.append(f"| `{path.relative_to(ROOT)}` | — | **缺失** |")
            missing_count += 1
            continue
        lines.append(
            f"| `{path.relative_to(ROOT)}` | {path.stat().st_size:,} | `{sha256(path)[:16]}` |"
        )

    lines.append("\n## 四、重算命令（按依赖顺序）\n")
    lines.append("```bash")
    lines.append("cd \"07_代码_AI-UWM引擎/aiuwm_src\"")
    lines.append("# 解释器：需 numpy/pandas/scipy（见环境一节）")
    lines.append("")
    lines.append("# ① 单元测试")
    lines.append("PYTHONPATH=src python -m pytest -q")
    lines.append("")
    lines.append("# ② 主张登记表（依赖 reservoir_multiyear_ensemble.json）")
    lines.append("PYTHONPATH=src python scripts/build_claim_register.py")
    lines.append("")
    lines.append("# ③ 水量闭合（读已有逐日产物，不重跑引擎）")
    lines.append("PYTHONPATH=src python scripts/audit_water_balance_closure.py")
    lines.append("")
    lines.append("# ④ 水—能—碳—社会联合指标")
    lines.append("PYTHONPATH=src python scripts/build_intervention_wec.py")
    lines.append("")
    lines.append("# ⑤ 多序列集合（20 条 = 原 12 条 + 索引 12-19）")
    lines.append("#   原 12 条：  --sequences 12 --base-seed 20260918 --stride 100003")
    lines.append("#   新增 8 条： --sequences  8 --base-seed 1220954 --stride 100003")
    lines.append("PYTHONPATH=src python scripts/audit_reservoir_ensemble.py \\")
    lines.append("    --domains ha,co --years 10 --max-mw 1200 --step-mw 100 \\")
    lines.append("    --sequences 12 --base-seed 20260918 --stride 100003 \\")
    lines.append("    --out validation_artifacts/r2/reservoir_multiyear_ensemble.json")
    lines.append("PYTHONPATH=src python scripts/audit_reservoir_ensemble.py \\")
    lines.append("    --domains ha,co --years 10 --max-mw 1200 --step-mw 100 \\")
    lines.append("    --sequences 8 --base-seed 1220954 --stride 100003 \\")
    lines.append("    --out validation_artifacts/r2/reservoir_multiyear_ensemble_ext.json")
    lines.append("PYTHONPATH=src python scripts/merge_reservoir_ensemble.py")
    lines.append("")
    lines.append("# ⑥ 三道提交门禁")
    lines.append("PYTHONPATH=src python scripts/audit_doc_consistency.py")
    lines.append("PYTHONPATH=src python scripts/audit_experiment_design.py")
    lines.append("PYTHONPATH=src python scripts/audit_realism.py")
    lines.append("")
    lines.append("# ⑦ 本清单自身")
    lines.append("PYTHONPATH=src python scripts/build_reproduction_manifest.py")
    lines.append("```")

    lines.append("\n## 五、尚未固化的可复现项\n")
    lines.append("- ❌ **环境锁定文件**（`requirements.txt` / `environment.lock`）：当前依赖系统解释器，未锁定小版本")
    lines.append("- ❌ **原始数据许可**：无真实数据源，故不适用；接入观测数据后须补充")
    lines.append("- ❌ **7 张图的图表清单**：已登记为待办，尚未制作")
    lines.append("- ❌ **独立审稿人式投稿前复核**：未执行")
    lines.append("- ⚠️ 集合产物仅在种子层面可复现，因其依赖 `build_r2_domains` 的合成驱动规则版本")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written -> {OUT}")
    print(f"缺失产物 {missing_count} 个；git 工作区脏：{dirty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
