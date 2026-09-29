import urllib.request, ssl, os

OUT = "C:\\Users\\mmrgr\\Desktop\\论文9.15"
ctx = ssl.create_default_context()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"

jobs = [
    ("02_Lei2025_RCR.pdf",        "https://escholarship.org/content/qt1vx545q7/qt1vx545q7.pdf"),
    ("13_Renouf2018_WaterRes.pdf","https://eprints.qut.edu.au/205145/1/68911651.pdf"),
    ("17_Radini2021_ApplEnergy.pdf","https://zenodo.org/records/7561635/files/Radini_2021.pdf"),
]

for fname, url in jobs:
    dest = os.path.join(OUT, fname)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*", "Referer": url})
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
        open(dest, "wb").write(data)
        ok = data[:4] == b"%PDF"
        print(f"{fname}: {len(data)} bytes  PDF_HEAD={ok}")
    except Exception as e:
        print(f"{fname}: ERROR {e}")
