import os, json, urllib.parse, urllib.request, ssl

OUTDIR = r"C:\Users\mmrgr\Desktop\论文9.15补充"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
CTX = ssl.create_default_context()

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def search(query):
    url = "https://api.crossref.org/works?query=%s&rows=6" % urllib.parse.quote(query)
    try:
        d = get_json(url)
        out = []
        for it in d["message"]["items"]:
            t = (it.get("title") or [""])[0]
            a = (it.get("author") or [{}])[0]
            fa = a.get("family") or a.get("name") or "?"
            y = str((it.get("issued",{}).get("date-parts",[[""]])[0])[0] or "")
            # collect all authors
            aus = []
            for x in it.get("author", [])[:4]:
                aus.append(x.get("family") or x.get("given","") or "")
            out.append({"title": t, "authors": aus, "year": y, "doi": it.get("DOI","")})
        return out
    except Exception as e:
        return [{"error": str(e)}]

queries = {
    "Hsieh2010": "Hsieh Walker Chien Dzombak Vidic plant cooling municipal wastewater",
    "Walker2012": "Walker Vidic Dzombak tertiary treated municipal wastewater scale formation cooling",
    "Wang2020": "Wang Yang Sun water reuse recycling industrial systems review technologies applications",
}
print("=== TARGETED CROSSREF SEARCH ===")
for k, q in queries.items():
    print("\n--- %s : %s ---" % (k, q))
    for r in search(q):
        print(json.dumps(r, ensure_ascii=False))

# retry MDPI #16 with referer
def try_dl(url, dest, referer=None):
    try:
        h = {"User-Agent": UA, "Accept": "application/pdf,*/*"}
        if referer: h["Referer"] = referer
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            data = r.read()
        if data[:4] == b"%PDF" and len(data) > 5000:
            open(dest, "wb").write(data)
            return "OK %d bytes" % len(data)
        return "NOT_PDF %d" % len(data)
    except Exception as e:
        return "ERR %s" % str(e)[:120]

print("\n=== MDPI RETRY ===")
dest = os.path.join(OUTDIR, "16_Qin2016_Water.pdf")
print("16_Qin2016_Water.pdf:", try_dl("https://www.mdpi.com/2073-4441/8/4/157/pdf", dest, referer="https://www.mdpi.com/2073-4441/8/4/157"))
