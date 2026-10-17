# NE-2 结果：「碱度是唯一符号杠杆」是 **baseline 面板的产物**（红队 F-5 成立）

> 脚本：`ne2_panel_robustness.py`｜产物：`ne2_panel_robustness_summary.json` / `_cases.csv` / `_log.txt`

---

## 1. 裁定（先说结论）

> **红队正确。"碱度是唯一符号杠杆"不能写成普适机制，必须限定为"在 baseline 引用档下"。**

| 限值档 | 定义 | IEUA 绑定物种 | LADWP 绑定物种 | 是否存在符号杠杆 |
|---|---|---|---|---|
| **baseline** | 2200 / 700 / 750 / **350** / 175 | **alkalinity** | **alkalinity** | ✅ alkalinity（IEUA） |
| **permissive** | 2600 / 1000 / 750 / **350** / 175 | **alkalinity** | **alkalinity** | ✅ alkalinity（IEUA） |
| **strict** | 1000 / 250 / 450 / **350** / **30** | **silica** | **TDS** | ❌ **NONE** |

⇒ 绑定物种集合：`{baseline: [alkalinity], permissive: [alkalinity], strict: [TDS, silica]}`
⇒ **不随档位保持不变**。

---

## 2. 逐物种「限值/浓度」比（原始证据）

### IEUA RP-1（变更驱动的样本）

| 档 | TDS | chloride | hardness | **alkalinity** | silica | 最小者 |
|---|---:|---:|---:|---:|---:|---|
| baseline | 4.966 | 7.000 | 5.019 | **2.500** | 7.292 | **alkalinity** |
| permissive | 5.869 | 10.000 | 5.019 | **2.500** | 7.292 | **alkalinity** |
| strict | 2.257 | 2.500 | 3.012 | 2.500 | **1.250** | **silica** |

### LADWP AWPF

| 档 | TDS | chloride | hardness | alkalinity | silica | 最小者 |
|---|---:|---:|---:|---:|---:|---|
| baseline | 100.000 | 194.444 | 732.586 | 49.296 | 336.538 | **alkalinity** |
| permissive | 118.182 | 277.778 | 732.586 | 49.296 | 336.538 | **alkalinity** |
| strict | **45.455** | 69.444 | 439.552 | 49.296 | 57.692 | **TDS** |

**为什么 strict 档会改变绑定物种**：strict 档的 **silica 限值压到 30**（baseline 175）
而 **TDS 压到 1000**（baseline 2200），但 **alkalinity 三档都是 350**（未变）。
⇒ 当其他物种的限值被收紧、而碱度限值不变时，碱度就不再是最紧的约束。

---

## 3. 单点扰动检验（只改一个物种浓度 ×0.5 / ×2.0，其余不变，$\varphi$=0.6）

| 档 | 水样 | $dS$ 基准 | TDS | chloride | hardness | alkalinity | silica | 杠杆 |
|---|---|---:|---:|:---:|:---:|:---:|:---:|---|
| baseline | IEUA | −4.194 | − | − | − | **FLIP** | − | **alkalinity** |
| baseline | LADWP | 0 | − | − | − | − | − | NONE |
| permissive | IEUA | −4.194 | − | − | − | **FLIP** | − | **alkalinity** |
| permissive | LADWP | 0 | − | − | − | − | − | NONE |
| **strict** | IEUA | **−30.64** | − | − | − | **−** | − | **NONE** |
| **strict** | LADWP | **+2.821** | − | − | − | − | − | **NONE** |

**两个重要观察**：
1. **strict 档下没有任何单物种扰动能翻转符号**——并非"换了另一个杠杆"，
   而是该档下扰动被别处吸收（各物种余量都变小、相互牵制增强）。
2. **LADWP 在 strict 档下 $dS$ 由 0 变为 +2.821（有害）**——即**换档本身就会改变结论符号**，
   而不需要任何单物种扰动。

---

## 4. 对论文的改写指令

### 4.1 必须改述（原文过强）
- ❌ 原表述："**only one** quantity changes the sign of the outcome — the alkalinity of the
  reclaimed water"（Abstract 与 §7a）
- ✅ 改为：**"在本文采用的引用档（baseline）下**，碱度是唯一能翻转符号的杠杆；
  **该结论不跨档稳健**：在更严的补充水口径档（strict）下，绑定物种变为 silica（IEUA）
  与 TDS（LADWP），且不存在任何单物种符号杠杆。"

### 4.2 必须补充的诚实说明
- "碱度唯一"的**适用域明确为 baseline / permissive 两档**；
- **strict 档下换档本身就翻转 LADWP 的符号**（0 → +2.821）⇒ 结论对档位敏感；
- 因此该结果应表述为**"在一个被明确界定的限值域内识别出的符号杠杆"**，
  而不是"再生水冷却的普适符号机制"。

### 4.3 积极面（仍可主张）
- 在 **baseline 与 permissive 两档**（两者 alkalinity 限值同为 350）结论**一致**，
  说明它至少在**碱度限值不变**的档位间是稳健的；
- 机理（限值/浓度比决定绑定物种）**可复核、可预测**——这本身是有价值的贡献：
  它给出了"何时哪个物种会绑定"的**判别规则**，而不仅是一个经验观察。

---

## 5. 与红队意见的对应

| 红队条目 | 状态 |
|---|---|
| F-5：碱度"唯一杠杆"是否只是当前面板的产物？ | **成立** ⇒ 已量化并改写 |
| 审稿人 3 红线（R10a 重跑） | NE-1 已回应（方向稳健、机制路径依赖） |
| NE-2（换限值档重跑） | ✅ **本次完成** |

---

## 6. 复现

```bash
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4/A38_模拟审稿"
PYTHONIOENCODING=utf-8 python ne2_panel_robustness.py    # <1 s
```

## 7. 仍未闭合

| 项 | 状态 |
|---|---|
| strict 档下"无杠杆"的机理（是否因各物种余量趋同导致相互补偿） | 未分解 |
| NE-3 PHREEQC 温度维 | 待做 |
| NE-4 Sobol bootstrap 置信区间 | 待做 |
| 起点：`city_model.PANELS` 实际只有 `A_engine2 / B_full` 两个**引擎面板**，与本文的**限值档**是不同概念 | 已在脚本中注明，勿混用 |
