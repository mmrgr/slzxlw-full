"""A22: 三量判据的结构分解 —— 把"恒等式"升级为"可判定的决策条件".

【为什么要重做】
A17 报告的"三量判据"（dS<0 ⟺ x_AI+(M0-M1) > 位移）经自查发现是
**代数恒等式的重排**（残差 1.3e-15），因此不构成"发现"。

真正有科学内容的是它**背后的符号结构**。本脚本把它分解为三个无量纲量，
并给出每个量由什么**外部可测条件**决定。

【分解（除以 M1，无量纲）】
    dS_pot / M1 = ρ·(κ - 1) - q
      ρ = x_AI / M1          再利用率（AI 取用的再生水占其补水的份额）
      κ = 位移 / x_AI        竞争比（AI 取的再生水里有多少是从既有用户夺来的）
      q = (M0 - M1) / M1     质量效应（>0 表示回用使补水【下降】）

  符号：dS < 0  ⟺  ρ(κ-1) < q
  即     【回用带来的净释放】超过【质量惩罚】时，城市取水才下降。

【关键：q 的符号由什么决定（外部可测）】
  在 volume-only 口径下 CoC_lim = L / c_mix,  c_mix = φ·c_rec + (1-φ)·c_pot
  ⇒ 回用使 c_mix 下降（⇒CoC 上升⇒补水下降，q>0） 当且仅当  c_rec < c_pot
  外部可测条件：**再生水比自来水更"干净"（按限值相关指标）**
  这是可以在现实中查证的（查两家水质报告即可），不是模型内部量。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# 引擎 project.json 中 potable 源的水质（未被水样覆盖，固定）
POTABLE_TDS = 180.0
POTABLE_CL = 35.0
# T6 水样的再生水水质
RECLAIMED = {
    "IEUA RP-1 (2025, tertiary)": {"TDS": 443.0, "chloride": 100.0},
    "LADWP AWPF (2012, RO product)": {"TDS": 22.0, "chloride": 3.6},
    "Figshare RW (2025, paired study)": {"TDS": 1378.0, "chloride": 313.7},
    "AI-UWM model assumption": {"TDS": 650.0, "chloride": 130.0},
}


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A22  三量判据的结构分解：从恒等式到可判定条件")
    rec("=" * 80)

    ss = pd.read_csv(HERE.parent / "A13_可靠性机制" / "supply_state_regimes.csv",
                     encoding="utf-8-sig")
    for c in ("x_ai_B1_ml", "M0_ml", "M1_ml", "displaced_ml", "dS_pot_ml"):
        ss[c] = pd.to_numeric(ss[c], errors="coerce")

    # ---------- 1. 无量纲分解 ----------
    ss["rho"] = ss["x_ai_B1_ml"] / ss["M1_ml"]
    ss["kappa"] = ss["displaced_ml"] / ss["x_ai_B1_ml"].replace(0, np.nan)
    ss["q"] = (ss["M0_ml"] - ss["M1_ml"]) / ss["M1_ml"]
    lhs = ss["dS_pot_ml"] / ss["M1_ml"]
    rhs = ss["rho"] * (ss["kappa"] - 1.0) - ss["q"]
    res = (lhs - rhs).abs().max()

    rec("\n[1] 无量纲分解（自查：这是恒等式重排，不是发现）")
    rec("    dS_pot/M1 = ρ·(κ-1) - q")
    rec(f"    最大残差 = {res:.3e}  → 确认是代数恒等式")

    # ---------- 2. q 的符号结构（真正的科学内容） ----------
    rec("\n[2] ★ q 的符号分布（这是有科学内容的）")
    rec(f"    q > 0（回用使补水下降）: {int((ss['q'] > 1e-9).sum()):4d}")
    rec(f"    q ≈ 0                  : {int((ss['q'].abs() <= 1e-9).sum()):4d}")
    rec(f"    q < 0（回用使补水上升）: {int((ss['q'] < -1e-9).sum()):4d}")

    rec("\n[3] ★ 按 q 的符号分组的 dS_pot（决定性结构）")
    groups = [("q>0  回用降低补水", ss["q"] > 1e-9),
              ("q≈0", ss["q"].abs() <= 1e-9),
              ("q<0  回用升高补水", ss["q"] < -1e-9)]
    tbl = []
    for lab, m in groups:
        g = ss[m]
        row = {"group": lab, "n": int(len(g)),
               "n_beneficial": int((g["dS_pot_ml"] < -1e-6).sum()),
               "n_harmful": int((g["dS_pot_ml"] > 1e-6).sum()),
               "dS_median": float(g["dS_pot_ml"].median())}
        tbl.append(row)
        rec(f"    {lab:20} n={row['n']:4d}  有益={row['n_beneficial']:4d}  "
            f"有害={row['n_harmful']:4d}  中位 dS={row['dS_median']:9.0f}")

    # ---------- 4. q 的外部可测判据 ----------
    rec("\n[4] ★ q 符号的外部可测判据")
    rec("    volume-only: CoC_lim = L / c_mix,  c_mix = φ·c_rec + (1-φ)·c_pot")
    rec("    ⇒ q > 0  ⟺  c_rec < c_pot  ⟺  【再生水比自来水更干净】")
    rec(f"    引擎固定自来水: TDS={POTABLE_TDS}, Cl={POTABLE_CL}")
    ext = []
    for name, q in RECLAIMED.items():
        pred_clean = q["TDS"] < POTABLE_TDS
        g = ss[ss["sample"] == name]
        share_pos = float((g["q"] > 1e-9).mean()) if len(g) else float("nan")
        ext.append({"sample": name, "TDS": q["TDS"], "chloride": q["chloride"],
                    "predicted_cleaner_than_potable": bool(pred_clean),
                    "observed_share_q_pos": share_pos, "n": int(len(g))})
        rec(f"    {name[:34]:34} TDS={q['TDS']:7.1f}  预测更干净={str(pred_clean):5}  "
            f"实测 q>0 占比={share_pos:.3f}")

    # 判据的定量吻合（按"干净"预测的样本级一致性）
    rec("\n[5] 外部判据的样本级一致性")
    ok = 0
    tot = 0
    for e in ext:
        if e["predicted_cleaner_than_potable"]:
            ok += int(e["observed_share_q_pos"] > 0.5)
        else:
            ok += int(e["observed_share_q_pos"] < 0.5)
        tot += 1
    rec(f"    按'TDS < 自来水 TDS'预测 q 的多数符号: {ok}/{tot} 一致")

    # ---------- 6. 决策条件（论文可用形式） ----------
    rec("\n[6] ★ 可写入论文的可判定条件")
    rec("    城市取水下降（再生水冷却有利）当且仅当")
    rec("        ρ·(κ-1) < q")
    rec("    其中 q>0 的可测前提是【再生水的限值相关浓度低于自来水】；")
    rec("    若再生水更脏（q<0），则必须靠【不挤占任何既有用户】(κ→0) 来抵消：")
    rec("        条件退化为  -ρ < q  ... 当 κ=0 时 dS = -ρ·M1 - q·M1")
    kappa0 = ss[ss["displaced_ml"].abs() < 1e-6]
    rec(f"    实测 κ=0 子集: n={len(kappa0)}  "
        f"有利={int((kappa0['dS_pot_ml'] < -1e-6).sum())}  "
        f"有害={int((kappa0['dS_pot_ml'] > 1e-6).sum())}")

    summary = {
        "identity_residual": float(res),
        "identity_note": "dS/M1 = ρ(κ-1) - q 是恒等式重排（残差 ~1e-15），不构成发现",
        "q_sign_groups": tbl,
        "q_external_criterion": {
            "statement": "q > 0 ⟺ c_reclaimed < c_potable（按限值相关指标）",
            "potable_tds_mg_l": POTABLE_TDS,
            "potable_chloride_mg_l": POTABLE_CL,
            "samples": ext,
            "agreement": f"{ok}/{tot}",
        },
        "decision_condition": "ρ(κ-1) < q；κ=0 时退化为 -ρ < q",
        "kappa_zero_subset": {
            "n": int(len(kappa0)),
            "beneficial": int((kappa0["dS_pot_ml"] < -1e-6).sum()),
            "harmful": int((kappa0["dS_pot_ml"] > 1e-6).sum()),
        },
        "discipline_note": (
            "全部量由现行 supply_state_regimes.csv 重算；外部判据只用公开水质浓度，"
            "不含任何模型内部量。"),
    }
    (HERE / "derived_criterion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ss.to_csv(HERE / "derived_criterion_grid.csv", index=False, encoding="utf-8-sig")
    rec("\n[write] derived_criterion_summary.json / derived_criterion_grid.csv")
    (HERE / "a22_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
