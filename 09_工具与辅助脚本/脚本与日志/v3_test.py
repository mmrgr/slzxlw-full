#!/usr/bin/env python3
import urllib.request, http.cookiejar, re, os
UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9"}
CJ=http.cookiejar.CookieJar()
OP=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))
OUT=r"C:\Users\mmrgr\Desktop\论文9.15"

def get(url, ref=None, binary=False, timeout=30):
    h=dict(H)
    if ref: h["Referer"]=ref
    if binary: h["Accept"]="application/pdf,*/*"
    req=urllib.request.Request(url, headers=h)
    r=OP.open(req, timeout=timeout)
    return r.getcode(), (r.read() if binary else r.read().decode("utf-8","replace")), r.geturl()

def save(name, data):
    p=os.path.join(OUT,name)
    with open(p,"wb") as f: f.write(data)
    return p

tests=[
 ("01_Wang2026_ESE","10.1016/j.ese.2026.100702","Elsevier"),
 ("06_Siddik2021_ERL","10.1088/1748-9326/abfba1","IOP"),
 ("08_Privette2026_AGUAdv","10.1029/2025AV002140","AGU"),
 ("05_Li2025_CACM","10.1145/3724499","ACM"),
 ("02_Lei2025_RCR","10.1016/j.resconrec.2025.108310","Elsevier"),
]
for name,doi,pub in tests:
    try:
        if pub=="Elsevier":
            code,html,final=get("https://doi.org/"+doi)
            # find pdf link in html / final page
            urls=set(re.findall(r'(https://www\.sciencedirect\.com/[^"\']*?pdfft[^"\']*)', html))
            urls|=set(re.findall(r'(https://www\.sciencedirect\.com/[^"\']*?/pdf[^"\']*)', html))
            # also from final url pii
            m=re.search(r"pii/([A-Za-z0-9]+)", final)
            if m:
                pii=m.group(1)
                urls.add(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isRDR=true")
            got=False
            for u in list(urls)[:6]:
                try:
                    c,d,f=get(u, ref=final if 'sciencedirect' in final else None, binary=True, timeout=30)
                    if c==200 and d[:4]==b"%PDF" and len(d)>10240:
                        save(name+".pdf", d); print(f"{name}: OK via {u[:70]} size={len(d)}"); got=True; break
                except Exception as e:
                    pass
            if not got: print(f"{name}: no PDF (urls found={len(urls)})")
        elif pub=="IOP":
            art=f"https://iopscience.iop.org/article/{doi}"
            code,html,final=get(art)
            c,d,f=get(art+"/pdf", ref=art, binary=True)
            if d[:4]==b"%PDF" and len(d)>10240:
                save(name+".pdf", d); print(f"{name}: OK size={len(d)}")
            else:
                print(f"{name}: not pdf (ctype/page), len={len(d)}")
        elif pub=="AGU":
            art=f"https://agupubs.onlinelibrary.wiley.com/doi/abs/{doi}"
            code,html,final=get(art)
            for u in [f"https://agupubs.onlinelibrary.wiley.com/doi/pdf/{doi}", f"https://agupubs.onlinelibrary.wiley.com/doi/epdf/{doi}"]:
                try:
                    c,d,f=get(u, ref=art, binary=True)
                    if c==200 and d[:4]==b"%PDF" and len(d)>10240:
                        save(name+".pdf", d); print(f"{name}: OK via {u[:60]} size={len(d)}"); break
                except Exception as e:
                    print(f"{name}: {u[:50]} -> {repr(e)[:60]}")
            else:
                print(f"{name}: AGU no pdf")
        elif pub=="ACM":
            art=f"https://dl.acm.org/doi/10.1145/3724499"
            code,html,final=get(art)
            c,d,f=get("https://dl.acm.org/doi/pdf/10.1145/3724499", ref=art, binary=True)
            if d[:4]==b"%PDF" and len(d)>10240:
                save(name+".pdf", d); print(f"{name}: OK size={len(d)}")
            else:
                print(f"{name}: ACM not pdf len={len(d)}")
    except Exception as e:
        print(f"{name}: ERR {repr(e)[:120]}")
