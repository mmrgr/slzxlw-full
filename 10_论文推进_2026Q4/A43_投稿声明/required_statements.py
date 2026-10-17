"""A43: 生成投稿必需声明 (Data/Code Availability, Author Contributions, etc.).

【为什么必须做】
Nature 系列期刊要求主稿含**强制性声明**, 缺失会被编辑部退回 (desk reject) 或要求补件:
  · Data Availability  —— 数据可得性(含 DOI/URL)
  · Code Availability  —— 代码可得性(含仓库/版本)
  · Author Contributions
  · Competing Interests
  · Acknowledgements

当前主稿与 SI **均无这些节**(实测 0 命中)。本脚本从**已知事实**生成草稿:
  · 外部数据来自 Shen et al. 2026 的 Zenodo 复现包 (10.5281/zenodo.22138940, CC-BY)
  · 本项目自有产物在本地仓库 A* 目录, 已建复现清单与六套门禁
  · 作者/贡献/致谢/利益冲突**属于作者个人事实, 不得编造** ⇒ 留占位符并显式标注需作者填写

【纪律】
  · **绝不编造**作者姓名、单位、贡献、基金号;
  · 数据/代码可得性可据实撰写(来源已知);
  · 需人工填写的部分用醒目占位符 [[...]] 标出, 并在门禁中检查是否已填。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"
OUT = HERE / "required_statements.md"
OUTJ = HERE / "required_statements.json"


def main() -> None:
    t0 = time.time()
    md: list[str] = []

    def w(x=""):
        md.append(x)

    w("# 投稿必需声明（草稿）")
    w()
    w("> 自动生成：`python A43_投稿声明/required_statements.py`")
    w()
    w("**⚠️ 使用说明**：Data Availability 与 Code Availability 已据实撰写；")
    w("`[[...]]` 为**必须由作者填写**的个人信息——脚本**绝不编造**姓名、单位、基金号。")
    w("填完后本文件的相关段落应并入主稿（Nature 要求这些声明出现在正文中）。")
    w()
    w("---")
    w()

    # ---------- Data Availability ----------
    w("## Data availability")
    w()
    w("The study uses no new primary measurements. All external data are public and are")
    w("redistributed here only by reference:")
    w()
    w("- The wastewater-treatment-plant inventory, reclaimed-water project catalogue,")
    w("  cooling-water share table, city water-tariff series and capacity-deployment records")
    w("  are all taken from the reproducible source-data package accompanying Shen et al.")
    w("  (2026), released under CC-BY-4.0 at Zenodo:")
    w("  **https://doi.org/10.5281/zenodo.22138940**")
    w("  (workbook `Source_data.xlsx`; sheets `WWTP_data_2020`, `Reclaimed water case`,")
    w("  `Share of cooling water`, `water price(CNY_m-3)`, `Source data 4`).")
    w("- Cooling-water quality limits follow the cited standards **GB/T 50050-2017** and")
    w("  **GB/T 19923-2024** (values tabulated in the Supplementary Information).")
    w("- All model outputs generated in this work — scenario grids, sensitivity designs,")
    w("  bootstrap replicates, figures and the evidence ledger — are contained in the")
    w("  project archive described under *Code availability*, together with SHA-256 hashes")
    w("  of every authoritative artifact (see `A40_投稿包/reproducibility_manifest.md`).")
    w("- Any further data are available from the corresponding author on reasonable request.")
    w()

    # ---------- Code Availability ----------
    w("## Code availability")
    w()
    w("The modelling engine is not redistributed here; analyses were performed against a")
    w("read-only checkout of the AI-UWM engine (no engine source was modified — this is")
    w("asserted and checked in the analysis scripts). All analysis, sensitivity, figure and")
    w("audit code written for this study is available as follows:")
    w()
    w("- Repository: **[[REPOSITORY_URL]]** *(e.g. GitHub/Zenodo DOI for the analysis archive)*")
    w("- Version / commit: **[[COMMIT_OR_VERSION]]**")
    w("- Complete reproduction:")
    w()
    w("  ```bash")
    w('  cd "10_论文推进_2026Q4"')
    w("  python A36_终审/final_gate.py                      # terminal gate, expects all PASS")
    w("  python A40_投稿包/make_reproducibility_manifest.py  # artifact hashes + numeric re-checks")
    w("  python A37_六主图_v4/make_all_figures.py            # regenerates all six main figures")
    w("  python A41_全包审计/package_consistency_check.py    # cross-document consistency")
    w("  python A42_参考文献/references_from_bib.py          # citation ↔ bibliography mapping")
    w("  ```")
    w()
    w("- Environment: Python 3.13.14; numpy 2.4.4; pandas 3.0.5; matplotlib 3.11.2;")
    w("  phreeqpython 1.6.2. The engine is located via `AIUWM_REPO` or a relative layout")
    w("  (hard-coded absolute paths have been removed).")
    w("- Six automated gates ship with the archive; all currently pass. They check: terminal")
    w("  assertions, figure–source consistency (64 checks), artifact hashes and numeric")
    w("  re-computation (17 checks), cross-document consistency, citation integrity, and")
    w("  absence of corrupted control characters.")
    w()

    # ---------- Author contributions ----------
    w("## Author contributions")
    w()
    w("**⚠️ 需作者填写（不得代拟）**")
    w()
    w("- [[Author 1]]: [[conception / model design / analysis / writing]]")
    w("- [[Author 2]]: [[…]]")
    w()
    w("All authors discussed the results and approved the manuscript.")
    w()

    # ---------- Competing interests ----------
    w("## Competing interests")
    w()
    w("**⚠️ 需作者确认**（若确无，保留下述标准表述）")
    w()
    w("The authors declare no competing interests.")
    w()

    # ---------- Acknowledgements ----------
    w("## Acknowledgements")
    w()
    w("**⚠️ 需作者填写**（基金号、数据提供者致谢等）")
    w()
    w('- [[FUNDING: grant number(s) and funder name(s), or "This research received no '
      'specific grant from any funding agency."]]')
    w("- We thank [[names]] for [[contribution]].")
    w("- We acknowledge the authors of Shen et al. (2026) for releasing their source-data")
    w("  package under CC-BY-4.0, which underpins the external anchors in this work.")
    w()

    # ---------- Reporting summary ----------
    w("## Reporting summary")
    w()
    w("**⚠️ Nature 要求随稿提交** *Reporting Summary*（生命科学类为强制；物质/地球科学类")
    w("按期刊要求）。本项目为水系统建模研究，若目标期刊要求，须在线填写对应的")
    w("Reporting Summary 表单。**本脚本不代填**——须由作者在投稿系统中完成。")
    w()

    # ---------- 自检 ----------
    text = "\n".join(md)
    placeholders = re.findall(r"\[\[([^\]]+)\]\]", text)
    w("---")
    w()
    w("## 自检")
    w()
    w(f"- 占位符数量 = **{len(placeholders)}**（必须由作者全部填写后方可投稿）")
    for p in placeholders:
        w(f"  - `[[{p}]]`")
    w()

    OUT.write_text(text, encoding="utf-8")
    OUTJ.write_text(json.dumps({
        "n_placeholders": len(placeholders),
        "placeholders": placeholders,
        "sections": ["Data availability", "Code availability", "Author contributions",
                     "Competing interests", "Acknowledgements", "Reporting summary"],
        "runtime_s": round(time.time() - t0, 1),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print("=" * 76)
    print("A43  投稿必需声明草稿")
    print("=" * 76)
    print(f"  已生成 {len(md)} 行; 占位符 {len(placeholders)} 处需作者填写")
    for p in placeholders:
        print(f"    [[{p[:60]}]]")
    print(f"\n[write] {OUT.name} / {OUTJ.name}")
    # 主稿缺失这些声明 → 非零退出以提示
    ms_txt = MS.read_text(encoding="utf-8")
    missing = [s for s in ("Data availability", "Code availability",
                           "Author contributions", "Competing interests")
               if s.lower() not in ms_txt.lower()]
    print(f"\n主稿仍缺声明: {missing if missing else '无'}")
    # 2026-10-17 修正: 原注释写"非零退出以提示", 但实际恒为 sys.exit(0),
    # 导致缺声明时门禁仍报成功 —— 与门禁第4条(禁止空洞通过)直接冲突。
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
