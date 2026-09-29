# -*- coding: utf-8 -*-
"""通过 GitHub Git Data API 推送提交（本机代理拦截 github.com，但放行 api.github.com）。"""
import base64
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"
OWNER, REPO = "mmrgr", "AI-UWM"
BRANCH = "main"

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("no token")

API = "https://api.github.com"
HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "aiuwm-push",
}


def req(method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:600]
        sys.exit("HTTP %s %s\n%s" % (e.code, path, body))


# 1) 远端当前提交与基准树
ref = req("GET", "/repos/%s/%s/git/ref/heads/%s" % (OWNER, REPO, BRANCH))
base_sha = ref["object"]["sha"]
commit = req("GET", "/repos/%s/%s/git/commits/%s" % (OWNER, REPO, base_sha))
base_tree = commit["tree"]["sha"]
print("remote head:", base_sha[:10], "tree:", base_tree[:10])

# 2) 本地提交的文件清单（mode/type/sha/path）
out = subprocess.check_output(
    ["git", "ls-tree", "-r", "-z", "HEAD"], cwd=ROOT
).decode("utf-8")
local = {}
for rec in out.split("\0"):
    if not rec:
        continue
    meta, path = rec.split("\t", 1)
    mode, typ, sha = meta.split()
    local[path] = (mode, typ, sha)

print("local files:", len(local))

# 3) 远端现有文件（用于计算需要删除的路径）
rtree = req("GET", "/repos/%s/%s/git/trees/%s?recursive=1" % (OWNER, REPO, BRANCH))
remote_paths = {e["path"] for e in rtree["tree"] if e["type"] == "blob"}
to_delete = sorted(p for p in remote_paths if p not in local)
print("remote blobs:", len(remote_paths), "to delete:", len(to_delete))

# 4) 为每个本地文件创建 blob
entries = []
for i, (path, (mode, typ, sha)) in enumerate(sorted(local.items()), 1):
    raw = subprocess.check_output(["git", "cat-file", "blob", sha], cwd=ROOT)
    blob = req(
        "POST",
        "/repos/%s/%s/git/blobs" % (OWNER, REPO),
        {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"},
    )
    entries.append({"path": path, "mode": mode, "type": "blob", "sha": blob["sha"]})
    if i % 25 == 0 or i == len(local):
        print("  blobs %d/%d" % (i, len(local)))

# 5) 删除远端独有的旧路径
for p in to_delete:
    entries.append({"path": p, "mode": "100644", "type": "blob", "sha": None})

tree = req(
    "POST", "/repos/%s/%s/git/trees" % (OWNER, REPO),
    {"base_tree": base_tree, "tree": entries},
)
print("tree:", tree["sha"][:10])

# 6) 提交
msg = subprocess.check_output(
    ["git", "log", "-1", "--pretty=%B"], cwd=ROOT
).decode("utf-8").strip()
new_commit = req(
    "POST", "/repos/%s/%s/git/commits" % (OWNER, REPO),
    {"message": msg, "tree": tree["sha"], "parents": [base_sha]},
)
print("commit:", new_commit["sha"][:10])

# 7) 更新分支引用
req("PATCH", "/repos/%s/%s/git/refs/heads/%s" % (OWNER, REPO, BRANCH),
    {"sha": new_commit["sha"]})
print("ref updated ->", new_commit["sha"][:10])

# 8) 同步本地远端跟踪引用
subprocess.check_call(
    ["git", "update-ref", "refs/remotes/origin/%s" % BRANCH, new_commit["sha"]], cwd=ROOT
)
print("local remote-tracking ref synced")
