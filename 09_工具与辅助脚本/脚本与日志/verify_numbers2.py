"""Second verification pass: dry-cooling PUE penalty + annual vs peak water
for wet-first vs dry-first hybrid, checked against Karimi2022 and Ren2026.
"""
rho, cp, Lv = 1.0e3, 4.186e3, 2.45e6

def water(C_IT, LF, PUE, f_wet, CoC=5.0, drift_pct=0.05, dT=5.0, eta=0.85, xi_h=1.0):
    P_IT = C_IT * LF
    Q = xi_h * PUE * P_IT
    Q_wet = f_wet * Q
    E = eta * Q_wet * 1e6 / Lv * 86400 / 1000          # m3/d
    V = Q_wet * 1e6 / (rho * cp * dT) if Q_wet > 0 else 0.0
    D = drift_pct / 100.0 * V * 86400
    B = E / (CoC - 1.0) if CoC > 1 else 0.0
    M = E + B + D
    WUE = M * 1000 / (P_IT * 1e3 * 24)
    return M, WUE, P_IT, PUE * P_IT

print("=" * 78)
print("F. DRY-COOLING PUE PENALTY  (Karimi2022: air-cooled DC1 PUE ~13% HIGHER than")
print("   water-cooled+evaporative DC2, while DC2 WUE far higher) -> PUE(dry)>PUE(wet)")
print("=" * 78)
C, LF = 100.0, 0.8
configs = [
    ("A 湿式为主  f_wet=1.00 PUE=1.25", 1.25, 1.00),
    ("B 干湿混合  f_wet=0.50 PUE=1.33", 1.33, 0.50),
    ("C 干式为主  f_wet=0.25 PUE=1.41", 1.41, 0.25),
    ("D 全干式    f_wet=0.00 PUE=1.45", 1.45, 0.00),
]
for tag, pue, fw in configs:
    M, WUE, P_IT, P_fac = water(C, LF, pue, fw)
    print(f"  {tag:<34} 补水={M:8.0f} m3/d  WUE={WUE:5.2f} L/kWh  设施电功率={P_fac:6.1f} MW")

print()
print("=" * 78)
print("G. ANNUAL-AVERAGE vs PEAK-DAY  (dry-first hybrid: water concentrated on hot days)")
print("=" * 78)
# dry-first: most of year f_wet small; hot days f_wet rises with wet-bulb
# Model: annual mean f_wet = 0.25 ; hottest-day f_wet = 0.85 (evaporative assist)
M_ann, WUE_ann, P_IT, P_ann = water(C, LF, 1.41, 0.25)
M_hot, WUE_hot, _, P_hot = water(C, LF, 1.41, 0.85)   # hot day, evaporative assist on
M_wet_ann, _, _, P_wet = water(C, LF, 1.25, 1.00)
M_wet_hot, _, _, _ = water(C, LF, 1.25, 1.00)          # wet: heat load ~IT load, weak T effect

pf_hybrid = M_hot / M_ann
pf_wet = M_wet_hot / M_wet_ann
print(f"  湿式为主:  年均 {M_wet_ann:7.0f} m3/d ; 热日 {M_wet_hot:7.0f} m3/d -> 峰值系数 ~{pf_wet:.2f}x")
print(f"  干式优先:  年均 {M_ann:7.0f} m3/d ; 热日 {M_hot:7.0f} m3/d -> 峰值系数 ~{pf_hybrid:.2f}x")
print()
print("  对标 Ren2026: 纯蒸发冷却塔 ~2.2x ; 干式+蒸发辅助 6.5-10x")
print(f"  -> 湿式算例 {pf_wet:.2f}x 落在纯湿区间(需>1,约1-2.5x) ; 干式优先 {pf_hybrid:.2f}x 应落入 6.5-10x 区间")
print(f"  => 若模型算出的干式优先峰值系数 < 6.5x，说明 f_wet 随湿球温度的切换函数过弱，需重标定(设计中的 V5 判据)")

print()
print("=" * 78)
print("H. WATER->POWER BURDEN SHIFT (the mechanism to design an experiment for)")
print("=" * 78)
print(f"  湿式为主: 设施电功率 {P_wet:6.1f} MW ; 补水 {M_wet_ann:7.0f} m3/d")
print(f"  干式优先: 设施电功率 {P_ann:6.1f} MW ; 补水 {M_ann:7.0f} m3/d")
dP = P_ann - P_wet
dM = M_wet_ann - M_ann
print(f"  -> 节水 {dM:7.0f} m3/d ({dM/M_wet_ann*100:.0f}%)，代价是增功率 {dP:5.1f} MW ({dP/P_wet*100:.0f}%)")
print(f"  -> 每节省 1 m3/d 水，需增加 {dP*1000/dM:.2f} kW 电功率  <-- 可直接作为'负担转移'指标")
print(f"  -> 热日进一步恶化: 干式优先热日功率 {P_hot:6.1f} MW (逼近度随湿球升高而恶化)")
