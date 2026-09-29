import os, json, time, urllib.parse, urllib.request, ssl, re

OUTDIR = r"C:\Users\mmrgr\Desktop\论文9.15补充"
os.makedirs(OUTDIR, exist_ok=True)

EMAIL = "reader@openaccess.org"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
CTX = ssl.create_default_context()

# number | first_author | year | journal_short | doi | filename
PAPERS = [
    (1, "Xiao", 2025, "NatSustain", "10.1038/s41893-025-01681-y", "01_Xiao2025_NatSustain.pdf"),
    (2, "Masanet", 2020, "Science", "10.1126/science.aba3758", "02_Masanet2020_Science.pdf"),
    (3, "de Vries", 2023, "Joule", "10.1016/j.joule.2023.09.004", "03_deVries2023_Joule.pdf"),
    (4, "Ebrahimi", 2014, "RSER", "10.1016/j.rser.2013.12.007", "04_Ebrahimi2014_RSER.pdf"),
    (5, "Zhang", 2014, "RSER", "10.1016/j.rser.2014.04.017", "05_Zhang2014_RSER.pdf"),
    (6, "Chen", 2022, "FrontEnergy", "10.3389/fenrg.2022.952680", "06_Chen2022_FrontEnergy.pdf"),
    (7, "Kenway", 2011, "WST", "10.2166/wst.2011.070", "07_Kenway2011_WST.pdf"),
    (8, "Urich", 2014, "WST", "10.2166/wst.2014.363", "08_Urich2014_WST.pdf"),
    (9, "Cai", 2025, "EcolModel", "10.1016/j.ecolmodel.2024.110972", "09_Cai2025_EcolModel.pdf"),
    (10, "Voskamp", 2020, "JCLP", "10.1016/j.jclepro.2020.120310", "10_Voskamp2020_JCLP.pdf"),
    (11, "Nezami", 2022, "SustCitiesSoc", "10.1016/j.scs.2022.104065", "11_Nezami2022_SCS.pdf"),
    (12, "Hsieh", 2010, "EST", "10.1021/es101379r", "12_Hsieh2010_EST.pdf"),
    (13, "Walker", 2012, "WaterRes", "10.1016/j.watres.2012.04.015", "13_Walker2012_WaterRes.pdf"),
    (14, "Wang", 2020, "JCLP", "10.1016/j.jclepro.2020.120789", "14_Wang2020_JCLP.pdf"),
    (15, "Vakilifard", 2019, "ApplEnergy", "10.1016/j.apenergy.2018.10.128", "15_Vakilifard2019_ApplEnergy.pdf"),
    (16, "Qin", 2016, "Water", "10.3390/w8040157", "16_Qin2016_Water.pdf"),
    (17, "Wang", 2021, "EcolIndic", "10.1016/j.ecolind.2020.107232", "17_Wang2021_EcolIndic.pdf"),
    (18, "Blokker", 2010, "JWRPM", "10.1061/(ASCE)WR.1943-5452.0000002", "18_Blokker2010_JWRPM.pdf"),
    (19, "Haasnoot", 2013, "GlobEnvChange", "10.1016/j.gloenvcha.2012.12.006", "19_Haasnoot2013_GEC.pdf"),
    (20, "Mortazavi-Naeini", 2015, "EnvModSoft", "10.1016/j.envsoft.2015.02.021", "20_Mortazavi2015_EnvModSoft.pdf"),
]

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def verify_crossref(doi):
    try:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        d = get_json(url)
        m = d.get("message", {})
        title = (m.get("title") or [""])[0]
        authors = m.get("author", [])
        first = (authors[0].get("family") or authors[0].get("name") or "") if authors else ""
        issued = m.get("issued", {}).get("date-parts", [[""]])[0]
        year = str(issued[0]) if issued and issued[0] else ""
        container = (m.get("container-title") or [""])[0]
        return {"ok": True, "title": title, "first_author": first, "year": year, "journal": container}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def unpaywall(doi):
    try:
        url = "https://api.unpaywall.org/v2/%s?email=%s" % (urllib.parse.quote(doi, safe=""), EMAIL)
        d = get_json(url)
        status = d.get("oa_status")
        loc = d.get("best_oa_location") or {}
        pdf = loc.get("pdf_url") or ""
        # fallback: scan all oa_locations
        if not pdf:
            for ol in (d.get("oa_locations") or []):
                if ol.get("pdf_url"):
                    pdf = ol["pdf_url"]; break
        return {"status": status, "pdf": pdf}
    except Exception as e:
        return {"status": "err", "pdf": "", "error": str(e)}

def try_download(pdf_url, dest):
    if not pdf_url:
        return False, "no-url"
    try:
        req = urllib.request.Request(pdf_url, headers={
            "User-Agent": UA, "Accept": "application/pdf,*/*", "Referer": pdf_url})
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            data = r.read()
        if data[:4] == b"%PDF" and len(data) > 5000:
            open(dest, "wb").write(data)
            return True, "ok-%d" % len(data)
        return False, "not-pdf-%d" % len(data)
    except Exception as e:
        return False, "err-%s" % str(e)[:80]

results = []
for num, author, year, jshort, doi, fname in PAPERS:
    row = {"num": num, "author": author, "year": year, "jshort": jshort, "doi": doi, "file": fname}
    cr = verify_crossref(doi)
    row["crossref"] = cr
    if cr.get("ok"):
        # match checks
        tmatch = norm(cr["title"]) and (norm(author.split()[-1]) in norm(cr["title"]) or norm(cr["title"])[:20] in norm(author) or True)
        amatch = norm(author.split()[-1]) in norm(cr["first_author"]) or norm(cr["first_author"]) in norm(author.split()[-1])
        ymatch = str(year) == str(cr["year"])
        row["verified"] = amatch and ymatch
        row["verified_detail"] = {"author_match": amatch, "year_match": ymatch, "crossref_title": cr["title"], "crossref_author": cr["first_author"], "crossref_year": cr["year"]}
    else:
        row["verified"] = False
    # OA download
    up = unpaywall(doi)
    row["oa"] = up
    dest = os.path.join(OUTDIR, fname)
    if up.get("pdf"):
        ok, msg = try_download(up["pdf"], dest)
        row["downloaded"] = ok
        row["dl_msg"] = msg
    else:
        row["downloaded"] = False
        row["dl_msg"] = "no-oa-url"
    results.append(row)
    print("DONE %02d %s verified=%s oa=%s dl=%s" % (num, fname, row["verified"], up.get("status"), row["downloaded"]), flush=True)
    time.sleep(0.3)

with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\batch2_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# text report
lines = []
lines.append("=== 核验 + 下载报告 ===")
for r in results:
    lines.append("%02d | %s | 真实:%s | OA:%s | 下载:%s | %s" % (
        r["num"], r["file"], r["verified"],
        r["oa"].get("status"), r["downloaded"], r["dl_msg"]))
lines.append("\n=== 未能下载（需机构权限/机器人墙）===")
for r in results:
    if not r["downloaded"]:
        cr = r["crossref"]
        lines.append("%02d. %s et al. (%s) — DOI %s  [%s]" % (
            r["num"], r["author"], r["year"], r["doi"], r["jshort"]))
with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\batch2_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ALL_DONE")
