# -*- coding: utf-8 -*-
"""一次性从 HEAD 版 README 重建干净的去名 README（LF 换行，不复写已经破损的工作区版本）。"""
import io
import re
import subprocess

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"

# 1) 取 HEAD 原始 README
raw = subprocess.check_output(["git", "show", "HEAD:README.md"], cwd=ROOT)
src = raw.decode("utf-8").replace("\r\n", "\n")
lines = src.split("\n")

# 2) 头部整体替换：标题 + 导语 + “主要公开依据” -> 新标题 + 导语 + “方法学来源与合规声明”
anchor = next(i for i, l in enumerate(lines) if l.startswith("## 1. 安装与验证"))
body = lines[anchor:]

NEW_HEAD = """# AI-UWM：面向 AI 算力影响研究的城市水系统代谢与承载力分析框架

本项目是一套**独立编写**的城市水系统日尺度代谢模拟与承载力分析框架（Python 引擎 + Web Studio），核心用途是评估 **AI 数据中心进入城市之后**的取水—给水—排水—再生水回路响应、多时间尺度承载边界（CAWCC）以及水—能耦合瓶颈迁移。能力覆盖日尺度水量与污染物质量守恒、四级空间表达、供水—用水—雨洪—污水—回用、能源/材料/化学品、环境影响、成本、资源回收、干预方案、校准、不确定性、CP/AHP 多准则排序和场景决策支持。

公开文献所述方法的参考实现是闭源 C# 软件，论文使用的 Oslo SCADA 日序列也未公开，因此本项目不声称与任何闭源二进制逐行或逐日数值等价；但公开方法涉及的功能均有可审计实现。功能覆盖对照见 [FUNCTIONAL_COVERAGE_CN.md](FUNCTIONAL_COVERAGE_CN.md)，案例复现边界见 [REPRODUCTION_REPORT_CN.md](REPRODUCTION_REPORT_CN.md)。

## 方法学来源与合规声明

本框架的**方法学思路**参考了公开发表的城市水系统定量绩效模型文献与公开项目文档，**全部为独立编码实现**：不含任何第三方源代码、二进制组件或私有工程文件格式，也未使用任何受商标保护的产品名称作为本项目的包名、命令名或产品名。

| 来源 | 标识 |
|---|---|
| 城市水代谢与战略规划论文（Behzadian & Kapelan, 2015） | DOI: <https://doi.org/10.1016/j.resconrec.2015.03.015> |
| 城市水系统定量绩效模型论文（Behzadian 等, 2014） | DOI: <https://doi.org/10.5194/dwes-7-63-2014> |
| 城市新陈代谢长期规划决策支持系统论文（Morley 等, 2015） | DOI: <https://doi.org/10.2166/ws.2015.167> |
| Exeter 官方仓储的功能需求文档 | <https://ore.exeter.ac.uk/repository/handle/10871/17302> |

`references/` 仅发布来源元数据；论文和报告 PDF 因版权原因不随公开仓库上传，可从上述官方地址下载。

## Windows 一键打开

日常使用只需双击项目根目录中的：

```text
启动 AI-UWM Studio.cmd
```

程序会自动检查依赖、构建网页、启动模型服务并打开
<http://127.0.0.1:8000>。现在前端和 API 由同一个 Python 进程提供，不再需要手动启动两个终端。

第一次启动可能需要几分钟安装依赖；以后通常会直接打开。关闭启动程序窗口即可停止系统。目录用途见 [项目文件说明.md](项目文件说明.md)，自有数据操作教程见 [frontend/README.md](frontend/README.md)。

"""

new = NEW_HEAD + "\n".join(body)

# 3) 精确句子级替换（先长后短，逐条断言命中）
PRECISE = [
    # 简介/产品名
    ("项目包含 React + TypeScript 的 WaterMet² Studio，",
     "项目包含 React + TypeScript 的 AI-UWM Studio，"),
    # Toolkit 示例
    ("from watermet2_repro import WaterMet2Toolkit",
     "from aiuwm import AIUWMToolkit"),
    ("toolkit = WaterMet2Toolkit.open(", "toolkit = AIUWMToolkit.open("),
    ("它提供原 Toolkit 的高层用途，但不声称兼容原 `WaterMet2.dll/Toolkit.dll` ABI 或函数签名。",
     "它提供同类工具包的高层用途，但不声称兼容任何闭源参考实现的动态库 ABI 或函数签名。"),
    # 风险边界说明
    ("官方 2012 功能需求把部分风险列为 WaterMet² 直接计算，",
     "公开功能需求把部分风险列为模型直接计算，"),
    # 适用边界
    ("**：WaterMet² 是战略代谢模型，不是 EPANET/SWMM 的详细水力替代品。",
     "**：本框架是战略代谢模型，不是 EPANET/SWMM 的详细水力替代品。"),
    # 数据文件
    ("- `data/watermet2_database.json`：官方附录的能源、材料、化学品和修复系数。",
     "- `data/uwm_database.json`：`references/` 所列来源文献附录给出的能源、材料、化学品和修复系数默认值。"),
    ('  "database_file": "../../data/watermet2_database.json",',
     '  "database_file": "../../data/uwm_database.json",'),
    # CLI / 包名
    ("当前验证结果为 `49 passed`。安装后可使用 `watermet2` 命令；若环境没有刷新命令入口，可用 `python -m watermet2_repro.cli` 替代。",
     "当前验证结果为 Python 单元测试全部通过（前端 `dist/` 需先构建，否则 Studio 静态资源一项会因缺少构建产物而失败）。安装后可使用 `aiuwm` 命令；若环境没有刷新命令入口，可用 `python -m aiuwm.cli` 替代。"),
]

for old, rep in PRECISE:
    if old not in new:
        raise SystemExit("PRECISE MISS: %r" % old[:70])
    new = new.replace(old, rep)

# 4) 剩余命令 token：行首/代码块内的 watermet2 CLI
new = re.sub(r"(?m)^watermet2 ", "aiuwm ", new)
new = new.replace("watermet2-api", "aiuwm-api")

# 5) 兜底：任何残留词形统一替换（正常情况下不应触发）
FALLBACK = [
    ("watermet2_repro", "aiuwm"),
    ("watermet2_database", "uwm_database"),
    ("WaterMet2Toolkit", "AIUWMToolkit"),
    ("WaterMet² Studio", "AI-UWM Studio"),
    ("WaterMet2 Studio", "AI-UWM Studio"),
    ("watermet2", "aiuwm"),
    ("WaterMet2", "AI-UWM"),
    ("WaterMet²", "该参考实现"),
    ("WATERMET2", "AIUWM"),
]
for old, rep in FALLBACK:
    if old in new:
        print("FALLBACK HIT:", old)
        new = new.replace(old, rep)

low = new.lower()
assert "watermet" not in low, "still contains watermet"

# 6) 写回（LF，与 HEAD 一致）
target = ROOT + "/README.md"
with io.open(target, "w", encoding="utf-8", newline="\n") as f:
    f.write(new)

out = io.open(target, encoding="utf-8", newline="").read()
print("written:", target)
print("lines:", len(out.splitlines()), " CRLF:", out.count("\r\n"), " LF:", out.count("\n"))
print("watermet occurrences:", len(re.findall("watermet", out, re.I)))
