#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download original PDFs for a list of papers into the target folder.
Strategy per paper:
  1) Unpaywall open-access pdf_urls (publisher gold first, then repositories)
  2) Publisher-specific direct PDF URL derived from DOI
  3) For Elsevier: resolve DOI -> ScienceDirect PII -> pdfft link
Validate each candidate is a real PDF (%PDF header, size > 10KB).
"""
import urllib.request, urllib.error, json, os, re, time, sys

EMAIL = "workbuddy@workbuddy.ai"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "application/pdf,application/x-pdf,*/*"}

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

def http_get(url, binary=False, timeout=30, max_redir=10):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=timeout)
    # urllib follows redirects automatically; read full body
    data = resp.read()
    return resp.status, data, resp.geturl()

def is_pdf(data):
    if not data: return False
    if data[:4] != b"%PDF": return False
    if len(data) < 10240: return False
    return True

def unpaywall_candidates(doi):
    cands = []
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read())
        locs = data.get("oa_locations") or []
        # prefer publisher gold, then any with pdf_url
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
            if p: cands.append(("unpaywall:"+ (l.get("host_type") or ""), p))
    except Exception as e:
        pass
    return cands

def publisher_candidates(doi, publisher):
    c = []
    if doi.startswith("10.1016/"):  # Elsevier / ScienceDirect
        # 1) resolve DOI -> article page with PII
        try:
            req = urllib.request.Request("https://doi.org/"+doi, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=25)
            final = resp.geturl()
            m = re.search(r"pii/([A-Za-z0-9]+)", final)
            if not m:
                body = resp.read().decode("utf-8","replace")
                m = re.search(r"/pii/([A-Za-z0-9]+)", body)
            if m:
                pii = m.group(1)
                c.append(("SD-pdfft", f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isRDR=true"))
            resp.close()
        except Exception:
            pass
        # 2) article HTML grep for pdfft
        try:
            req = urllib.request.Request("https://doi.org/"+doi, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=25)
            body = resp.read().decode("utf-8","replace")
            resp.close()
            for m in re.finditer(r'(https://www\.sciencedirect\.com/[^"\']*?/pdfft[^"\']*)', body):
                c.append(("SD-html", m.group(1)))
        except Exception:
            pass
    elif doi.startswith("10.1145/"):  # ACM
        c.append(("ACM", f"https://dl.acm.org/doi/pdf/{doi}"))
    elif doi.startswith("10.1088/"):  # IOP
        c.append(("IOP", f"https://iopscience.iop.org/article/{doi}/pdf"))
    elif doi.startswith("10.1029/"):  # AGU / Wiley
        c.append(("AGU-pdf", f"https://agupubs.onlinelibrary.wiley.com/doi/pdf/{doi}"))
        c.append(("AGU-epdf", f"https://agupubs.onlinelibrary.wiley.com/doi/epdf/{doi}"))
    elif doi.startswith("10.1038/"):  # Nature / npj
        aid = doi.split("10.1038/",1)[1]
        c.append(("Nature", f"https://www.nature.com/articles/{aid}.pdf"))
    elif doi.startswith("10.5194/"):  # Copernicus
        tok = doi.split("10.5194/",1)[1]  # e.g. dwes-7-63-2014
        parts = tok.split("-")
        if len(parts) >= 4:
            journal, vol, page, year = parts[0], parts[1], parts[2], parts[3]
            c.append(("Copernicus", f"https://{journal}.copernicus.org/articles/{vol}/{page}/{year}/{tok}.pdf"))
    elif doi.startswith("10.1007/"):  # Springer
        c.append(("Springer", f"https://link.springer.com/content/pdf/{doi}.pdf"))
    return c

def try_download(idx, author, year, tag, doi, publisher):
    base = f"{idx}_{author}{year}_{tag}.pdf"
    path = os.path.join(OUT, base)
    candidates = []
    candidates += unpaywall_candidates(doi)
    candidates += publisher_candidates(doi, publisher)
    # de-dup preserve order
    seen=set(); uniq=[]
    for src,u in candidates:
        if u not in seen:
            seen.add(u); uniq.append((src,u))
    for src, u in uniq:
        try:
            status, data, final = http_get(u, timeout=35)
            if status == 200 and is_pdf(data):
                with open(path,"wb") as f:
                    f.write(data)
                return ("OK", src, len(data), u)
            else:
                reason = f"status={status}" if status!=200 else "not-a-pdf"
                # continue to next candidate
                last = reason
        except Exception as e:
            last = repr(e)[:120]
            continue
    return ("FAIL", last if 'last' in dir() else "no-candidate", 0, "")

def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    for (idx, author, year, tag, doi, pub) in PAPERS:
        try:
            status, src, size, url = try_download(idx, author, year, tag, doi, pub)
        except Exception as e:
            status, src, size, url = "ERROR", repr(e)[:120], 0, ""
        results.append((idx, author, year, tag, doi, pub, status, src, size))
        print(f"{idx} {author}{year} [{tag}] -> {status} ({src}) {size}B  {doi}")
        sys.stdout.flush()
        time.sleep(0.3)
    # write manifest
    with open(os.path.join(OUT, "_manifest.txt"), "w", encoding="utf-8") as f:
        for (idx, author, year, tag, doi, pub, status, src, size) in results:
            f.write(f"{idx}\t{author}{year}\t{tag}\t{pub}\t{status}\t{src}\t{size}\t{doi}\n")
    ok = [r for r in results if r[6]=="OK"]
    fail = [r for r in results if r[6]!="OK"]
    print(f"\n=== SUMMARY: {len(ok)} OK / {len(results)} total; {len(fail)} failed ===")
    for r in fail:
        print("FAILED:", r[0], r[1], r[3], r[4], "->", r[7])

if __name__ == "__main__":
    main()
