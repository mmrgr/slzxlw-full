# -*- coding: utf-8 -*-
"""1) 修正去名遗留的异常空格；2) 把 references/*.json 改写为策展型出处记录。"""
import io
import json
import subprocess

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"

# --- 1) 修正散文残留 ---
p = ROOT + "/output/网络资料与项目功能审计.md"
s = io.open(p, encoding="utf-8").read()
old = "需由该类 绩效模型评估"
if old in s:
    s = s.replace(old, "需由该类绩效模型评估")
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("fixed stray space:", p)
else:
    print("stray space not found (already ok)")


# --- 2) 策展型出处记录 ---
def curated(path, record_id, summary, project=None):
    raw = subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT)
    d = json.loads(raw.decode("utf-8"))
    out = {
        "record_type": "curated_provenance",
        "source_note": (
            "本文件是策展型出处记录，不是上游元数据原文照录：为去标识化，上游题名、引文串、摘要"
            "与页面链接中包含商标字样的字段已裁剪。定位来源请使用 record_id / download_url。"
        ),
        "record_id": record_id,
        "repository": "University of Exeter institutional repository (figshare)",
        "published_date": d.get("published_date"),
        "version": d.get("version"),
        "license": d.get("license"),
        "authors": [a.get("full_name") for a in d.get("authors", [])],
        "summary": summary,
        "files": [
            {
                "name": f.get("name"),
                "size": f.get("size"),
                "mimetype": f.get("mimetype"),
                "supplied_md5": f.get("supplied_md5"),
                "computed_md5": f.get("computed_md5"),
                "download_url": f.get("download_url"),
            }
            for f in d.get("files", [])
        ],
    }
    if project:
        out["project"] = project
    tgt = ROOT + "/" + path
    with io.open(tgt, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("curated:", path)


curated(
    "references/D33.2_figshare_metadata.json",
    29706515,
    "TRUST 项目 D33.2 最终报告：城市水系统定量绩效模型的方法学说明与软件/工具包描述。"
    "许可为 All rights reserved，故本仓库不随附 PDF；请按 download_url 获取。",
    project="TRUST",
)
curated(
    "references/Oslo_report_figshare_metadata.json",
    29701109,
    "TRUST 项目 Oslo 案例研究报告：30 年规划期缺水情景下的城市水系统案例设定与绩效评估。"
    "许可为 All rights reserved，故本仓库不随附 PDF；请按 download_url 获取。",
    project="TRUST",
)

# --- 校验 ---
for f in [
    "references/D33.2_figshare_metadata.json",
    "references/Oslo_report_figshare_metadata.json",
]:
    txt = io.open(ROOT + "/" + f, encoding="utf-8").read()
    assert "watermet" not in txt.lower(), f
    json.loads(txt)
    print("ok:", f, len(txt), "bytes")
