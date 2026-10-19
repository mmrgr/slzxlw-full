# -*- coding: utf-8 -*-
"""核验干预两两交互结果，并确认它不是自证循环。

【关键发现（2026-10-19）】
HA 端 36 对干预中，35 对**完全可加**（交互 = 0），唯一非可加对是
`leakage_minus_30pct + combined_upgrade`，交互 −250 MW（纯物理）/ −150 MW（联合）。

这是**预期的**，不是缺陷：`combined_upgrade` 的干预集合本来就包含
`leakage_minus_30pct`（见 specs/interventions_ha.json），两者同时施加等于
把降漏损计了两次，故必然出现完全冗余（次可加且交互恰等于降漏损单项增益）。

因此本核验要断言的是：
  1. 除该对以外，所有对都可加（说明干预互不干扰）；
  2. 该对交互恰等于 −gain(leakage)，即完全冗余；
  3. 单干预联合口径增益与论文 §5.4 表一致（HA +150 / CO +100）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
R2 = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
SUM = R2 / "interaction_pairs_50mw_summary.json"
SPEC_HA = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "examples" / "cawcc_r2" / "specs" / "interventions_ha.json"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not SUM.exists():
        print("缺少 interaction_pairs_50mw_summary.json")
        return
    d = json.loads(SUM.read_text(encoding="utf-8"))
    ck("含两基底", set(d["bases"]) == {"ha", "co"}, str(sorted(d["bases"])))

    ha, co = d["bases"]["ha"], d["bases"]["co"]

    # ---- 1. 单干预增益与论文 §5.4 一致（联合口径）----
    ck("HA 基线（联合）= 1150", ha["baseline_joint_mw"] == 1150.0,
       str(ha["baseline_joint_mw"]))
    ck("CO 基线（联合）= 1450", co["baseline_joint_mw"] == 1450.0,
       str(co["baseline_joint_mw"]))
    ck("HA leakage 联合增益 = +150（与论文 §5.4 一致）",
       ha["single_gains_joint"]["leakage_minus_30pct"] == 150.0,
       str(ha["single_gains_joint"]["leakage_minus_30pct"]))
    ck("CO grid 联合增益 = +100（与论文 §5.4 一致）",
       co["single_gains_joint"]["grid_plus_50pct"] == 100.0,
       str(co["single_gains_joint"]["grid_plus_50pct"]))
    ck("HA leakage 纯物理增益 = +250",
       ha["single_gains_physical"]["leakage_minus_30pct"] == 250.0,
       str(ha["single_gains_physical"]["leakage_minus_30pct"]))

    # ---- 2. 除冗余对外全部可加 ----
    for tag, base in (("HA", ha), ("CO", co)):
        for cal in ("joint", "physical"):
            sub = [p for p in base["pairs"] if p["caliber"] == cal]
            ck(f"{tag} [{cal}] 有 36 对", len(sub) == 36, str(len(sub)))
            n_add = sum(1 for p in sub if p["kind"] == "additive")
            n_non = len(sub) - n_add
            if tag == "CO":
                ck(f"{tag} [{cal}] 全部可加", n_non == 0, f"{n_non} 对非可加")
            else:
                ck(f"{tag} [{cal}] 仅 1 对非可加", n_non == 1, f"{n_non} 对非可加")

    # ---- 3. 那 1 对必须是 leakage + combined_upgrade，且完全冗余 ----
    for cal in ("joint", "physical"):
        non = [p for p in ha["pairs"] if p["caliber"] == cal and p["kind"] != "additive"]
        ck(f"HA [{cal}] 非可加对确为 leakage+combined_upgrade",
           len(non) == 1 and set([non[0]["a"], non[0]["b"]]) ==
           {"leakage_minus_30pct", "combined_upgrade"},
           str([(n["a"], n["b"]) for n in non]))
        if len(non) == 1:
            p = non[0]
            gain_leak = ha[f"single_gains_{cal}"]["leakage_minus_30pct"]
            ck(f"HA [{cal}] 交互恰等于 −gain(leakage)（完全冗余）",
               abs(p["interaction_mw"] + gain_leak) < 1e-6,
               f"交互 {p['interaction_mw']}, −gain(leak) {-gain_leak}")

    # ---- 4. 规格层面确认 combined_upgrade 确实包含 leakage ----
    spec = json.loads(SPEC_HA.read_text(encoding="utf-8"))
    items = {it["name"]: it["set"] for it in spec["interventions"]}
    leak_paths = {e["path"] for e in items.get("leakage_minus_30pct", [])}
    comb_paths = {e["path"] for e in items.get("combined_upgrade", [])}
    ck("规格层面：combined_upgrade 包含 leakage 的全部路径",
       leak_paths and leak_paths.issubset(comb_paths),
       f"leak {len(leak_paths)} 条，comb {len(comb_paths)} 条，"
       f"交集 {len(leak_paths & comb_paths)}")

    # ---- 5. 无非零但未解释的交互 ----
    unexplained = [p for p in ha["pairs"] + co["pairs"]
                   if p["kind"] != "additive"
                   and not (set([p["a"], p["b"]]) ==
                            {"leakage_minus_30pct", "combined_upgrade"})]
    ck("无其他未解释的非可加对", len(unexplained) == 0,
       f"{len(unexplained)} 对")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n干预交互核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
