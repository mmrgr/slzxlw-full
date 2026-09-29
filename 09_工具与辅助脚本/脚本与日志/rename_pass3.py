"""Pass 3: neutralise every remaining WaterMet prose occurrence."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src")


def edit(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in t:
            print(f"  MISS [{rel}]: {old[:70]}")
            continue
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("ok", rel)


edit("AI_DATA_CENTER_RESEARCH_CN.md", [
    ("# WaterMet² AI算力—城市水资源承载力研究指南",
     "# AI-UWM：AI 算力—城市水资源承载力研究指南"),
    ("本扩展保留 WaterMet² 的战略级、日尺度、质量守恒建模定位。WaterMet² 原始开放论文将模型定义为",
     "本框架保持战略级、日尺度、质量守恒的建模定位。公开文献将该类城市水系统性能模型定义为"),
    ("- [WaterMet² 原始开放论文（DWES, 2014）](https://dwes.copernicus.org/articles/7/63/2014/)",
     "- [Behzadian 等（2014）：城市水系统定量绩效模型公开论文，DOI 10.5194/dwes-7-63-2014](https://doi.org/10.5194/dwes-7-63-2014)"),
    ("- [WaterMet² 城市水代谢论文记录](https://repository.uwl.ac.uk/id/eprint/1824/)",
     "- [城市水代谢相关论文记录（UWL 机构库 1824）](https://repository.uwl.ac.uk/id/eprint/1824/)"),
    ("- [Water reuse 与 WaterMet² 综合框架研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC7028841/)",
     "- [再生水回用与城市水系统综合框架研究（PMC7028841）](https://pmc.ncbi.nlm.nih.gov/articles/PMC7028841/)"),
])

edit("FUNCTIONAL_COVERAGE_CN.md", [
    ("# WaterMet² 公开功能对照表", "# AI-UWM 功能覆盖对照表"),
    ("它与原 WaterMet² 的定位一致", "它与公开文献所述战略模型的定位一致"),
])

edit("output/网络资料与项目功能审计.md", [
    ("# WaterMet² 网络资料补充与项目功能最终审计",
     "# 网络资料补充与项目功能最终审计"),
    ("原 WaterMet² 二进制、工程格式与 GUI 的逐项兼容",
     "与原始闭源程序的二进制、工程格式与 GUI 的逐项兼容"),
    ("可重建的 WaterMet² 战略模型及 DSS 功能", "可重建的战略级城市水系统模型及 DSS 功能"),
    ("公开论文将 WaterMet² 定义为", "公开论文将该类城市水系统模型定义为"),
    ("描述了 WaterMet² 模型、桌面软件和 Toolkit", "描述了该模型、桌面软件和 Toolkit"),
    ("需由 WaterMet² 评估", "需由该类 models评估".replace("models", "绩效模型")),
    ("据此，核心 WaterMet²、风险扩展、Toolkit", "据此，核心代谢模型、风险扩展、Toolkit"),
    ("`AI-UWM.dll`", "`原始闭源动态库`"),
])

edit("REPRODUCTION_REPORT_CN.md", [
    ("# WaterMet² 论文精读与复现报告", "# 城市水系统定量绩效模型：论文精读与复现报告"),
    ("WaterMet² 的关键创新有三点：", "该模型方法的关键创新有三点："),
    ("D33.2 说明 WaterMet² 是 C#/.NET 闭源程序，核心封装为 `AI-UWM.dll`；",
     "D33.2 说明其参考实现是 C#/.NET 闭源程序，核心封装为动态库；"),
    ("不是 WaterMet² 源码", "不是该模型的源码"),
    ("- CORDIS WaterMet² page: https://cordis.europa.eu/article/id/121974-the-watermet-tool-",
     "- CORDIS 项目报道：https://cordis.europa.eu/article/id/121974"),
])

edit("项目文件说明.md", [
    ("# WaterMet² 项目文件说明", "# AI-UWM 项目文件说明"),
    ("# WaterMet² 参数数据库和 Oslo 参数", "# 参数数据库和 Oslo 参数"),
])

edit("validation_artifacts/VALIDATION_REPORT_CN.md", [
    ("# WaterMet² 合成数据全流程验证报告", "# AI-UWM 合成数据全流程验证报告"),
])

edit("README.md", [
    ("它覆盖公开文献描述的 WaterMet² 分析链：", "它覆盖公开文献描述的城市水系统性能分析链："),
    ("原始 WaterMet² 是闭源 C# 软件", "公开文献所述方法的参考实现是闭源 C# 软件"),
    ("把部分风险列为 WaterMet² 直接计算", "把部分风险列为模型直接计算"),
    ("WaterMet² 是战略代谢模型", "本框架是战略代谢模型"),
])
