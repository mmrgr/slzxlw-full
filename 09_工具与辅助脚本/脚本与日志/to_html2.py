import markdown, os
import importlib.util

spec = importlib.util.spec_from_file_location("t", r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\to_html.py")
# just re-implement to avoid executing the module
src = r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md"
out = r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.html"

body = markdown.markdown(
    open(src, encoding="utf-8").read(),
    extensions=["tables", "fenced_code", "sane_lists", "toc"],
)

css = """
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; color:#1f2328;
       background:#ffffff; margin:0; padding:48px 24px; line-height:1.75; }
.wrap { max-width: 980px; margin:0 auto; }
h1 { font-size: 28px; border-bottom: 3px solid #1f6f8f; padding-bottom: 12px; margin-top: 8px; }
h2 { font-size: 22px; margin-top: 40px; padding-left: 12px; border-left: 5px solid #1f6f8f; color:#10394d; }
h3 { font-size: 18px; margin-top: 28px; color:#17506a; }
blockquote { margin: 20px 0; padding: 12px 20px; background:#f2f8fb; border-left:4px solid #4a9dc4;
             color:#1d3f52; border-radius:0 6px 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14px; }
th, td { border: 1px solid #d5e3ea; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #e8f2f7; font-weight: 600; color:#10394d; }
tr:nth-child(even) td { background: #fafcfe; }
code { background:#eff3f5; padding:2px 6px; border-radius:4px; font-family: Consolas, monospace; font-size: 13px; }
pre { background:#f5f9fb; padding:14px; border-radius:8px; overflow:auto; border:1px solid #dfe9ef; }
hr { border:none; border-top:1px solid #dfe9ef; margin:36px 0; }
strong { color:#111; }
li { margin: 4px 0; }
a { color:#1a6d94; }
"""
html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-UWM 下一轮模拟：情景设置与实施方案</title>
<style>{css}</style></head><body><div class="wrap">{body}</div></body></html>"""
open(out, "w", encoding="utf-8").write(html)
print("WROTE", out)
