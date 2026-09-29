import os, json, urllib.parse, urllib.request, ssl

OUTDIR = r"C:\Users\mmrgr\Desktop\论文9.15补充"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
CTX = ssl.create_default_context()

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def search_crossref(title_query):
    url = "https://api.crossref.org/works?query.bibliographic=%s&rows=5" % urllib.parse.quote(title_query)
    try:
        d = get_json(url)
        out = []
        for it in d["message"]["items"]:
            t = (it.get("title") or [""])[0]
            a = (it.get("author") or [{}])[0]
            fa = a.get("family") or a.get("name") or "?"
            y = str((it.get("issued",{}).get("date-parts",[[""]])[0])[0] or "")
            doi = it.get("DOI","")
            out.append({"title": t, "first_author": fa, "year": y, "doi": doi})
        return out
    except Exception as e:
        return [{"error": str(e)}]

titles = {
    "Hsieh2010": "Secondary treated municipal wastewater for plant cooling Water reuse and energy nexus",
    "Walker2012": "Water quality and scale formation in cooling systems using tertiary treated municipal wastewater",
    "Wang2020": "Water reuse and recycling in industrial systems A review of technologies and applications",
}
print("=== CROSSREF TITLE SEARCH (correct DOIs) ===")
for k, q in titles.items():
    print("\n--- %s ---" % k)
    for r in search_crossref(q):
        print(json.dumps(r, ensure_ascii=False))

# Direct OA downloads
def try_dl(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            data = r.read()
        if data[:4] == b"%PDF" and len(data) > 5000:
            open(dest, "wb").write(data)
            return "OK %d bytes" % len(data)
        return "NOT_PDF %d bytes (head=%r)" % (len(data), data[:20])
    except Exception as e:
        return "ERR %s" % str(e)[:120]

print("\n=== DIRECT OA DOWNLOAD ATTEMPTS ===")
jobs = [
    ("06_Chen2022_FrontEnergy.pdf", "https://www.frontiersin.org/articles/10.3389/fenrg.2022.952680/pdf"),
    ("16_Qin2016_Water.pdf", "https://www.mdpi.com/2073-4441/8/4/157/pdf"),
    ("09_Cai2025_EcolModel.pdf", "https://www.sciencedirect.com/science/article/pii/S0304389424010972/pdfft?isRDR=true"),
]
for fn, url in jobs:
    dest = os.path.join(OUTDIR, fn)
    if os.path.exists(dest):
        print("%s: SKIP exists" % fn); continue
    msg = try_dl(url, dest)
    print("%s: %s" % (fn, msg))
