import json, urllib.request, urllib.parse, time, ssl

EMAIL = "research@example.edu"  # valid-format contact for Unpaywall
DOIS = [
    ("01_Wang2026_ESE",            "10.1016/j.ese.2026.100702"),
    ("02_Lei2025_RCR",             "10.1016/j.resconrec.2025.108310"),
    ("03_Jiang2025_ApplEnergy",    "10.1016/j.apenergy.2025.126522"),
    ("04_Lei2022_RCR",             "10.1016/j.resconrec.2022.106323"),
    ("05_Li2025_CACM",             "10.1145/3724499"),
    ("06_Siddik2021_ERL",          "10.1088/1748-9326/abfba1"),
    ("07_Karimi2022_RCR",          "10.1016/j.resconrec.2022.106194"),
    ("08_Privette2026_AGUAdv",     "10.1029/2025AV002140"),
    ("09_Barnett2026_WaterRes",    "10.1016/j.watres.2026.125866"),
    ("10_Behzadian2014_DWES",      "10.5194/dwes-7-63-2014"),
    ("11_Dobson2024_GMD",          "10.5194/gmd-17-4495-2024"),
    ("12_Landa2020_ESPR",          "10.1007/s11356-019-05465-8"),
    ("13_Renouf2018_WaterRes",     "10.1016/j.watres.2018.01.070"),
    ("14_Alissa2025_Nature",       "10.1038/s41586-025-08832-3"),
    ("15_Mytton2021_npjCW",        "10.1038/s41545-021-00101-w"),
    ("16_Zou2025_ApplEnergy",      "10.1016/j.apenergy.2025.125700"),
    ("17_Radini2021_ApplEnergy",   "10.1016/j.apenergy.2021.117268"),
    ("18_Dai2022_JCLP",            "10.1016/j.jclepro.2022.131137"),
    ("19_Zhou2019_STOTEN",         "10.1016/j.scitotenv.2019.02.146"),
    ("20_HousePeters2011_WRR",     "10.1029/2010WR009624"),
]

ctx = ssl.create_default_context()
out = []
for name, doi in DOIS:
    url = f"https://api.unpaywall.org/v2/{doi}?email={urllib.parse.quote(EMAIL)}"
    rec = {"name": name, "doi": doi}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8"))
        rec["oa_status"] = data.get("oa_status")
        rec["oa_status_reason"] = data.get("oa_status_reason")
        best = data.get("best_oa_location") or {}
        rec["best_oa_url"] = best.get("url")
        rec["best_oa_pdf"] = best.get("pdf_url")
        rec["best_oa_repo"] = (best.get("repository") or {}).get("name")
        # also list any green/gold locations with pdf
        locs = []
        for loc in (data.get("oa_locations") or []):
            if loc.get("pdf_url"):
                locs.append({"url": loc.get("url"), "pdf": loc.get("pdf_url"),
                             "repo": (loc.get("repository") or {}).get("name"),
                             "version": loc.get("version"), "host": loc.get("host_type")})
        rec["all_pdf_locs"] = locs
    except Exception as e:
        rec["error"] = str(e)
    out.append(rec)
    time.sleep(0.3)

with open("C:\\Users\\mmrgr\\WorkBuddy\\2026-09-15-10-49-54\\oa_result.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("DONE", len(out))
