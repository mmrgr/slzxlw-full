import asyncio, os, sys
from playwright.async_api import async_playwright

CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"
OUT = r"C:\Users\mmrgr\Desktop\论文9.15"

# fast attempt: short waits
PAPERS = {
    "01": {
        "file": "01_Wang2026_ESE.pdf",
        "start": "https://doi.org/10.1016/j.ese.2026.100702",
        "candidates": [],
    },
    "06": {
        "file": "06_Siddik2021_ERL.pdf",
        "start": "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1",
        "candidates": ["https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf"],
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
    async def on_download(d):
        try:
            await d.save_as(os.path.join(OUT, cfg["file"])); dl_done.set()
        except Exception as e:
            log.append(f"  save err {e}"); dl_done.set()
    page.on("download", on_download)
    got = False
    try:
        await page.goto(cfg["start"], wait_until="load", timeout=45000)
        # give Cloudflare/Radware a chance to resolve
        await page.wait_for_timeout(25000)
        title = await page.title()
        log.append(f"=== {key} === after wait title: {title[:60]}")
        hrefs = await page.eval_on_selector_all("a","els=>els.map(a=>a.href).filter(h=>h&&/pdf|epdf|download|pdfft/i.test(h))")
        cands = list(cfg["candidates"])+[h for h in hrefs if h not in cfg["candidates"]]
        log.append(f"  cands: {cands[:5]}")
        for url in cands[:4]:
            dl_done.clear()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                log.append(f"  goto note: {str(e)[:80]}")
            try:
                await asyncio.wait_for(dl_done.wait(), timeout=20)
                if os.path.exists(os.path.join(OUT,cfg["file"])) and os.path.getsize(os.path.join(OUT,cfg["file"]))>10000:
                    log.append(f"  OK {cfg['file']}"); got=True; break
            except asyncio.TimeoutError:
                log.append(f"  no dl for {url[-40:]}")
    except Exception as e:
        log.append(f"ERROR {key}: {e}")
    finally:
        await browser.close()
    if not got: log.append(f"  >>> {key} NOT captured")

async def main():
    keys = sys.argv[1:] or list(PAPERS.keys())
    log=[]
    async with async_playwright() as pw:
        for k in keys:
            if k in PAPERS: await handle(pw,k,PAPERS[k],log)
    with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\pw_cap5.log","w",encoding="utf-8") as f:
        f.write("\n".join(log)+"\n")
    print("DONE")

asyncio.run(main())
