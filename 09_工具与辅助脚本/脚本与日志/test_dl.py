import urllib.request, os
UA="Mozilla/5.0"
H={"User-Agent":UA,"Accept":"application/pdf,*/*"}
OUT=r"C:\Users\mmrgr\Desktop\论文9.15"
tests=[
 ("10_Copernicus_test","https://dwes.copernicus.org/articles/7/63/2014/dwes-7-63-2014.pdf"),
 ("06_IOP_test","https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf"),
 ("15_npj_test","https://www.nature.com/articles/s41545-021-00101-w.pdf"),
 ("08_AGU_test","https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2025AV002140"),
]
for name,url in tests:
    try:
        req=urllib.request.Request(url,headers=H)
        with urllib.request.urlopen(req,timeout=30) as r:
            data=r.read()
        ok = data[:4]==b"%PDF" and len(data)>10240
        path=os.path.join(OUT,name+(".pdf" if ok else ".bin"))
        with open(path,"wb") as f: f.write(data)
        print(f"{name}: status ok={ok} size={len(data)} saved={path}")
    except Exception as e:
        print(f"{name}: ERR {repr(e)[:160]}")
