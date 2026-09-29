import subprocess, sys, os, time

AB = r"C:\Users\mmrgr\.workbuddy\binaries\node\versions\22.22.2-3\agent-browser.ps1"
CHROME = r"C:\Users\mmrgr\.agent-browser\browsers\chrome-153.0.8010.36\chrome.exe"
DOWNLOAD_DIR = r"C:\Users\mmrgr\Desktop\论文9.15"
LOG = r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\ab_run.log"

def run(args, timeout=120):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", AB] + args
    line = "RUN: " + " ".join(args)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "AGENT_BROWSER_EXECUTABLE_PATH": CHROME})
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("RC=" + str(p.returncode) + "\n")
            f.write("OUT=" + (p.stdout or "")[:2000] + "\n")
            f.write("ERR=" + (p.stderr or "")[:2000] + "\n")
        return p
    except subprocess.TimeoutExpired as e:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("TIMEOUT after " + str(timeout) + "s\n")
        return None

if __name__ == "__main__":
    open(LOG, "w", encoding="utf-8").write("=== START ===\n")
    # ensure clean
    run(["close", "--all"], timeout=20)
    paper = sys.argv[1] if len(sys.argv) > 1 else "06"
    urls = {
        "06": ("06_Siddik2021_ERL.pdf", "https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf"),
        "05": ("05_Li2025_CACM.pdf", "https://dl.acm.org/doi/pdf/10.1145/3724499"),
        "08": ("08_Privette2026_AGUAdv.pdf", "https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2025AV002140"),
    }
    fname, url = urls[paper]
    # launch with no-sandbox chrome args
    run(["--download-path", DOWNLOAD_DIR, "--args", "--no-sandbox,--disable-setuid-sandbox,--disable-dev-shm-usage",
         "open", url], timeout=90)
    time.sleep(3)
    run(["wait", "4000"], timeout=30)
    run(["get", "url"], timeout=30)
    # try pdf save (works for inline-rendered PDFs)
    run(["pdf", os.path.join(DOWNLOAD_DIR, fname)], timeout=90)
    run(["close"], timeout=20)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("=== END ===\n")
    print("done")
