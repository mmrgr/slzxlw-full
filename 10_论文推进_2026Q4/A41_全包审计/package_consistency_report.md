# 全包一致性审计报告

> 自动生成：`python A41_全包审计/package_consistency_check.py`
> 状态：**CONSISTENT**（FAIL 0；WARN 8）

## 审计范围

- 主稿 ↔ SI ↔ 六图图注 ↔ 证据台账 ↔ 复现清单（五方交叉）

## FAIL 明细

（无）

## WARN 明细

- '813' (可靠子集) 仅在 SI
- '643' (dS<0) 两处均未出现
- '290' (q>0) 两处均未出现
- '2.55' (恒等式残差) 两处均未出现
- '0.806' (留出 R²) 两处均未出现
- '0.671' (E3 仅化学) 仅在 SI
- '0.861' (E3 基线) 两处均未出现
- 主稿含 10 处待作者填写占位符(投稿前须完成)

## 完整日志

```
====================================================================================
A41  全包一致性审计 (主稿 / SI / 图 / 台账 / 复现清单)
====================================================================================

[1] 已撤回主张: 仅允许出现在撤回语境
    撤回语境命中 4 处; 违规 0 处

[2] 关键数字: 主稿 / SI 双出现检查
    [WARN] 可靠子集             '813' 仅 SI
    [WARN] dS<0             '643' 两处均无
    [OK]   dS=0             '36' 主稿+SI
    [WARN] q>0              '290' 两处均无
    [WARN] 恒等式残差            '2.55' 两处均无
    [WARN] 留出 R²            '0.806' 两处均无
    [WARN] E3 仅化学           '0.671' 仅 SI
    [WARN] E3 基线            '0.861' 两处均无
    [OK]   B3 占比            '28.4' 主稿+SI
    [OK]   冷却水占比            '0.258' 主稿+SI
    [OK]   工业水价             '1.550' 主稿+SI
    [OK]   再生水/水价           '1.56' 主稿+SI

[3] 图注声明 vs 主稿
    [PASS] Fig2 碱度绑定限 cited/permissive  (图注=True, 主稿=True)
    [PASS] Fig4 折外为候选判据  (图注=True, 主稿=True)
    [PASS] Fig5 NE-4 区间  (图注=True, 主稿=True)
    [PASS] Fig5 NE-2 三档  (图注=True, 主稿=True)
    [PASS] Fig6 WP8/WP9/WP10/WP11  (图注=True, 主稿=True)

[4] 证据台账 vs 复现清单
    [PASS] 复现清单 产物 28(缺 0), 数字复算 17/17
    状态 = ALL_CHECKS_PASS
    证据台账 权威产物条目 = 34

[5] SI 章节编号连续性
    [PASS] S1–S21 共 21 节, 连续=True

[6] SI 是否引用本轮全部实验包
    [PASS] A29 被引用=True
    [PASS] A30 被引用=True
    [PASS] A31 被引用=True
    [PASS] A32 被引用=True
    [PASS] A33 被引用=True
    [PASS] A34 被引用=True
    [PASS] A38 被引用=True
    [PASS] A39 被引用=True

[7] References 与内联引用一致性
    主稿 References 条目 = 17
    正文内联引用(去重) = 15
      - Alissa (2025)
      - Alston (2026)
      - Badruzzaman (2022)
      - Behzadian (2015)
      - Chen (2023)
      - Garrido-Baserba (2024)
      - Han (2026)
      - Lei (2025)
      - Mytton (2021)
      - Renouf (2018)
      - Saleh (2026)
      - Shen (2026)
      - Siddik (2021)
      - Wang (2026)
      - Xiao (2025)
    [PASS] 引用↔文献表一致 (缺失 0)

[8] 摘要长度
    Abstract 词数 = 300 (上限 300, 含撤回/限制披露的宽限)
    [PASS] 摘要长度

[9] 投稿必需声明
    [PASS] Data availability
    [PASS] Code availability
    [PASS] Author contributions
    [PASS] Competing interests
    [PASS] Acknowledgements

[10] 稿件结构完整性
    正文图注引用数 = 6 (应为 6)
    [PASS] 章节 Abstract
    [PASS] 章节 Introduction
    [PASS] 章节 Results
    [PASS] 章节 Discussion
    [PASS] 章节 Methods
    [PASS] 章节 References

====================================================================================
裁定
====================================================================================
  FAIL = 0
  WARN = 8
    ⚠ '813' (可靠子集) 仅在 SI
    ⚠ '643' (dS<0) 两处均未出现
    ⚠ '290' (q>0) 两处均未出现
    ⚠ '2.55' (恒等式残差) 两处均未出现
    ⚠ '0.806' (留出 R²) 两处均未出现
    ⚠ '0.671' (E3 仅化学) 仅在 SI
    ⚠ '0.861' (E3 基线) 两处均未出现
    ⚠ 主稿含 10 处待作者填写占位符(投稿前须完成)

  总状态: CONSISTENT
  (0.0s)
```
