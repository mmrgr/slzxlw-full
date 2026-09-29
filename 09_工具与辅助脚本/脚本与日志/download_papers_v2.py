#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legitimate batch PDF downloader: Unpaywall OA + publisher open-access URLs.
No Sci-Hub / no paywall circumvention. Validates each file is a real PDF.
"""
import urllib.request, urllib.error, http.cookiejar, json, os, re, time, sys

EMAIL = "workbuddy@workbuddy.ai"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "application/pdf,application/x-pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# cookie-aware opener so Wiley/IOP can set session cookies
CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))

PAPERS = [
    ("01","Wang","2026","ESE","10.1016/j.ese.2026.100702","Elsevier"),
    ("02","Lei","2025","RCR","10.1016/j.resconrec.2025.108310","Elsevier"),
    ("03","Jiang","2025","ApplEnergy","10.1016/j.apenergy.2025.126522","Elsevier"),
    ("04","Lei","2022","RCR","10.1016/j.resconrec.2022.106323","Elsevier"),
    ("05","Li","2025","CACM","10.1145/3724499","ACM"),
    ("06","Siddik","2021","ERL","10.1088/1748-9326/abfba1","IOP"),
    ("07","Karimi","2022","RCR","10.1016/j.resconrec.2022.106194","Elsevier"),
    ("08","Privette","2026","AGUAdv","10.1029/2025AV002140","AGU/Wiley"),
    ("09","Barnett-Itzhaki","2026","WaterRes","10.1016/j.watres.2026.125866","Elsevier"),
    ("10","Behzadian","2014","DWES","10.5194/dwes-7-63-2014","Copernicus"),
    ("11","Dobson","2024","GMD","10.5194/gmd-17-4495-2024","Copernicus"),
    ("12","Landa-Cansigno","2020","ESPR","10.1007/s11356-019-05465-8","Springer"),
    ("13","Renouf","2018","WaterRes","10.1016/j.watres.2018.01.070","Elsevier"),
    ("14","Alissa","2025","Nature","10.1038/s41586-025-08832-3","Nature"),
    ("15","Mytton","2021","npjCW","10.1038/s41545-021-00101-w","Nature/npj"),
    ("16","Zou","2025","ApplEnergy","10.1016/j.apenergy.2025.125700","Elsevier"),
    ("17","Radini","2021","ApplEnergy","10.1016/j.apenergy.2021.117268","Elsevier"),
    ("18","Dai","2022","JCLP","10.1016/j.jclepro.2022.131137","Elsevier"),
    ("19","Zhou","2019","STOTEN","10.1016/j.scitotenv.2019.02.146","Elsevier"),
    ("20","House-Peters","2011","WRR","10.1029/2010WR009624","AGU/Wiley"),
]

def fetch(url, timeout=25, referer=None):
    h = dict(HEADERS)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    resp = OPENER.open(req, timeout=timeout)
    return resp.getcode(), resp.read(), resp.geturl()

def is_pdf(data):
    return bool(data) and data[:4] == b"%PDF" and len(data) > 10240

def unpaywall_candidates(doi):
    cands = []
    try:
        req = urllib.request.Request(
            f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}",
            headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read())
        locs = data.get("oa_locations") or []
        def grade(l):
            ht = l.get("host_type") or ""
            ver = (l.get("version") or "").lower()
            if ht == "publisher" and "gold" in ver: return 0
            if ht == "publisher": return 1
            if "gold" in ver: return 2
            return 3
        locs.sort(key=grade)
        for l in locs:
            p = l.get("pdf_url")
            if p:
                cands.append(("unpaywall:"+(l.get("host_type") or ""), p))
    except Exception:
        pass
    return cands

def publisher_candidates(doi):
    c = []
    if doi.startswith("10.1016/"):  # Elsevier / ScienceDirect
        try:
            code, body, final = fetch("https://doi.org/"+doi, timeout=25)
            m = re.search(r"pii/([A-Za-z0-9]+)", final)
            if not m:
                m = re.search(r"/pii/([A-Za-z0-9]+)", body.decode("utf-8","replace"))
            if m:
                pii = m.group(1)
                art = f"https://www.sciencedirect.com/science/article/pii/{pii}"
                c.append(("SD-pdfft", f"{art}/pdfft?isRDR=true", art))
        except Exception:
            pass
    elif doi.startswith("10.1145/"):  # ACM
        c.append(("ACM", f"https://dl.acm.org/doi/pdf/{doi}", f"https://dl.acm.org/doi/10.1145/3724499"))
    elif doi.startswith("10.1088/"):  # IOP
        art = f"https://iopscience.iop.org/article/{doi}"
        c.append(("IOP", f"{art}/pdf", art))
    elif doi.startswith("10.1029/"):  # AGU / Wiley
        art = f"https://agupubs.onlinelibrary.wiley.com/doi/abs/{doi}"
        c.append(("AGU-pdf", f"https://agupubs.onlinelibrary.wiley.com/doi/pdf/{doi}", art))
        c.append(("AGU-epdf", f"https://agupubs.onlinelibrary.wiley.com/doi/epdf/{doi}", art))
    elif doi.startswith("10.1038/"):  # Nature / npj
        aid = doi.split("10.1038/",1)[1]
        c.append(("Nature", f"https://www.nature.com/articles/{aid}.pdf", f"https://www.nature.com/articles/{aid}"))
    elif doi.startswith("10.5194/"):  # Copernicus
        tok = doi.split("10.5194/",1)[1]
        parts = tok.split("-")
        if len(parts) >= 4:
            journal, vol, page, year = parts[0], parts[1], parts[2], parts[3]
            c.append(("Copernicus", f"https://{journal}.copernicus.org/articles/{vol}/{page}/{year}/{tok}.pdf", None))
    elif doi.startswith("10.1007/"):  # Springer
        c.append(("Springer", f"https://link.springer.com/content/pdf/{doi}.pdf", f"https://link.springer.com/article/{doi}"))
    return c

def try_download(idx, author, year, tag, doi, publisher):
    base = f"{idx}_{author}{year}_{tag}.pdf"
    path = os.path.join(OUT, base)
    candidates = unpaywall_candidates(doi) + publisher_candidates(doi)
    # normalize tuples: (label, url, referer_or_None)
    norm = []
    for item in candidates:
        if len(item) == 2:
            norm.append((item[0], item[1], None))
        else:
            norm.append(item)
    seen=set(); uniq=[]
    for label,u,ref in norm:
        if u not in seen:
            seen.add(u); uniq.append((label,u,ref))
    last = "no-candidate"
    for label, u, ref in uniq:
        try:
            code, data, final = fetch(u, timeout=30, referer=ref)
            if code == 200 and is_pdf(data):
                with open(path,"wb") as f:
                    f.write(data)
                return ("OK", label, len(data))
            last = f"{label}:status={code}" if code!=200 else f"{label}:not-pdf"
        except Exception as e:
            last = f"{label}:{repr(e)[:80]}"
            continue
    return ("FAIL", last, 0)

def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    for (idx, author, year, tag, doi, pub) in PAPERS:
        status, src, size = try_download(idx, author, year, tag, doi, pub)
        results.append((idx, author, year, tag, doi, pub, status, src, size))
        print(f"{idx} {author}{year} [{tag}] -> {status} ({src}) {size}B")
        sys.stdout.flush()
        time.sleep(0.4)
    with open(os.path.join(OUT, "_manifest.txt"), "w", encoding="utf-8") as f:
        for r in results:
            f.write("\t".join(str(x) for x in r)+"\n")
    ok = [r for r in results if r[6]=="OK"]
    fail = [r for r in results if r[6]!="OK"]
    print(f"\n=== SUMMARY: {len(ok)} OK / {len(results)} total; {len(fail)} failed ===")
    for r in fail:
        print("FAILED:", r[0], r[1], r[3], r[4], "->", r[7])

if __name__ == "__main__":
    main()
