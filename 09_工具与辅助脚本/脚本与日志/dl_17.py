import urllib.request, ssl, os, sys
print("START", flush=True)
OUT = "C:\\Users\\mmrgr\\Desktop\\论文9.15"
ctx = ssl.create_default_context()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0.0.0 Safari/537.36"
urls = [
  "https://zenodo.org/records/7561635/files/Radini_2021.pdf",
  "https://zenodo.org/record/7561635/files/Radini_2021.pdf",
]
for url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
            data = r.read()
        open(os.path.join(OUT, "17_Radini2021_ApplEnergy.pdf"), "wb").write(data)
        print(f"OK {url} {len(data)} PDF={data[:4]==b'%PDF'}", flush=True)
        break
    except Exception as e:
        print(f"ERR {url}: {e}", flush=True)
print("DONE", flush=True)
