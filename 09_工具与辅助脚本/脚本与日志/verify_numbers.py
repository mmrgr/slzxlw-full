"""Sanity / self-check computations for the scenario design.

Sources of inputs are commented. All derived numbers are printed so they can be
cross-checked against literature before being written into the design.
"""

def wm3d(annual_yi_m3):
    """亿 m3/yr -> 万 m3/day"""
    return annual_yi_m3 * 1e8 / 365 / 1e4

print("=" * 70)
print("A. BASE CITY (Beijing-type) daily rates from 北京市水资源公报 2024")
print("=" * 70)
items = [
    ("供水设施总供水量", 19.80),
    ("城镇公共供水厂供水", 15.09),
    ("污水排放总量", 23.58),
    ("污水处理量", 23.00),
    ("再生水利用量(总)", 13.23),
    ("再生水-河湖补水", 11.82),
    ("再生水-生产生活", 1.41),
    ("工业用水", 2.85),
    ("工业用水中再生水", 0.93),
    ("生活用水(配置口径)", 19.32),
    ("生产生活总用水(不含损失)", 22.62),
]
base = {}
for name, v in items:
    d = wm3d(v)
    base[name] = d
    print(f"  {name:<28} {v:>6.2f} 亿m3/yr -> {d:8.2f} 万m3/d")

# consistency checks
supply = base["供水设施总供水量"]
treated = base["污水处理量"]
reclaim = base["再生水利用量(总)"]
print(f"\n  再生水利用 / 处理量          = {reclaim/treated*100:.1f}%")
print(f"  再生水利用 / 再生水生产能力728.9 = {reclaim/728.9*100:.1f}%  (公报载生产能力 728.9 万m3/d)")
print(f"  工业再生水占工业用水          = {base['工业用水中再生水']/base['工业用水']*100:.1f}%  (公报称>30% -> 一致)")

print()
print("=" * 70)
print("B. AI CAMPUS COOLING WATER (physics check vs literature)")
print("=" * 70)
# Physics constants (report eq 5-15..5-19)
rho, cp, Lv = 1.0e3, 4.186e3, 2.45e6

def campus(C_IT_MW, LF, PUE, xi_h, f_wet, eta_evap, CoC, drift_pct, dT):
    P_IT = C_IT_MW * LF                 # MW
    P_fac = PUE * P_IT                  # MW
    Q = xi_h * P_fac                    # MW total heat to reject
    Q_wet = f_wet * Q                   # MW to wet side
    # evaporation
    E_kgs = eta_evap * Q_wet * 1e6 / Lv           # kg/s
    E = E_kgs * 86400 / 1000                       # m3/day
    # circulation
    V = Q_wet * 1e6 / (rho * cp * dT)              # m3/s
    D = drift_pct / 100.0 * V * 86400              # m3/day
    # blowdown from salt balance at CoC
    B = E / (CoC - 1.0)
    M = E + B + D
    # closure check: M == E*CoC/(CoC-1) + D
    M2 = E * CoC / (CoC - 1.0) + D
    IT_kwh = P_IT * 1e3 * 24                       # kWh/day
    WUE = M * 1000 / IT_kwh                        # L/kWh
    return dict(P_IT=P_IT, P_fac=P_fac, Q=Q, Q_wet=Q_wet, E=E, B=B, D=D, M=M,
                M2=M2, WUE=WUE, V=V)

cases = [
    ("基准 全湿 CoC=5", dict(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=5,  drift_pct=0.05, dT=5)),
    ("CoC=3  (poor)",   dict(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=3,  drift_pct=0.05, dT=5)),
    ("CoC=10 (good)",   dict(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=10, drift_pct=0.05, dT=5)),
    ("CoC=15 (best)",   dict(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=15, drift_pct=0.05, dT=5)),
    ("干湿混合 f_wet=0.3", dict(C_IT_MW=100, LF=0.8, PUE=1.25, xi_h=1.0, f_wet=0.3, eta_evap=0.85, CoC=5, drift_pct=0.05, dT=5)),
    ("液冷 PUE=1.10",   dict(C_IT_MW=100, LF=0.8, PUE=1.10, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=5,  drift_pct=0.05, dT=8)),
]
for name, kw in cases:
    r = campus(**kw)
    print(f"\n  --- {name} ---")
    print(f"   P_IT={r['P_IT']:.1f} MW  P_fac={r['P_fac']:.1f} MW  Q={r['Q']:.1f} MW  Q_wet={r['Q_wet']:.1f} MW")
    print(f"   循环量 V={r['V']:.2f} m3/s")
    print(f"   蒸发 E={r['E']:.0f}  排污 B={r['B']:.0f}  飘散 D={r['D']:.0f}  补水 M={r['M']:.0f} m3/d")
    print(f"   闭合校验 M2={r['M2']:.0f} (应等于 M)  残差={abs(r['M']-r['M2']):.3e}")
    print(f"   WUE_onsite = {r['WUE']:.2f} L/kWh   排污占补水 {r['B']/r['M']*100:.1f}%   蒸发占补水 {r['E']/r['M']*100:.1f}%")

print()
print("=" * 70)
print("C. SCALE vs CITY SUPPLY + PEAKING (Ren et al. 2026 benchmark)")
print("=" * 70)
r = campus(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=5, drift_pct=0.05, dT=5)
m100 = r["M"]
for C in [100, 250, 500, 1000, 2000]:
    m = m100 * C / 100.0
    print(f"  C_IT={C:>5} MW: 日均补水 {m:9.0f} m3/d ({m/1e4:6.2f} 万m3/d) "
          f"= 全市供水({supply:.1f}万m3/d)的 {m/1e4/supply*100:5.2f}%")
print("\n  峰值倍数对标 (Han/Li/Wierman/Ren 2026, arXiv:2603.02705):")
print("    居民/商业 1.5-2.5x ; 纯蒸发冷却塔 ~2.2x ; 干式+蒸发辅助(混合) 6.5-10x ; 极端单体可达 ~30x")
for C in [500, 1000]:
    m = m100 * C / 100.0
    for pf, tag in [(2.2, "纯湿"), (6.5, "混合低"), (10.0, "混合高")]:
        p = m * pf
        print(f"    C_IT={C} MW {tag:<5} 峰值={p/1e4:6.2f} 万m3/d = 全市供水的 {p/1e4/supply*100:5.2f}%")

print()
print("=" * 70)
print("D. INDIRECT (power) water vs onsite  -- order-of-magnitude")
print("=" * 70)
r = campus(C_IT_MW=100, LF=0.8, PUE=1.30, xi_h=1.0, f_wet=1.0, eta_evap=0.85, CoC=5, drift_pct=0.05, dT=5)
kwh_day = r["P_fac"] * 1e3 * 24
for wif, tag in [(1.0, "低(高效/干冷机组)"), (2.18, "US均值2015 Mytton"), (5.1, "US均值 Karimi")]:
    ind = kwh_day * wif / 1000.0
    print(f"  电网水因子 {wif:>5.2f} L/kWh ({tag}): 间接水 {ind:8.0f} m3/d ; "
          f"间接/直接 = {ind/r['M']:.2f}")
print(f"  直接(现场) = {r['M']:.0f} m3/d")

print()
print("=" * 70)
print("E. LOCAL ACCESS CONSTRAINT (why 局部接入 matters)")
print("=" * 70)
# a district WTP serving a fraction of the city
for frac, tag in [(0.10, "片区水厂(占全市10%)"), (0.05, "片区水厂(占全市5%)")]:
    cap = supply * frac
    for C in [250, 500, 1000]:
        m = m100 * C / 100.0
        print(f"  {tag} 能力 {cap*1e4:8.0f} m3/d ; C_IT={C} MW 日需 {m:7.0f} -> 占比 {m/(cap*1e4)*100:5.2f}% ; "
              f"峰值(2.2x) {m*2.2/(cap*1e4)*100:5.2f}%")
