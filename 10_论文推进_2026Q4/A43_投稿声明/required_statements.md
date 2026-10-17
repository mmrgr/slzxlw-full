# 投稿必需声明（草稿）

> 自动生成：`python A43_投稿声明/required_statements.py`

**⚠️ 使用说明**：Data Availability 与 Code Availability 已据实撰写；
`[[...]]` 为**必须由作者填写**的个人信息——脚本**绝不编造**姓名、单位、基金号。
填完后本文件的相关段落应并入主稿（Nature 要求这些声明出现在正文中）。

---

## Data availability

The study uses no new primary measurements. All external data are public and are
redistributed here only by reference:

- The wastewater-treatment-plant inventory, reclaimed-water project catalogue,
  cooling-water share table, city water-tariff series and capacity-deployment records
  are all taken from the reproducible source-data package accompanying Shen et al.
  (2026), released under CC-BY-4.0 at Zenodo:
  **https://doi.org/10.5281/zenodo.22138940**
  (workbook `Source_data.xlsx`; sheets `WWTP_data_2020`, `Reclaimed water case`,
  `Share of cooling water`, `water price(CNY_m-3)`, `Source data 4`).
- Cooling-water quality limits follow the cited standards **GB/T 50050-2017** and
  **GB/T 19923-2024** (values tabulated in the Supplementary Information).
- All model outputs generated in this work — scenario grids, sensitivity designs,
  bootstrap replicates, figures and the evidence ledger — are contained in the
  project archive described under *Code availability*, together with SHA-256 hashes
  of every authoritative artifact (see `A40_投稿包/reproducibility_manifest.md`).
- Any further data are available from the corresponding author on reasonable request.

## Code availability

The modelling engine is not redistributed here; analyses were performed against a
read-only checkout of the AI-UWM engine (no engine source was modified — this is
asserted and checked in the analysis scripts). All analysis, sensitivity, figure and
audit code written for this study is available as follows:

- Repository: **[[REPOSITORY_URL]]** *(e.g. GitHub/Zenodo DOI for the analysis archive)*
- Version / commit: **[[COMMIT_OR_VERSION]]**
- Complete reproduction:

  ```bash
  cd "10_论文推进_2026Q4"
  python A36_终审/final_gate.py                      # terminal gate, expects all PASS
  python A40_投稿包/make_reproducibility_manifest.py  # artifact hashes + numeric re-checks
  python A37_六主图_v4/make_all_figures.py            # regenerates all six main figures
  python A41_全包审计/package_consistency_check.py    # cross-document consistency
  python A42_参考文献/references_from_bib.py          # citation ↔ bibliography mapping
  ```

- Environment: Python 3.13.14; numpy 2.4.4; pandas 3.0.5; matplotlib 3.11.2;
  phreeqpython 1.6.2. The engine is located via `AIUWM_REPO` or a relative layout
  (hard-coded absolute paths have been removed).
- Six automated gates ship with the archive; all currently pass. They check: terminal
  assertions, figure–source consistency (64 checks), artifact hashes and numeric
  re-computation (17 checks), cross-document consistency, citation integrity, and
  absence of corrupted control characters.

## Author contributions

**⚠️ 需作者填写（不得代拟）**

- [[Author 1]]: [[conception / model design / analysis / writing]]
- [[Author 2]]: [[…]]

All authors discussed the results and approved the manuscript.

## Competing interests

**⚠️ 需作者确认**（若确无，保留下述标准表述）

The authors declare no competing interests.

## Acknowledgements

**⚠️ 需作者填写**（基金号、数据提供者致谢等）

- [[FUNDING: grant number(s) and funder name(s), or "This research received no specific grant from any funding agency."]]
- We thank [[names]] for [[contribution]].
- We acknowledge the authors of Shen et al. (2026) for releasing their source-data
  package under CC-BY-4.0, which underpins the external anchors in this work.

## Reporting summary

**⚠️ Nature 要求随稿提交** *Reporting Summary*（生命科学类为强制；物质/地球科学类
按期刊要求）。本项目为水系统建模研究，若目标期刊要求，须在线填写对应的
Reporting Summary 表单。**本脚本不代填**——须由作者在投稿系统中完成。
