import os, glob, hashlib
from pypdf import PdfReader

folders = [
    r"C:\Users\mmrgr\Desktop\论文9.15",
    r"C:\Users\mmrgr\Desktop\论文9.15补充",
]
hashes = {}
for f in folders:
    print("=== FOLDER:", f, "EXISTS:", os.path.isdir(f))
    for p in sorted(glob.glob(os.path.join(f, "*.pdf"))):
        try:
            r = PdfReader(p)
            meta = r.metadata
            title = (meta.title if meta and meta.title else "") or ""
            txt = ""
            try:
                txt = r.pages[0].extract_text() or ""
            except Exception:
                txt = ""
            txt = " ".join(txt.split())[:400]
            data = open(p, "rb").read()
            h = hashlib.md5(data).hexdigest()
            dup = [os.path.basename(x) for x, hh in hashes.items() if hh == h]
            hashes[p] = h
            print(f"\nFILE: {os.path.basename(p)}\n  SIZE: {os.path.getsize(p)}  MD5: {h[:8]}")
            if dup:
                print("  >>> DUPLICATE OF:", dup)
            print(f"  META_TITLE: {title[:160]}")
            print(f"  PAGE1: {txt}")
        except Exception as e:
            print(f"\nFILE: {os.path.basename(p)}\n  ERROR: {e}")
