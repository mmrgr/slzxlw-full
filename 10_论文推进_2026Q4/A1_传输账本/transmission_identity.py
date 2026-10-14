"""A1 传输账本: 验证 AI-UWM 的"设施节水 -> 城市节水"传递恒等式.

输入(冻结产物, 只读):
    validation_artifacts/r2/reclaimed_compatibility_R9.csv

输出:
    transmission_ledger.csv   复算的传递账本
    fig1_transmission_identity.png

恒等式(共享情景 Ls, 再生水取自既有用户存量):
    M(CoC) = E * CoC / (CoC - 1)                总补水仅由 CoC 决定
    S_AI   = M(0) - M_AI_potable(f)
    S_city = W_source(0) - W_source(f)
    预测   S_city ~= M(0) - M(f)                即"总补水变化", 与水源构成无关
    eta_transfer = S_city / S_AI

注: 本脚本只做只读复算, 不运行主模型, 不改变任何门禁.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
SRC = REPO / "validation_artifacts" / "r2" / "reclaimed_compatibility_R9.csv"
OUT = Path(__file__).resolve().parent


def build_ledger(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for domain, d in df.groupby("domain", sort=True):
        d = d.sort_values("target_reclaimed_fraction")
        base = d.iloc[0]
        m0 = float(base["ai_withdrawal_ml"])          # B2 基线: 设计 CoC 下的总补水
        src0 = float(base["city_potable_abstraction_ml"])
        inc0 = float(base["other_users_potable_delivered_ml"])
        ww0 = float(base["wwtw_treated_ml"])
        for _, r in d.iterrows():
            f = float(r["target_reclaimed_fraction"])
            m = float(r["ai_withdrawal_ml"])
            s_ai = m0 - float(r["ai_potable_ml"])
            s_city = src0 - float(r["city_potable_abstraction_ml"])
            pred = m0 - m
            d_inc = float(r["other_users_potable_delivered_ml"]) - inc0
            d_ww = float(r["wwtw_treated_ml"]) - ww0
            rows.append(
                {
                    "domain": domain,
                    "f_reclaimed": f,
                    "M_total_makeup_ml": m,
                    "CoC_mean": float(r["ai_mean_coc"]),
                    "S_AI_ml": s_ai,
                    "S_city_ml": s_city,
                    "S_city_predicted_M0_minus_M_ml": pred,
                    "identity_residual_ml": s_city - pred,
                    "identity_residual_pct_of_S_AI": (
                        100.0 * (s_city - pred) / s_ai if s_ai > 1e-9 else 0.0
                    ),
                    "eta_transfer": (s_city / s_ai if s_ai > 1e-9 else np.nan),
                    "delta_incumbent_potable_ml": d_inc,
                    "delta_wwtw_treated_ml": d_ww,
                    "redistribution_check_ML_gap": d_inc - (m0 - m),
                }
            )
    return pd.DataFrame(rows)


def find_f_star(led: pd.DataFrame) -> dict:
    """f* = 城市取水由"不增"转为"增加"的临界掺混比.

    在给定网格上给出区间 [f_last_zero, f_first_negative] 及其中点;
    f* 的精确值由 CoC_lim(f) = CoC_design 解析确定, 需加密网格后求解.
    """
    out = {}
    for domain, d in led.groupby("domain"):
        d = d.sort_values("f_reclaimed").reset_index(drop=True)
        neg = d.index[d["S_city_ml"] < -1e-9]
        if len(neg) == 0:
            out[domain] = {"bracket": [float(d["f_reclaimed"].iloc[-1]), None], "midpoint": None}
            continue
        i = int(neg[0])
        f_lo = float(d["f_reclaimed"].iloc[i - 1]) if i > 0 else 0.0
        f_hi = float(d["f_reclaimed"].iloc[i])
        out[domain] = {"bracket": [f_lo, f_hi], "midpoint": 0.5 * (f_lo + f_hi)}
    return out


def make_figure(led: pd.DataFrame, f_star: dict) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    for domain, d in led.groupby("domain"):
        d = d.sort_values("f_reclaimed")
        c = "#c0392b" if domain == "D-HA" else "#2471a3"
        axes[0].plot(d["f_reclaimed"], d["S_AI_ml"] / 1e3, "o-", color=c, label=f"{domain} $S_{{AI}}$")
        axes[0].plot(d["f_reclaimed"], d["S_city_ml"] / 1e3, "s--", color=c, alpha=0.55, label=f"{domain} $S_{{city}}$")
        axes[0].plot(d["f_reclaimed"], d["CoC_mean"], "^-", color=c, alpha=0.9)
    axes[0].axhline(0, color="k", lw=1)
    axes[0].set_xlabel("Reclaimed fraction of makeup $f$")
    axes[0].set_ylabel("$S_{AI}$ / $S_{city}$ (10$^3$ ML)")
    axes[0].set_title("Facility saving vs city saving", fontsize=11)
    axes[0].legend(fontsize=7, loc="upper left")

    for domain, d in led.groupby("domain"):
        d = d.sort_values("f_reclaimed")
        c = "#c0392b" if domain == "D-HA" else "#2471a3"
        axes[1].plot(d["f_reclaimed"], d["S_city_ml"] / 1e3, "o-", color=c, label=f"{domain} actual $S_{{city}}$")
        axes[1].plot(d["f_reclaimed"], d["S_city_predicted_M0_minus_M_ml"] / 1e3, "x--", color="k", alpha=0.6, ms=4)
    axes[1].axhline(0, color="k", lw=1)
    axes[1].set_xlabel("Reclaimed fraction of makeup $f$")
    axes[1].set_ylabel("$S_{city}$ (10$^3$ ML)")
    axes[1].set_title("Identity test: $S_{city}=M(0)-M(f)$  (x = prediction)", fontsize=11)
    axes[1].legend(fontsize=7)

    for domain, d in led.groupby("domain"):
        d = d.sort_values("f_reclaimed")
        c = "#c0392b" if domain == "D-HA" else "#2471a3"
        axes[2].plot(d["f_reclaimed"], d["eta_transfer"], "o-", color=c, label=domain)
        fs = f_star.get(domain, {}).get("midpoint")
        if fs is not None:
            lo, hi = f_star[domain]["bracket"]
            axes[2].axvspan(lo, hi, color=c, alpha=0.12)
            axes[2].annotate(f"$f^*\\in[{lo:.1f},{hi:.1f}]$", (fs, -0.055), color=c, fontsize=8, ha="center")
    axes[2].axhline(0, color="k", lw=1)
    axes[2].set_xlabel("Reclaimed fraction of makeup $f$")
    axes[2].set_ylabel(r"$\eta_{transfer}=S_{city}/S_{AI}$")
    axes[2].set_title("Transmission efficiency", fontsize=11)
    axes[2].legend(fontsize=8)

    for ax in axes:
        ax.grid(alpha=0.25, lw=0.6)
        ax.set_facecolor("#fbfbfb")
    fig.suptitle(
        "AI-UWM: reclaimed-water cooling transmits no city-scale saving, and reverses beyond a quality-determined threshold",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    fig.savefig(OUT / "fig1_transmission_identity.png", dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(SRC)
    led = build_ledger(df)
    led.to_csv(OUT / "transmission_ledger.csv", index=False, encoding="utf-8-sig")
    f_star = find_f_star(led)
    make_figure(led, f_star)

    summary = {
        "source": str(SRC.relative_to(REPO)),
        "rows": int(len(led)),
        "f_star": f_star,
        "max_abs_identity_residual_pct_of_S_AI": float(
            led["identity_residual_pct_of_S_AI"].abs().max()
        ),
        "zero_transfer_region": {
            k: float(v)
            for k, v in led[led["S_city_ml"].abs() < 1e-6]
            .groupby("domain")["f_reclaimed"]
            .max()
            .items()
        },
        "eta_transfer_at_max_f": {
            k: float(v) for k, v in led.sort_values("f_reclaimed").groupby("domain")["eta_transfer"].last().items()
        },
        "scope": "model diagnostic over frozen R9 artifact; 1000 MW, fixed point TDS/chloride; NOT a field-validated result",
    }
    (OUT / "transmission_identity_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
