#!/usr/bin/env python3
"""Amul High‑Protein Rose Lassi stock monitor

* Checks the product page each time the script runs.
* If the product becomes ``InStock`` a notification is sent to an ntfy.sh topic.
* Designed for execution via a scheduled job (cron, GitHub Actions, etc.).
"""

import sys
import re
import logging
from datetime import datetime
from urllib import request

# ------------------- configuration -------------------
PRODUCT_URL = "https://shop.amul.com/en/product/amul-high-protein-rose-lassi-200-ml-or-pack-of-30"
# The topic can be overridden via the NTFY_TOPIC environment variable (used by GitHub Actions).
NTFY_TOPIC = "amulStockCheck-7Incher"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
LOG_FILE = "stock_notifier.log"
# ----------------------------------------------------

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def fetch_page(url: str) -> str:
    """Download the page and return it as a UTF‑8 string."""
    req = request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
    })
    with request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def is_in_stock(html: str) -> bool:
    """Detect the ``InStock`` marker used by the Amul shop.
    The page contains a tag such as:
        <link itemprop="availability" href="https://schema.org/InStock">
    """
    match = re.search(r"<link\s+itemprop=[\"']availability[\"']\s+href=[\"']([^\"']+)[\"']", html, re.I)
    if not match:
        return False
    return "InStock" in match.group(1)

def send_ntfy(message: str) -> None:
    """POST a plain‑text message to the ntfy topic."""
    data = message.encode("utf-8")
    req = request.Request(
        NTFY_URL,
        data=data,
        method="POST",
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    with request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"ntfy responded with status {resp.status}")

def main() -> None:
    try:
        html = fetch_page(PRODUCT_URL)
        if is_in_stock(html):
            message = (
                "🥛 *Amul High‑Protein Rose Lassi* is back in stock!\n"
                f"🛒 Order now: {PRODUCT_URL}\n"
                f"📅 Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_ntfy(message)
            logging.info("Product IN STOCK – notification sent")
        else:
            logging.info("Product still out of stock")
    except Exception as e:
        logging.exception(f"Error while checking stock: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Allow the environment to override the hard‑coded topic (useful for CI).
    import os
    env_topic = os.getenv("NTFY_TOPIC")
    if env_topic:
        NTFY_TOPIC = env_topic
        NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
    main()
