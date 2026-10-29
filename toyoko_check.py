"""東橫INN 空房檢查（單次執行版，給 GitHub Actions 排程用）"""
import os
import sys
import urllib.request
from datetime import datetime

from playwright.sync_api import sync_playwright

URL = os.environ["TARGET_URL"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

SOLD_OUT_KEYWORDS = ["測試用"]
AVAILABLE_KEYWORDS = ["房態日曆"]


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def notify(title, message):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "urgent", "Click": URL},
    )
    urllib.request.urlopen(req, timeout=15)
    log("已送出通知")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="zh-TW", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        page.screenshot(path="debug.png", full_page=True)
        with open("debug.txt", "w", encoding="utf-8") as f:
            f.write(text)
        browser.close()

    if len(text.strip()) < 50 or not any(k in text for k in AVAILABLE_KEYWORDS):
        log("狀態：unknown（頁面可能被擋或未載入完整）")
        sys.exit(0)

    if any(k in text for k in SOLD_OUT_KEYWORDS):
        log("狀態：full")
        return

    log("狀態：available")
    notify("Toyoko Inn Available!", "2027/1/18 單人禁菸房可能釋出，請立刻確認並訂房。")


if __name__ == "__main__":
    main()
