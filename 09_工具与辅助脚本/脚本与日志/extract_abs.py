import os, glob
from pypdf import PdfReader

folders = [r"C:\Users\mmrgr\Desktop\论文9.15", r"C:\Users\mmrgr\Desktop\论文9.15补充"]
out = r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\abstracts.txt"
lines = []
for f in folders:
    for p in sorted(glob.glob(os.path.join(f, "*.pdf"))):
        name = os.path.basename(p)
        lines.append("\n\n########## " + name + " ##########")
        try:
            r = PdfReader(p)
            txt = ""
            try:
                txt = r.pages[0].extract_text() or ""
            except Exception as e:
                txt = f"[page1 err {e}]"
            txt = " ".join(txt.split())
            lines.append(txt[:1600])
        except Exception as e:
            lines.append(f"[ERR {e}]")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("WROTE", out, len(lines))
