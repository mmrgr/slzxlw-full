"""Rewrite the README identity block for AI-UWM."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src")
p = ROOT / "README.md"
t = p.read_text(encoding="utf-8")

OLD_HEAD = """# WaterMet² 开放复现与城市水系统分析框架

这是依据 Behzadian 与 Kapelan（2015）论文、TRUST D33.2 官方手册和 Oslo 案例报告重写的 Python 实现。它覆盖公开文献描述的城市水系统性能分析链：日尺度水量与污染物质量守恒、四级空间表达、供水—用水—雨洪—污水—回用、能源/材料/化学品、环境影响、成本、资源回收、干预方案、校准、不确定性、CP/AHP 多准则排序和场景决策支持。

公开文献所述方法的参考实现是闭源 C# 软件，论文使用的 Oslo SCADA 日序列也未公开，因此本项目不能声称与原二进制逐行或逐日数值完全相同；但公开方法和功能都已有可审计实现。完整对照见 [FUNCTIONAL_COVERAGE_CN.md](FUNCTIONAL_COVERAGE_CN.md)，论文案例复现边界见 [REPRODUCTION_REPORT_CN.md](REPRODUCTION_REPORT_CN.md)。
""".replace("\n", "\r\n")

NEW_HEAD = """# AI-UWM：面向 AI 算力影响研究的城市水系统代谢与承载力分析框架

本项目是一套**独立编写**的城市水系统日尺度代谢模拟与承载力分析框架（Python 引擎 + Web Studio），核心用途是评估 **AI 数据中心进入城市之后**的取水—给水—排水—再生水回路响应、多时间尺度承载边界（CAWCC）以及水—能耦合瓶颈迁移。

除 AI 算力专题外，框架本身覆盖完整的城市水系统性能分析链：日尺度水量与污染物质量守恒、四级空间表达（Resource → Supply → Local area → Indoor）、供水—用水—雨洪—污水—回用、能源/材料/化学品、环境影响、全生命周期成本、资源回收、干预方案、校准、不确定性、CP/AHP 多准则排序与场景决策支持。

## 方法学来源与合规声明

本框架的**方法学思路**来源于公开发表的城市水系统定量绩效模型文献与公开项目文档，全部为独立编码实现，**不含任何第三方闭源代码、二进制组件或官方私有工程文件格式**：

| 来源 | 标识 |
|---|---|
| Behzadian & Kapelan (2015) 城市水代谢与战略规划论文 | DOI: <https://doi.org/10.1016/j.resconrec.2015.03.015> |
| Behzadian 等 (2014) 城市水系统定量绩效模型公开论文 | DOI: <https://doi.org/10.5194/dwes-7-63-2014> |
| TRUST D33.2 最终报告（Exeter 机构库） | Handle: <https://hdl.handle.net/10871/17062> |
| TRUST Oslo 案例报告（Exeter 机构库） | Handle: <https://hdl.handle.net/10871/17060> |
| TRUST DSS 方法论文 | DOI: <https://doi.org/10.2166/ws.2015.167> |

上述文献所述方法公开的参考实现是闭源 C# 程序，其所使用的 Oslo SCADA 日序列也未公开。因此本项目**不声称**与任何闭源二进制逐行或逐日数值等价，也不提供对第三方动态库 ABI、函数签名或私有工程格式的兼容层——只保证公开方法与公开功能具备可审计、可运行、可测试的独立实现。

- 功能覆盖逐项对照见 [FUNCTIONAL_COVERAGE_CN.md](FUNCTIONAL_COVERAGE_CN.md)
- 论文案例的复现边界见 [REPRODUCTION_REPORT_CN.md](REPRODUCTION_REPORT_CN.md)
- AI 算力专题的方法与实验设计见 [AI_DATA_CENTER_RESEARCH_CN.md](AI_DATA_CENTER_RESEARCH_CN.md)
- `references/` 仅收录来源元数据；受版权保护的论文与报告 PDF 不随仓库分发，请通过上表官方地址获取。
""".replace("\n", "\r\n")

if OLD_HEAD not in t:
    raise SystemExit("head block not matched")
t = t.replace(OLD_HEAD, NEW_HEAD, 1)

OLD_REFS = """主要公开依据：

- 2015 论文 DOI：<https://doi.org/10.1016/j.resconrec.2015.03.015>

- 2014 开放论文与模型概述：<https://doi.org/10.5194/dwes-7-63-2014>

- Exeter 官方仓储的功能需求：<https://ore.exeter.ac.uk/repository/handle/10871/17302>

- `references/` 仅发布来源元数据；论文和报告 PDF 因版权原因不随公开仓库上传，可从上述官方地址下载。
""".replace("\n", "\r\n")
if OLD_REFS in t:
    t = t.replace(OLD_REFS, "", 1)
    print("removed legacy reference block")
else:
    print("MISS: legacy reference block")

p.write_text(t, encoding="utf-8")
print("README rewritten, lines =", len(t.splitlines()))
