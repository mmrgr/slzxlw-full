# 外部数据清单与核验记录（A24）

> 本文件记录本项目**实际取得**的外部数据，供复现与审稿核验。所有条目均经过下载/解析验证。

---

## 1. Shen et al. 2026 — 中国集中式污水处理系统（★ 关键锚点）

| 项 | 内容 |
|---|---|
| 论文 | "China's Centralized Wastewater Treatment System Reaches Efficiency Limits in Tackling Water Scarcity" |
| 期刊 | *Nature Water* (2026-10-12) |
| 论文 DOI | `10.1038/s44221-026-00727-5` |
| 数据仓库 | Zenodo `10.5281/zenodo.22138940` |
| 许可 | **CC-BY-4.0**（可再分发、可再利用，须署名） |
| 归档文件 | `CWTS_code_JJS.zip` — 2 683 047 字节（记录标注 2.7 MB） |
| 关键数据文件 | `source_data/Source_data.xlsx`（2 882 698 字节，13 个工作表） |
| 本地路径 | `C:/Users/mmrgr/Desktop/论文/_ext_data/`（未入库：体积大，按需重新下载） |

### 下载命令（可复现）

```bash
mkdir -p _ext_data && cd _ext_data
curl -sL -o CWTS_code_JJS.zip \
  "https://zenodo.org/records/22138940/files/CWTS_code_JJS.zip?download=1"
# 校验: 应为 2683047 字节
python -c "import zipfile; z=zipfile.ZipFile('CWTS_code_JJS.zip'); z.extractall('.')"
```

### 核验结果

| 核验项 | 结果 |
|---|---|
| 下载字节数 | 2 683 047（与记录 2.7 MB 一致）✅ |
| `WWTP_data_2020` 行数 | **10 826**（与论文标题所述 10 826 座一致）✅ |
| 内部一致性 | `Load Rate` 列 ↔ `实际年处理量 / 365 / 设计能力`，相关系数 **1.0000** ✅ |
| 工作表清单 | 13 个（含 `Data source` / `WWTP_data_2020` / `Reclaimed water case` 等） |

### 关键实测分布（已用于 A24）

| 量 | 值 |
|---|---|
| 设计能力 | 中位 **8.0** ML/d（P25 1.4 / P75 25 / P90 60）；合计 268 599 ML/d |
| 负荷率 | 中位 **0.594**（P10 0.092 / P75 0.83 / P90 0.973；>1 占 6.23%） |
| 工业冷却水占比（39 部门） | 部门均值中位 **0.184** |
| 城市水价（n = 39 083） | 中位 **1.45** CNY/m³（P10 0.70 / P90 4.35） |

### 用途与限制

- **用途**：约束模型参数 $P_0$ 的量级（定位到真实 P80.9 百分位）；界定再生水**供给扩张的物理空间**。
- **限制**：为**中国**数据；负荷率是**生产侧**量，不能映射为 A17 分支占比（方向相反，已撤回该用法，见 `A24_外部锚定报告.md` §3）。

---

## 2. 既有水质来源（A4/A14，本项目前期已取得）

| 来源 | 类型 | 说明 |
|---|---|---|
| IEUA RP-1 (2025) | utility report | 三级再生水，5 项离子完整（TDS 443 / Cl 100 / hardness 149.4 / alk 140 / silica 24） |
| LADWP AWPF (2012) | utility report | RO 产水，5 项完整（TDS 22 / Cl 3.6 / hardness 1.02 / alk 7.1 / silica 0.52） |
| Figshare RW (2025) | open dataset | 高盐再生水，3 项（TDS 1378 / Cl 313.7 / hardness 538.5）；缺 alkalinity、silica |
| Figshare BW (2025) | open dataset | 苦咸水，非再生水；仅作边界对照 |
| AI-UWM model assumption | model assumption | ⚠ 仅 2 项（TDS 650 / Cl 130）；缺 hardness/alkalinity/silica ⇒ 按 0 计，限值不触发。建议主扫描剔除或明确标注 |

---

## 3. 数据分级声明

| 级别 | 定义 | 本项目中的例子 |
|---|---|---|
| `observed` | 实测、有公开来源 | Shen 2026 的 10 826 座厂；IEUA/LADWP 水质 |
| `literature` | 公开文献/标准的准则值 | GB/T 50050-2017、GB/T 19923-2024；GSA 实测 CoC 上界 |
| `assumption` | 模型假设，无公开来源 | `AI-UWM model assumption` 水样；占位限值；成本声明值 |

**纪律**：三类严格区分，不得混称。任何 `assumption` 不得写作"实测"或"公开数据"。
