import os, glob, sys
from pypdf import PdfReader

DIR = r"C:\Users\mmrgr\Desktop\论文9.15"
files = sorted(glob.glob(os.path.join(DIR, "*.pdf")))
out = []
for f in files:
    name = os.path.basename(f)
    try:
        r = PdfReader(f)
        meta = r.metadata or {}
        title = (meta.get("/Title") or "").strip()
        # first page text snippet
        txt = ""
        try:
            pg = r.pages[0]
            txt = pg.extract_text() or ""
        except Exception as e:
            txt = "(text-extract-fail:%s)" % e
        snippet = " ".join(txt.split())[:300]
        npages = len(r.pages)
        out.append("FILE: %s\n  size=%d pages=%d\n  title=%r\n  snippet=%s\n" % (name, os.path.getsize(f), npages, title, snippet))
    except Exception as e:
        out.append("FILE: %s\n  ERROR: %s\n" % (name, e))
print("\n".join(out))
