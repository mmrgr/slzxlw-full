import asyncio, os, sys
from playwright.async_api import async_playwright

CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"

PAPERS = {
    "05": {
        "file": "05_Li2025_CACM.pdf",
        "start": "https://dl.acm.org/doi/10.1145/3724499",
        "candidates": ["https://dl.acm.org/doi/pdf/10.1145/3724499?download=true",
                       "https://dl.acm.org/doi/pdf/10.1145/3724499"],
    },
    "08": {
        "file": "08_Privette2026_AGUAdv.pdf",
        "start": "https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025AV002140",
        "candidates": ["https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2025AV002140",
                       "https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2025AV002140"],
    },
    "01": {
        "file": "01_Wang2026_ESE.pdf",
        "start": "https://doi.org/10.1016/j.ese.2026.100702",
        "candidates": [],
    },
    "06": {
        "file": "06_Siddik2021_ERL.pdf",
        "start": "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1",
        "candidates": ["https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf",
                       "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/ampdf"],
    },
}

async def handle(pw, key, cfg, log):
    browser = await pw.chromium.launch(
        executable_path=CHROME, headless=True,
        args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage",
              "--disable-blink-features=AutomationControlled","--disable-infobars"],
    )
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
        viewport={"width":1366,"height":768}, locale="en-US", accept_downloads=True,
    )
    page = await ctx.new_page()
    dl_done = asyncio.Event()
    dl_path = {}
    async def on_download(download):
        try:
            dest = os.path.join(OUT, cfg["file"])
            await download.save_as(dest)
            dl_path["path"] = dest
            dl_done.set()
        except Exception as e:
            log.append(f"  save_as err: {e}")
            dl_done.set()
    page.on("download", on_download)
    got = False
    try:
        await page.goto(cfg["start"], wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)
        title = await page.title()
        log.append(f"=== {key} === start: {title[:50]}")
        # collect candidate pdf links
        hrefs = await page.eval_on_selector_all(
            "a", "els => els.map(a=>a.href).filter(h=>h && /pdf|epdf|download/i.test(h))")
        cands = list(cfg["candidates"]) + [h for h in hrefs if h not in cfg["candidates"]]
        log.append(f"  cands: {cands[:6]}")
        for url in cands[:8]:
            log.append(f"  -> {url}")
            dl_done.clear()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                # 'Download is starting' is expected for attachment downloads
                log.append(f"    goto note: {str(e)[:120]}")
            try:
                await asyncio.wait_for(dl_done.wait(), timeout=45)
                if os.path.exists(os.path.join(OUT, cfg["file"])):
                    sz = os.path.getsize(os.path.join(OUT, cfg["file"]))
                    if sz > 10000:
                        log.append(f"  OK {cfg['file']}: {sz} bytes")
                        got = True
                        break
            except asyncio.TimeoutError:
                log.append(f"    no download within 45s")
        # fallback: click download buttons
        if not got:
            for sel in ["text=Download PDF","text=Download article PDF","a#downloadPdf","[data-action='download']","text=PDF"]:
                try:
                    async with page.expect_download(timeout=8000) as dinfo:
                        await page.click(sel, timeout=5000)
                    d = await dinfo.value
                    await d.save_as(os.path.join(OUT, cfg["file"]))
                    got = True
                    log.append(f"  OK(click {sel}) {cfg['file']}")
                    break
                except Exception as e:
                    log.append(f"    click {sel}: {str(e)[:80]}")
    except Exception as e:
        log.append(f"ERROR {key}: {e}")
    finally:
        await browser.close()
    if not got:
        log.append(f"  >>> {key} NOT captured")

async def main():
    keys = sys.argv[1:] or list(PAPERS.keys())
    log = []
    async with async_playwright() as pw:
        for k in keys:
            if k not in PAPERS: continue
            await handle(pw, k, PAPERS[k], log)
    logname = "pw_cap3_" + "_".join(keys) + ".log"
    with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\\" + logname,"w",encoding="utf-8") as f:
        f.write("\n".join(log)+"\n")
    print("DONE")

asyncio.run(main())
