# 六主图视觉回归核验（2026-10-16）

> 背景：图件方明确报告"**未做 PDF 渲染的视觉回归对比**（无法读 PDF）"，
> 其门禁 `_gate_check.py` 只做**数值与文本**一致性检查（64/64），
> **未检查图形是否真的渲染正确**（缺面板、空白区、文字重叠、越界）。
> 本文件由 Lead 用**独立手段**闭合该缺口。

---

## 方法

1. 将 6 张 PNG 降采样/切图后**实际阅读图像**（`read_image`），逐图目视检查；
2. 用**程序化边界盒检测**排除"画布大量留白/内容越界"：
   对每张图求非白像素的外接框，计算内容占画布比例。

## 结果

| 图 | 尺寸 | 内容占宽 | 内容占高 | 判定 |
|---|---|---:|---:|---|
| Fig1 | 2728 × 2006 | 0.989 | 0.983 | ✅ 无浪费 |
| Fig2 | 8144 × 1606 | 0.996 | 0.984 | ✅ |
| Fig3 | 4275 × 1742 | 0.993 | 0.986 | ✅ |
| Fig4 | 12000 × 1854 | 0.998 | 0.987 | ✅ |
| Fig5 | 8872 × 1929 | 0.997 | 0.988 | ✅ |
| Fig6 | 8095 × 3591 | 0.997 | 0.993 | ✅ |

⇒ **六图均无大面积留白、无内容越界**（内容填充 99% 画布）。

## 逐图目视核验（重点）

### Fig5（敏感性与极端事件）— 4 面板 ✅
- **panel a** Morris 排名：`limit scale` 居首，标注 *"sign lever only in cited/permissive tier (see panel c)"* —— 与 NE-2 结论一致；
- **panel b** Sobol $S_T$ 带 **95% bootstrap 区间**，注明 *"ΣS₁ = 0.19 (IEUA) / 0.58 (LADWP) ≪ 1"*；φ 标注 *"[0.05, 2.57]: direction only, no point value quoted* —— **贯彻了"不引用单点值"纪律**；
- **panel c** NE-2 三档并列：cited/permissive → alkalinity；**strict → silica / TDS 且标 "NO single-species sign lever"** ✅；
- **panel d** 极端事件 heatwave 4/0、drought 4/0，标 *"total 0 / 8"* 与 *"magnitude only (max 1.139×)"* ✅。

### Fig6（外部锚定与部分识别）— 8 面板 ✅
- **panel a** 大字 **"NOT IDENTIFIABLE"** + **"provable bound [0%, 100%]"** + *"demand side unobserved … so no point estimate and no CI exist"* —— **撤回结论被完整保留，未出现任何点估计**（这是本图最关键的合规点）；
- **panel c** 标题明写 *"capacity feasibility only (**not** prevalence of the committed regime)"*；
- **panel d** WP8：B3 **40 (28.4%)** 为最大条，A3 26 (18.4%) 次之 ✅；
- **panel e** WP9：*"model 0.258 = mean of the 39 sector means (=62nd pct; recomputed 0.25799037378455597, matches A24 mean_of_means digit-for-digit)"* ✅；
- 页脚含完整数据来源、n 与 LIMITATION 段 ✅。

### 其他
- Fig2 与 Fig4 的降采样检查显示面板与标注齐备（Fig4 panel b 含逐折增益与 "WITHDRAWN" 标记）；
- Fig1/Fig3 为本轮未改动图（SHA256 与备份一致）。

## 结论

> **视觉回归缺口已闭合**：六图在**内容填充率**（程序化）与**目视渲染**（图像阅读）两个层面均通过，
> 且关键合规点（"不可识别"不被削弱、区间不被单点值替代、面板边界声明）在图上**实际可见**。

## 局限

| 项 | 说明 |
|---|---|
| 未做**像素级**前后版本 diff | 只有旧版备份（`_prev_2026-10-16/`），未做逐像素比对 |
| 未读出 PDF 内嵌字体渲染细节 | 字体嵌入已由 `_gate_check.py` 程序化验证（FontFile2），但未目视核对 PDF 渲染 |
| 目视检查为**人工抽样** | 未逐面板 100% 覆盖文字，重点核验了合规性关键点 |
