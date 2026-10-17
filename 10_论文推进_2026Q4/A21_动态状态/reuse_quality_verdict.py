"""A21c: 决定性检验 —— R10a 的 CoC 7.98 是否为"缺失质量输入"的产物？

【假设（A21b 提出）】
R10a 的 CoC≈7.98 不是更真实的物理，而是因为 `CENTRAL_REUSE` 组件**未配置质量**，
其溶质账本为空 ⇒ 再生水浓度被当作 0 ⇒ 混合浓度降至 0.4×200=80 mg/L
⇒ CoC_lim = 1100/80 = 13.75 > 设计 8.0 ⇒ 取设计值 8.0。

【本脚本的判决性实验】
在 **R10a 路径**下，把 `CENTRAL_REUSE.quality_mg_l.TDS` 显式设为 900（与 volume-only 一致），
并补齐 `pollutant_removal_fraction`，看 CoC 是否回落到 volume-only 的 ~1.77。

  · 若回落到 ~1.77  ⇒ 假设成立；两条路径**本应一致**，
                     差异纯由"组件未配质量"造成 ⇒ 既有 volume-only 结论可用，
                     但须声明"再生水质量必须显式配置"。
  · 若仍 ≈8.0      ⇒ 假设被否证；两条路径确有结构性物理差异。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
if str(ENGINE / "src") not in sys.path:
    sys.path.insert(0, str(ENGINE / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
TDS_LIMIT = 1100.0
C_REC = 900.0
C_POT = 200.0


def run(dom: str, *, quality_state: bool, set_reuse_quality: bool,
        removal: bool = True) -> dict:
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 8.0
    dc["cooling"]["water_quality_limits"] = {"TDS": TDS_LIMIT}
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.6
    dc["water_sources"]["potable"]["target_fraction"] = 0.4
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": C_REC}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": C_POT}

    ru = proj["components"].get("CENTRAL_REUSE")
    if ru is not None:
        ru["treatment_capacity_ml_day"] = 200.0
        ru["initial_ml"] = 100.0
        if set_reuse_quality:
            ru["quality_mg_l"] = {"TDS": C_REC}
            ru["treated_quality_mg_l"] = {"TDS": C_REC}
            ru["quality_provenance"] = "treated_output"
        if removal:
            ru["pollutant_removal_fraction"] = {"TDS": 0.0}   # 不额外去除, 保持 900
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())

    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily
    return {
        "domain": dom, "quality_state": quality_state,
        "set_reuse_quality": set_reuse_quality,
        "makeup_ml": float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum()),
        "blowdown_ml": float(pd.to_numeric(d["blowdown_ml"], errors="coerce").sum())
        if "blowdown_ml" in d.columns else float("nan"),
        "coc_mean": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").mean()),
        "coc_min": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").min()),
    }


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("A21c  判决性检验: R10a 的 CoC 是否由缺失质量输入造成")
    rec("=" * 78)

    c_mix = 0.6 * C_REC + 0.4 * C_POT
    rec(f"\n预期（若两路径物理一致）: CoC = {TDS_LIMIT}/{c_mix:.0f} = {TDS_LIMIT/c_mix:.3f}")

    rows = []
    for dom in ("ha", "co"):
        for qs in (False, True):
            for srq in (False, True):
                try:
                    r = run(dom, quality_state=qs, set_reuse_quality=srq)
                    rows.append(r)
                    rec(f"  {dom} qs={str(qs):5} set_reuse_quality={str(srq):5} "
                        f"| makeup={r['makeup_ml']:10.0f} coc_mean={r['coc_mean']:6.3f} "
                        f"coc_min={r['coc_min']:.3f}")
                except Exception as e:  # noqa: BLE001
                    rec(f"  ERROR {dom} qs={qs} srq={srq}: {type(e).__name__}: {e}")

    d = pd.DataFrame(rows)
    d.to_csv(HERE / "reuse_quality_verdict.csv", index=False, encoding="utf-8-sig")

    rec("\n[判定]")
    for dom in ("ha", "co"):
        s = d[d.domain == dom]
        off = s[(~s.quality_state)]
        on_noq = s[(s.quality_state) & (~s.set_reuse_quality)]
        on_q = s[(s.quality_state) & (s.set_reuse_quality)]
        if len(off) and len(on_q):
            rec(f"  {dom}: volume-only coc={off['coc_mean'].iloc[0]:.3f} | "
                f"R10a(无质量)={on_noq['coc_mean'].iloc[0] if len(on_noq) else float('nan'):.3f} | "
                f"R10a(配质量)={on_q['coc_mean'].iloc[0]:.3f}")

    hypothesis_ok = None
    if len(d):
        on_q = d[(d.quality_state) & (d.set_reuse_quality)]
        if len(on_q):
            hypothesis_ok = bool((on_q["coc_mean"] - TDS_LIMIT / c_mix).abs().max() < 0.3)
    rec(f"\n  假设（配质量后 R10a 回落到解析值 {TDS_LIMIT/c_mix:.3f}）= {hypothesis_ok}")

    summary = {
        "expected_coc_if_consistent": float(TDS_LIMIT / c_mix),
        "hypothesis_confirmed": hypothesis_ok,
        "table": d.to_dict(orient="records"),
        "reading": (
            "若 hypothesis_confirmed=True，则 R10a 的 CoC≈8 是 **CENTRAL_REUSE 未配置质量**"
            "造成的（溶质账本为空 → 浓度按 0 计），而非更真实的物理；"
            "两条路径在补齐质量输入后应一致，既有 volume-only 结论可用，"
            "但论文须声明'再生水质量必须显式配置'。"),
        "discipline_note": "不改引擎；只改输入配置，配对比较。",
    }
    (HERE / "reuse_quality_verdict_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec("\n[write] reuse_quality_verdict.csv / .json")
    (HERE / "a21c_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
