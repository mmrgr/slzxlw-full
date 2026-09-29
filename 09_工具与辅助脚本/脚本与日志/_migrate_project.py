"""按确认的映射迁移项目文件（同卷 rename，幂等、可校验）。

设计原则：
- 显式映射（不用通配符），每个条目单独校验
- 移动后立即校验「目标存在 且 源不存在」，失败即中止并报告
- 只写目标目录，不删除任何未被映射的文件
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

DEST = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心")
KT = Path(r"C:\Users\mmrgr\Desktop\开题")
WS = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54")

# (源, 目标相对 DEST 的目录)
KT_MAP: list[tuple[str, str]] = [
    # --- 01 方案与设计文档 ---
    ("AI-UWM下一轮模拟_情景设置与实施方案.md", "01_方案与设计文档"),
    ("AI-UWM下一轮模拟_情景设置与实施方案.html", "01_方案与设计文档"),
    ("AI-UWM研究深化_文献映射与发表路径.md", "01_方案与设计文档"),
    ("AI-UWM研究深化_文献映射与发表路径.html", "01_方案与设计文档"),
    ("AI城市水代谢开题答辩PPT逐页内容设计方案_A类.docx", "01_方案与设计文档"),
    ("AI城市水代谢开题答辩PPT逐页内容设计方案_A类_白底版.docx", "01_方案与设计文档"),
    # --- 02 开题报告 ---
    ("邵敬哲24S129122开题报告.pdf", "02_开题报告/定稿"),
    ("开题报告3.3_环境领域用语修改版.docx", "02_开题报告/定稿"),
    ("开题报告3.3.docx", "02_开题报告/定稿"),
    ("开题报告3.1_修订后预览.pdf", "02_开题报告/定稿"),
    ("开题报告3.0.docx", "02_开题报告/历史版本"),
    ("开题报告3.2.docx", "02_开题报告/历史版本"),
    ("开题报告3.1_增补前备份20260910.docx", "02_开题报告/历史版本"),
    ("开题报告3.1_备份20260910_文献核查前.docx", "02_开题报告/历史版本"),
    ("开题报告3.1_备份20260910_第三轮精简前.docx", "02_开题报告/历史版本"),
    ("开题报告3.1_备份20260910_第二轮修订前.docx", "02_开题报告/历史版本"),
    ("开题报告3.1_备份20260910_第四轮迁移前.docx", "02_开题报告/历史版本"),
    ("开题报告3.1增补内容：数学模型体系与前期已完成工作.docx", "02_开题报告/增补材料"),
    # --- 03 答辩材料 ---
    ("邵敬哲硕士开题.pptx", "03_答辩材料/PPT"),
    ("开题3.5.pptx", "03_答辩材料/PPT"),
    ("哈尔滨工业大学硕士论文开题答辩-AI算力驱动下城市水系统代谢与承载边界-优化版.pptx",
     "03_答辩材料/PPT"),
    ("开题答辩_AI算力与城市人工水系统.pptx", "03_答辩材料/PPT"),
    ("开题答辩_AI算力与城市人工水系统 - 副本.pptx", "03_答辩材料/PPT"),
    ("开题3.8_发言稿.docx", "03_答辩材料/发言稿"),
    ("发言稿.pdf", "03_答辩材料/发言稿"),
    ("活页夹1.pdf", "03_答辩材料/发言稿"),
    ("开题答辩PPT_逐页详细修改报告.docx", "03_答辩材料"),
    # --- 04 评议与评价 ---
    ("邵敬哲24S129122开题报告评议表.pdf", "04_评议与评价"),
    ("sjz硕士开题报告评议表(1).pdf", "04_评议与评价"),
    ("sjz导师评价.docx", "04_评议与评价"),
    ("sjz导师评价.pdf", "04_评议与评价"),
    ("导师评价表（带签名）.pdf", "04_评议与评价"),
    ("以系统的最新版为准：硕士开题报告评议表.doc", "04_评议与评价"),
    ("以系统的最新版为准：硕士开题报告评议表.pdf", "04_评议与评价"),
    # --- 05 学校模板与规定 ---
    ("f37844a4-f6ac-4d63-a3a6-105a8a9002b7.pdf", "05_学校模板与规定"),
    ("以系统的最新版为准：硕士学位论文开题报告模板(1).docx", "05_学校模板与规定"),
]

KT_DIR_MAP: list[tuple[str, str]] = [
    ("开题1", "02_开题报告/历史版本"),
    ("lw", "06_文献库"),
    ("答辩备选PPT模板", "05_学校模板与规定"),
    ("2026秋季研究生学位过程管理工作通知（硕士）(1)", "05_学校模板与规定"),
]

WS_DIR_MAP: list[tuple[str, str]] = [
    ("aiuwm_src", "07_代码_AI-UWM引擎"),
    ("AI-UWM_R2_实验数据集", "08_实验数据"),
    ("kaoti_img", "09_工具与辅助脚本"),
    ("nature_skills", "09_工具与辅助脚本"),
]

moved = 0
errors: list[str] = []


def do_move(src: Path, dst: Path) -> None:
    global moved
    if not src.exists():
        errors.append(f"[源不存在] {src}")
        return
    if dst.exists():
        errors.append(f"[目标已存在，跳过] {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    ok = dst.exists() and not src.exists()
    if not ok:
        errors.append(f"[校验失败] {src} -> {dst}")
        return
    moved += 1
    print(f"  OK  {src.name}  ->  {dst.relative_to(DEST)}", flush=True)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    print(f"=== 批次 1：Desktop\\开题 顶层文件（{len(KT_MAP)} 个）===", flush=True)
    for name, sub in KT_MAP:
        do_move(KT / name, DEST / sub / name)

    print(f"\n=== 批次 2：Desktop\\开题 子目录（{len(KT_DIR_MAP)} 个）===", flush=True)
    for name, sub in KT_DIR_MAP:
        do_move(KT / name, DEST / sub / name)

    print(f"\n=== 批次 3：工作区目录（{len(WS_DIR_MAP)} 个，含 35k+ 文件的仓库）===", flush=True)
    for name, sub in WS_DIR_MAP:
        do_move(WS / name, DEST / sub / name)

    print("\n=== 批次 4：工作区根目录松散文件 ===", flush=True)
    loose_dir = DEST / "09_工具与辅助脚本" / "脚本与日志"
    loose = sorted(
        p for p in WS.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.name != Path(__file__).name  # 正在运行的脚本自身不移动
    )
    print(f"  待移动 {len(loose)} 个", flush=True)
    for p in loose:
        do_move(p, loose_dir / p.name)

    print(f"\n{'=' * 60}")
    print(f"成功移动 {moved} 项")
    if errors:
        print(f"\n异常 {len(errors)} 项：")
        for e in errors:
            print("  " + e)
        return 1
    print("全部校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
