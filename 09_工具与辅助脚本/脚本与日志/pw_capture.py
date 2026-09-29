import asyncio, base64, os, sys, json
from playwright.async_api import async_playwright

CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"

PAPERS = {
    "06": {
        "file": "06_Siddik2021_ERL.pdf",
        "url": "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf",
        "mode": "direct",
    },
    "05": {
        "file": "05_Li2025_CACM.pdf",
        "url": "https://dl.acm.org/doi/pdf/10.1145/3724499",
        "mode": "direct",
    },
    "08": {
        "file": "08_Privette2026_AGUAdv.pdf",
        "url": "https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2025AV002140",
        "mode": "direct",
    },
    "01": {
        "file": "01_Wang2026_ESE.pdf",
        "url": "https://www.sciencedirect.com/science/article/pii/S2666498426300702/pdf",
        "mode": "sd_direct",
    },
}

async def capture_pdf(page, client, log):
    pdf_requests = {}
    def on_resp(received):
        req_id = received["requestId"]
        mime = (received.get("response") or {}).get("mimeType", "")
        if "pdf" in mime.lower():
            pdf_requests[req_id] = True
    client.on("Network.responseReceived", on_resp)
    # poll for a pdf response up to 40s
    for _ in range(40):
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
                log.append(f"  req {req_id}: not pdf bytes ({len(body)})")
        except Exception as e:
            log.append(f"  getResponseBody err: {e}")
    return None

async def handle(pw, key, cfg, log):
    browser = await pw.chromium.launch(
        executable_path=CHROME,
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    )
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
    )
    page = await ctx.new_page()
    client = await ctx.new_cdp_session(page)
    await client.send("Network.enable")
    try:
        if cfg["mode"] == "direct":
            await page.goto(cfg["url"], wait_until="domcontentloaded", timeout=60000)
            body = await capture_pdf(page, client, log)
            if body:
                open(os.path.join(OUT, cfg["file"]), "wb").write(body)
                log.append(f"OK {cfg['file']}: {len(body)} bytes")
            else:
                log.append(f"FAIL no pdf captured for {key}")
        elif cfg["mode"] == "sd_direct":
            # try direct pii pdf; if fails, fall back to article page + click
            try:
                await page.goto(cfg["url"], wait_until="domcontentloaded", timeout=45000)
                body = await capture_pdf(page, client, log)
                if body:
                    open(os.path.join(OUT, cfg["file"]), "wb").write(body)
                    log.append(f"OK {cfg['file']}: {len(body)} bytes (sd_direct)")
                else:
                    raise RuntimeError("no pdf via sd_direct")
            except Exception as e:
                log.append(f"  sd_direct failed: {e}, trying article page")
                await page.goto("https://doi.org/10.1016/j.ese.2026.100702", wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(5000)
                # try to find and click download pdf
                for sel in ["text=Download PDF", "a#downloadPdf", "[data-action='download']", "text=Download full text"]:
                    try:
                        await page.click(sel, timeout=5000)
                        body = await capture_pdf(page, client, log)
                        if body:
                            open(os.path.join(OUT, cfg["file"]), "wb").write(body)
                            log.append(f"OK {cfg['file']}: {len(body)} bytes (sd_click)")
                            break
                    except Exception as e2:
                        log.append(f"  click {sel} failed: {e2}")
    except Exception as e:
        log.append(f"ERROR {key}: {e}")
    finally:
        await browser.close()

async def main():
    keys = sys.argv[1:] or list(PAPERS.keys())
    log = []
    async with async_playwright() as pw:
        for k in keys:
            if k not in PAPERS:
                continue
            log.append(f"=== {k} ===")
            await handle(pw, k, PAPERS[k], log)
    with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\pw_capture.log", "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print("DONE")

asyncio.run(main())
