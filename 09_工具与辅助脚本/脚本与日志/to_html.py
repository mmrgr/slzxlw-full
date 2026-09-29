import markdown

src = r"C:\Users\mmrgr\Desktop\开题\AI-UWM研究深化_文献映射与发表路径.md"
out = r"C:\Users\mmrgr\Desktop\开题\AI-UWM研究深化_文献映射与发表路径.html"

body = markdown.markdown(
    open(src, encoding="utf-8").read(),
    extensions=["tables", "fenced_code", "sane_lists", "toc"],
)

css = """
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; color:#1f2328;
       background:#ffffff; margin:0; padding:48px 24px; line-height:1.75; }
.wrap { max-width: 960px; margin:0 auto; }
h1 { font-size: 28px; border-bottom: 3px solid #2f6f4e; padding-bottom: 12px; margin-top: 8px; }
h2 { font-size: 22px; margin-top: 40px; padding-left: 12px; border-left: 5px solid #2f6f4e; color:#14432c; }
h3 { font-size: 18px; margin-top: 28px; color:#1c5a3a; }
blockquote { margin: 20px 0; padding: 12px 20px; background:#f3f8f5; border-left:4px solid #4a9d6f; color:#2a4a3a; border-radius:0 6px 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14px; }
th, td { border: 1px solid #d8e0da; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #eaf3ed; font-weight: 600; color:#14432c; }
tr:nth-child(even) td { background: #fafcfb; }
code { background:#f0f2f1; padding:2px 6px; border-radius:4px; font-family: Consolas, monospace; font-size: 13px; }
pre { background:#f6f8f7; padding:14px; border-radius:8px; overflow:auto; border:1px solid #e2e8e4; }
hr { border:none; border-top:1px solid #e2e8e4; margin:36px 0; }
strong { color:#111; }
li { margin: 4px 0; }
a { color:#1c7a4b; }
"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-UWM 研究深化路线</title>
<style>{css}</style></head>
<body><div class="wrap">
{body}
</div></body></html>"""

open(out, "w", encoding="utf-8").write(html)
print("WROTE", out, len(html), "chars")
