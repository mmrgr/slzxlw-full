import urllib.request, json, sys

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (workbuddy-paper-downloader)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

# Test 1: Unpaywall with a known-OA DOI
doi = "10.5194/dwes-7-63-2014"
url = f"https://api.unpaywall.org/v2/{doi}?email=research.assistant@example.com"
try:
    status, body = fetch(url)
    data = json.loads(body)
    print("UNPAYWALL_OK", status, "oa=", data.get("oa_status"), "pdf=", (data.get("best_oa_location") or {}).get("pdf_url"))
except Exception as e:
    print("UNPAYWALL_ERR", repr(e))
    # try to read error body
    try:
        if hasattr(e, 'read'):
            print("BODY", e.read().decode('utf-8','replace')[:500])
    except Exception as e2:
        print("BODY_ERR", repr(e2))

# Test 2: direct nature pdf
try:
    status, body = fetch("https://www.nature.com/articles/s41545-021-00101-w.pdf", timeout=20)
    print("NATURE_PDF", status, "len=", len(body), "ctype=", None)
except Exception as e:
    print("NATURE_ERR", repr(e))
