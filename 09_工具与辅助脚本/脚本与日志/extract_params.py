import re, os
from pypdf import PdfReader

BASE = r"C:\Users\mmrgr\Desktop\论文9.15"
TARGETS = {
    "B1_04_Lei2022_PUE_WUE_estimations_data_centers.pdf": ["PUE", "WUE", "L/kWh", "archetype", "climate zone", "IT equipment"],
    "B1_07_Karimi2022_Data_center_water_energy_hot_arid.pdf": ["PUE", "WUE", "cycles", "makeup", "blowdown", "evaporat"],
    "B1_02_Lei2025_Water_use_data_center_workloads.pdf": ["WUE", "PUE", "determinant", "utilization", "cool"],
    "B1_15_Mytton2021_Data_centre_water_consumption.pdf": ["WUE", "L/kWh", "liter", "cool", "evaporat"],
    "B2_06_Chen2022_Liquid_cooled_data_centers.pdf": ["liquid", "cold plate", "immersion", "flow", "temperature"],
}

KW = ["WUE", "PUE", "L/kWh", "cycles of concentration", "cycle of concentration", "CoC",
      "drift", "blowdown", "makeup water", "wet-bulb", "wet bulb", "approach",
      "evaporation", "evaporative", "cold plate", "immersion", "evaporation rate"]

out = r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\param_evidence.txt"
lines = []

for fn in TARGETS:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        lines.append(f"\n##### MISSING {fn}")
        continue
    lines.append(f"\n\n===== {fn} =====")
    try:
        r = PdfReader(p)
        full = []
        for pg in r.pages:
            try:
                full.append(pg.extract_text() or "")
            except Exception:
                pass
        txt = " ".join(" ".join(full).split())
    except Exception as e:
        lines.append(f"[ERR {e}]")
        continue
    lines.append(f"[len={len(txt)}]")
    seen = set()
    for kw in KW:
        for m in re.finditer(re.escape(kw), txt, re.I):
            s = max(0, m.start() - 220)
            e = min(len(txt), m.start() + 260)
            snip = txt[s:e]
            key = snip[:80]
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"--- [{kw}] ...{snip}...")
            if len([x for x in lines if x.startswith('---')]) > 90:
                break

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("WROTE", len(lines), "lines")
