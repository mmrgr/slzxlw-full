"""对《AI-UWM下一轮模拟_情景设置与实施方案》做 v4 修订的精确替换部分。

用 bytes 级替换，避免再次出现换行符被二次转义的问题（上一轮在仓库里踩过）。
"""
from __future__ import annotations

import io
from pathlib import Path

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")

# (旧文本, 新文本, 说明)
REPLACES: list[tuple[str, str, str]] = [
    # --- 1. 引擎路径：包名已由 watermet2_repro 改为 aiuwm -------------------
    (
        "工作目录：`aiuwm_src/`（`src/watermet2_repro/` 为引擎）",
        "工作目录：`aiuwm_src/`（`src/aiuwm/` 为引擎）",
        "引擎路径过时",
    ),
    (
        "| `src/watermet2_repro/data_center.py` |",
        "| `src/aiuwm/data_center.py` |",
        "源码路径过时",
    ),
    (
        "| `src/watermet2_repro/ai_metrics.py` |",
        "| `src/aiuwm/ai_metrics.py` |",
        "源码路径过时",
    ),
    # --- 2. 未改动段：去掉旧产品名 + 更新测试数 -----------------------------
    (
        "**未改动**：引擎守恒结构、WaterMet² 主循环、API/CLI/前端。"
        "既有测试复测 `57 passed, 1 failed`（失败项是前端 `dist` 未构建导致 "
        "Studio 健康检查 404，属既有环境问题，与本次改动无关）。",
        "**未改动**：引擎守恒结构、模拟主循环、API/CLI/前端。"
        "既有测试复测 `58 passed, 0 failed`（前端 `dist` 已构建，Studio 健康检查通过）。",
        "旧产品名 + 测试数过时",
    ),
    # --- 3. 第 17 节第 7 项：GitHub 状态已过期 ------------------------------
    (
        "7. **是否把本次改动提交到 GitHub**：改动目前只在工作区未提交"
        "（`git status`：**2 个修改 + 9 项新增**）。需要你决定是否 push。",
        "7. ~~**是否把本次改动提交到 GitHub**~~：**已完成**（commit `efa78e2`，"
        "119 files changed，已推送到 <https://github.com/mmrgr/AI-UWM> 的 `main` 分支）。"
        "注意仓库 `git user.name` 未配置，提交作者显示为 `unknown`，"
        "如需在 GitHub 上关联个人账号请先 `git config --global user.name`。",
        "GitHub 状态过时",
    ),
    # --- 4. 标题版本标记 ---------------------------------------------------
    (
        "# AI-UWM 下一轮（R2）模拟：情景设置与实施方案 v3（现实性审计版）",
        "# AI-UWM 下一轮（R2）模拟：情景设置与实施方案 v4（nature-skills 审查版）",
        "版本升级",
    ),
]


def main() -> None:
    raw = DOC.read_bytes()
    text = raw.decode("utf-8")
    eol = "\r\n" if b"\r\n" in raw else "\n"
    print(f"文件: {DOC}")
    print(f"换行风格: {'CRLF' if eol == chr(13)+chr(10) else 'LF'}")

    for old, new, note in REPLACES:
        # 兼容 CRLF：按统一 LF 处理后再还原
        work = text.replace("\r\n", "\n")
        old_lf = old.replace("\r\n", "\n")
        new_lf = new.replace("\r\n", "\n")
        if old_lf not in work:
            print(f"  [MISS] {note}: {old_lf[:60]}")
            continue
        count = work.count(old_lf)
        work = work.replace(old_lf, new_lf)
        text = work.replace("\n", eol)
        print(f"  [OK  ] {note} x{count}")

    DOC.write_bytes(text.encode("utf-8"))
    print("写入完成")
    print("残留 watermet 计数:", text.lower().count("watermet"))


if __name__ == "__main__":
    main()
