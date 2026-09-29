import urllib.request, json

def fetch_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())

for email in ["workbuddy@workbuddy.ai", "reader@workbuddy.cn", "a.b@gmail.com"]:
    url = f"https://api.unpaywall.org/v2/10.5194/dwes-7-63-2014?email={email}"
    try:
        status, data = fetch_json(url)
        print(email, "->", status, "oa=", data.get("oa_status"), "pdf=", (data.get("best_oa_location") or {}).get("pdf_url"))
    except Exception as e:
        print(email, "-> ERR", repr(e))
