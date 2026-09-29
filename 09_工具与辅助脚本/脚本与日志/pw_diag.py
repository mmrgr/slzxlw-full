import asyncio, os
from playwright.async_api import async_playwright

CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"

ARTICLE = {
    "06": "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1",
    "08": "https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025AV002140",
}

async def diag(pw, key, url, log):
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
    responses = []
    def on_resp(r):
        resp = r.get("response") or {}
        responses.append((r["requestId"], resp.get("status"), resp.get("mimeType"), r.get("type"), resp.get("url","")))
    client.on("Network.responseReceived", on_resp)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000)
        title = await page.title()
        log.append(f"=== {key} === url={url}")
        log.append(f"TITLE={title}")
        # look for pdf links
        hrefs = await page.eval_on_selector_all("a", "els => els.map(a=>a.href).filter(h=>h && /pdf/i.test(h)).slice(0,10)")
        log.append(f"PDF_HREFS={hrefs}")
        # challenge markers
        txt = await page.evaluate("() => document.body ? document.body.innerText.slice(0,300) : ''")
        log.append(f"BODY_SNIPPET={txt!r}")
        log.append("RESPONSES:")
        for rid, st, mime, rtype, rurl in responses[:25]:
            log.append(f"  {st} {mime} {rtype} {rurl[:100]}")
    except Exception as e:
        log.append(f"ERROR {key}: {e}")
    finally:
        await browser.close()

async def main():
    keys = ["06","08"]
    log = []
    async with async_playwright() as pw:
        for k in keys:
            await diag(pw, k, ARTICLE[k], log)
    with open(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\pw_diag.log","w",encoding="utf-8") as f:
        f.write("\n".join(log)+"\n")
    print("DONE")

asyncio.run(main())
