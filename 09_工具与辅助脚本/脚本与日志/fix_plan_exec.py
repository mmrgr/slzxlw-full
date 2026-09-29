"""把 v4 新增的两个实验段纳入第 13 节的执行方案（命令 + 产物表）。"""
from __future__ import annotations

from pathlib import Path

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")

# --- 13.1 命令序列：在「一次跑完」之后追加扩展块 ---------------------------
CMD_ANCHOR = """# 6) 一次跑完（两域约 35–40 分钟）
python scripts/run_r2.py --domains ha,co
```"""

CMD_NEW = """# 6) 一次跑完（两域约 35–40 分钟）
python scripts/run_r2.py --domains ha,co

# 7) 扩展块：城市侧参数敏感性 + 能源富集补充情景（v4 新增，约 35 分钟）
#    注意：需把 scripts/ 一并加入 PYTHONPATH——本脚本复用 run_r2.py 的
#    口径定义（CAPACITIES_SCAN / daily_constraints / annual_constraints），
#    以保证与主实验完全同一口径。
PYTHONPATH="src;scripts" python scripts/run_r2_extra.py --domains ha,co --sobol-samples 64

#    也可分块单独跑：
#    PYTHONPATH="src;scripts" python scripts/run_r2_extra.py --blocks city
#    PYTHONPATH="src;scripts" python scripts/run_r2_extra.py --blocks energy
```"""

# --- 13.2 产物表：追加 C6 与 J 两段 ---------------------------------------
ART_ANCHOR = "| C5 | 再生水**产水量**边际曲线（真杠杆） | `reuse_production_marginal_curve.csv` |"

ART_NEW = (
    "| C5 | 再生水**产水量**边际曲线（真杠杆） | `reuse_production_marginal_curve.csv` |\n"
    "| C6 | 城市侧参数敏感性（Morris 双指标 + Sobol） | `city_morris.csv`, `city_sobol.csv` |\n"
    "| J | 能源富集补充情景对比（仅 HA 端叠加） | `energy_rich_comparison.csv` |"
)

# --- 13.3 执行顺序：把扩展块并入 P2/P3 ------------------------------------
ORD_ANCHOR = "3. **P3 主扫描**：P2 全通过后才引用 CAWCC、瓶颈链、边际曲线、反馈链的结果。"

ORD_NEW = (
    "3. **P3 主扫描**：P2 全通过后才引用 CAWCC、瓶颈链、边际曲线、反馈链的结果。\n"
    "4. **P4 稳健性（v4 新增）**：`run_r2_extra.py` 补两块——（a）城市侧参数的\n"
    "   Morris/Sobol，回答\"头号结论是否依赖城市侧设定值\"；（b）能源富集补充情景，\n"
    "   把电力约束从瓶颈链中摘掉单独观察水系统。**这两块在 v3 里是缺失的**：\n"
    "   前者使核心结论没有不确定性支撑，后者是定义了却从未执行的悬空目标。"
)


def main() -> None:
    raw = DOC.read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")

    for anchor, new, note in (
        (CMD_ANCHOR, CMD_NEW, "13.1 命令序列"),
        (ART_ANCHOR, ART_NEW, "13.2 产物表"),
        (ORD_ANCHOR, ORD_NEW, "13.3 执行顺序"),
    ):
        if anchor not in text:
            print(f"  [MISS] {note}")
            continue
        text = text.replace(anchor, new, 1)
        print(f"  [OK  ] {note}")

    DOC.write_bytes(text.replace("\n", eol).encode("utf-8"))
    print("写入完成")


if __name__ == "__main__":
    main()
