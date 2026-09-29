"""把情景设计 Markdown 转成单文件 HTML（学术风、可打印）。"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def convert(md: str, title: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    toc: list[tuple[int, str, str]] = []
    while i < len(lines):
        line = lines[i]
        # fenced code
        if line.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue
        # table
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table>")
            out.append("<thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in header) + "</tr></thead>")
            out.append("<tbody>")
            for row in rows:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = inline(m.group(2))
            anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", m.group(2)).strip("-").lower() or f"h{len(toc)}"
            if level <= 2:
                toc.append((level, text, anchor))
            out.append(f'<h{level} id="{anchor}">{text}</h{level}>')
            i += 1
            continue
        if re.match(r"^\s*(---|\*\*\*)\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        m = re.match(r"^\s*>\s?(.*)$", line)
        if m:
            buf = [m.group(1)]
            i += 1
            while i < len(lines) and (re.match(r"^\s*>\s?(.*)$", lines[i]) or lines[i].strip() == ""):
                if lines[i].strip() == "":
                    if i + 1 < len(lines) and re.match(r"^\s*>\s?", lines[i + 1]):
                        buf.append("")
                        i += 1
                        continue
                    break
                buf.append(re.match(r"^\s*>\s?(.*)$", lines[i]).group(1))
                i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf) + "</blockquote>")
            continue
        m = re.match(r"^\s*([-*])\s+(.*)$", line)
        if m:
            items = []
            while i < len(lines) and re.match(r"^\s*([-*])\s+(.*)$", lines[i]):
                items.append(re.match(r"^\s*([-*])\s+(.*)$", lines[i]).group(2))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ul>")
            continue
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if m:
            items = []
            while i < len(lines) and re.match(r"^\s*(\d+)\.\s+(.*)$", lines[i]):
                items.append(re.match(r"^\s*(\d+)\.\s+(.*)$", lines[i]).group(2))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ol>")
            continue
        if line.strip() == "":
            i += 1
            continue
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    nav = "\n".join(
        f'<a class="toc-h{level}" href="#{anchor}">{text}</a>' for level, text, anchor in toc
    )
    return TEMPLATE.format(title=html.escape(title), toc=nav, body="\n".join(out))


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --ink:#1c1e21; --muted:#5b6470; --line:#dfe3e8; --accent:#1f5f8b; --bg:#ffffff; --soft:#f6f8fa; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:"Segoe UI","PingFang SC","Microsoft YaHei",-apple-system,Helvetica,Arial,sans-serif;
    font-size:15px; line-height:1.75; }}
  .wrap {{ display:flex; max-width:1180px; margin:0 auto; gap:36px; padding:36px 24px 80px; }}
  nav {{ position:sticky; top:24px; align-self:flex-start; width:250px; flex:0 0 250px;
    max-height:calc(100vh - 60px); overflow:auto; border-right:1px solid var(--line); padding-right:16px; }}
  nav .toc-h1 {{ display:block; font-weight:700; margin:10px 0 4px; color:var(--ink); text-decoration:none; }}
  nav .toc-h2 {{ display:block; font-size:13px; color:var(--muted); margin:2px 0 2px 12px; text-decoration:none; }}
  nav a:hover {{ color:var(--accent); }}
  main {{ flex:1 1 auto; min-width:0; }}
  h1 {{ font-size:26px; margin:0 0 6px; padding-bottom:10px; border-bottom:2px solid var(--accent); }}
  h2 {{ font-size:20px; margin:34px 0 10px; padding-left:10px; border-left:4px solid var(--accent); }}
  h3 {{ font-size:16.5px; margin:22px 0 6px; color:#20303d; }}
  h4 {{ font-size:15px; margin:16px 0 4px; color:var(--muted); }}
  p {{ margin:8px 0; }}
  ul, ol {{ margin:8px 0 8px 22px; padding:0; }}
  li {{ margin:3px 0; }}
  code {{ background:var(--soft); border:1px solid var(--line); border-radius:3px;
    padding:1px 5px; font-family:"Cascadia Mono",Consolas,Monaco,monospace; font-size:13px; }}
  pre {{ background:var(--soft); border:1px solid var(--line); border-radius:6px;
    padding:12px 14px; overflow:auto; font-size:12.5px; line-height:1.6; }}
  pre code {{ background:none; border:none; padding:0; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:13.5px; }}
  th, td {{ border:1px solid var(--line); padding:6px 9px; text-align:left; vertical-align:top; }}
  th {{ background:var(--soft); font-weight:600; }}
  tr:nth-child(even) td {{ background:#fbfcfd; }}
  blockquote {{ margin:12px 0; padding:10px 14px; background:#f2f6f9;
    border-left:4px solid var(--accent); color:#33404d; font-size:14px; }}
  hr {{ border:none; border-top:1px solid var(--line); margin:26px 0; }}
  a {{ color:var(--accent); }}
  @media print {{ nav {{ display:none; }} .wrap {{ display:block; max-width:none; padding:0; }} }}
</style>
</head>
<body>
<div class="wrap">
<nav>{toc}</nav>
<main>
{body}
</main>
</div>
</body>
</html>
"""


def main() -> None:
    src = Path(sys.argv[1])
    title = sys.argv[2] if len(sys.argv) > 2 else src.stem
    dst = src.with_suffix(".html")
    dst.write_text(convert(src.read_text(encoding="utf-8"), title), encoding="utf-8")
    print(f"written -> {dst}")


if __name__ == "__main__":
    main()
