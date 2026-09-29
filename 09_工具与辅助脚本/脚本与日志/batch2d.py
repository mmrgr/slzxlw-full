import json, urllib.parse, urllib.request, ssl
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0.0.0 Safari/537.36"
CTX = ssl.create_default_context()
def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))
def search(title):
    url = "https://api.crossref.org/works?query.bibliographic=%s&rows=4" % urllib.parse.quote(title)
    try:
        d = get_json(url)
        out=[]
        for it in d["message"]["items"]:
            t=(it.get("title") or [""])[0]
            a=(it.get("author") or [{}])[0]
            fa=a.get("family") or a.get("name") or "?"
            y=str((it.get("issued",{}).get("date-parts",[[""]])[0])[0] or "")
            out.append({"title":t,"first_author":fa,"year":y,"doi":it.get("DOI","")})
        return out
    except Exception as e:
        return [{"error":str(e)}]
qs = {
 "Hsieh2010":"Secondary treated municipal wastewater for plant cooling Water reuse and energy nexus",
 "Walker2012":"Water quality and scale formation in cooling systems using tertiary treated municipal wastewater",
 "Wang2020":"Water reuse and recycling in industrial systems review technologies applications",
}
for k,q in qs.items():
    print("\n=== %s ===" % k)
    for r in search(q):
        print(json.dumps(r, ensure_ascii=False))
