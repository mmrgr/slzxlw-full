import asyncio, base64, os, sys
from playwright.async_api import async_playwright

CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"

# start_url = article page; candidates = ordered list of pdf urls to try
PAPERS = {
    "06": {
        "file": "06_Siddik2021_ERL.pdf",
        "start": "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1",
        "candidates": ["https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf",
                       "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/ampdf"],
    },
    "08": {
        "file": "08_Privette2026_AGUAdv.pdf",
        "start": "https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025AV002140",
        "candidates": ["https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2025AV002140",
                       "https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2025AV002140"],
    },
    "05": {
        "file": "05_Li2025_CACM.pdf",
        "start": "https://dl.acm.org/doi/10.1145/3724499",
        "candidates": ["https://dl.acm.org/doi/pdf/10.1145/3724499"],
    },
    "01": {
        "file": "01_Wang2026_ESE.pdf",
        "start": "https://doi.org/10.1016/j.ese.2026.100702",
        "candidates": [],  # will collect from page
    },
}

async def capture_pdf(page, client, log, seconds=50):
    pdf_requests = {}
    def on_resp(received):
        req_id = received["requestId"]
        mime = (received.get("response") or {}).get("mimeType", "")
        if "pdf" in mime.lower():
            pdf_requests[req_id] = True
    client.on("Network.responseReceived", on_resp)
    for _ in range(seconds):
        await page.wait_for_timeout(1000)
        if pdf_requests:
            break
    for req_id in list(pdf_requests.keys()):
        try:
            res = await client.send("Network.getResponseBody", {"requestId": req_id})
            body = base64.b64decode(res["body"])
            if body[:4] == b"%PDF":
                return body
            else:
                log.append(f"  req {req_id[:8]}: non-pdf ({len(body)} bytes)")
        except Exception as e:
            log.append(f"  getResponseBody err: {e}")
    return None

async def handle(pw, key, cfg, log):
    browser = await pw.chromium.launch(
        executable_path=CHROME, headless=True,
        args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage",
              "--disable-blink-features=AutomationControlled","--disable-infobars"],
    )
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
        viewport={"width":1366,"height":768}, locale="en-US",
    )
    page = await ctx.new_page()
    client = await ctx.new_cdp_session(page)
    await client.send("Network.enable")
    try:
        await page.goto(cfg["start"], wait_until="load", timeout=60000)
        await page.wait_for_timeout(4000)
        title = await page.title()
        log.append(f"=== {key} === start loaded: {title[:60]}")
        # collect pdf hrefs from page
        hrefs = await page.eval_on_selector_all(
            "a", "els => els.map(a=>a.href).filter(h=>h && /pdf|fulltext|download/i.test(h))")
        candidates = list(cfg["candidates"]) + [h for h in hrefs if h not in cfg["candidates"]]
        log.append(f"  candidates: {candidates[:6]}")
        for url in candidates[:6]:
            log.append(f"  trying: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                log.append(f"    goto err: {e}")
            body = await capture_pdf(page, client, log, seconds=40)
            if body:
                open(os.path.join(OUT, cfg["file"]), "wb").write(body)
                log.append(f"  OK {cfg['file']}: {len(body)} bytes")
                break
            else:
                log.append(f"    no pdf from this url")
    except Exception as e:
        log.append(f"ERROR {key}: {e}")
    finally:
        await browser.close()

async def main():
    keys = sys.argv[1:] or list(PAPERS.keys())
    log = []
    async with async_playwright() as pw:
        for k in keys:
            if k not in PAPERS: continue
            await handle(pw, k, PAPERS[k], log)
    logname = "pw_cap_" + "_".join(keys) + ".log"
    with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\\" + logname,"w",encoding="utf-8") as f:
        f.write("\n".join(log)+"\n")
    print("DONE")

asyncio.run(main())
