import os
import re
import logging
from logging.handlers import RotatingFileHandler
from typing import Iterable, List, Set

import requests
from bs4 import BeautifulSoup

DEFAULT_URLS = [
    "https://api.uouin.com/cloudflare.html",
    "https://ip.164746.xyz",
]

IP_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def _get_env_urls() -> List[str]:
    raw = os.getenv("CF_URLS", "").strip()
    if not raw:
        return DEFAULT_URLS.copy()
    return [x.strip() for x in raw.split(",") if x.strip()]


def init_logger() -> logging.Logger:
    logger = logging.getLogger("collect_ips")
    desired_path = os.getenv("CF_AUDIT_LOG", "audit.log")
    desired_path = desired_path if desired_path is not None else "audit.log"

    # Determine if reconfiguration is needed
    need_reconfig = True
    current_file_handler = None
    if logger.handlers:
        need_reconfig = False
        for h in list(logger.handlers):
            if isinstance(h, RotatingFileHandler):
                current_file_handler = h
                current = getattr(h, "baseFilename", None)
                # If desired path is empty (disable) or different file, reconfigure
                if (not desired_path) or (current and desired_path and os.path.abspath(current) != os.path.abspath(desired_path)):
                    need_reconfig = True
        # If no file handler exists but we desire one, reconfigure
        if not current_file_handler and desired_path:
            need_reconfig = True

    if not need_reconfig:
        return logger

    # Reconfigure
    for h in list(logger.handlers):
        logger.removeHandler(h)
    logger.setLevel(logging.INFO)

    # file handler (optional)
    if desired_path:
        os.makedirs(os.path.dirname(desired_path) or ".", exist_ok=True)
        file_handler = RotatingFileHandler(desired_path, maxBytes=512_000, backupCount=3)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(file_handler)

    # stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(stream_handler)

    logger.propagate = False
    return logger


def fetch_html(url: str) -> str:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_ips_from_html(html: str) -> List[str]:
    # Generic parsing: search visible text for IPs to be robust across layouts
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")
    ips = []
    seen: Set[str] = set()
    for m in IP_PATTERN.finditer(text):
        ip = m.group(0)
        if ip not in seen:
            seen.add(ip)
            ips.append(ip)
    return ips


def collect_ips(urls: Iterable[str]) -> List[str]:
    logger = init_logger()
    all_ips: List[str] = []
    seen: Set[str] = set()

    logger.info("start collection: %d url(s)", len(list(urls)))
    for url in urls:
        try:
            logger.info("fetch %s", url)
            html = fetch_html(url)
            ips = parse_ips_from_html(html)
            logger.info("parsed %d ips from %s", len(ips), url)
            for ip in ips:
                if ip not in seen:
                    seen.add(ip)
                    all_ips.append(ip)
        except Exception as e:  # noqa: BLE001 - log and continue
            logger.error("error fetching %s: %s", url, e)
    logger.info("collection done: %d unique ips", len(all_ips))
    return all_ips


def _atomic_write(path: str, content: str) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, path)


def write_ips_file(path: str, ips: Iterable[str]) -> None:
    logger = init_logger()
    ips_list = list(ips)
    _atomic_write(path, "\n".join(ips_list) + "\n")
    logger.info("wrote %d ips to %s", len(ips_list), path)


def main() -> None:
    logger = init_logger()
    urls = _get_env_urls()
    logger.info("using %d urls", len(urls))
    ips = collect_ips(urls)
    write_ips_file("ip.txt", ips)
    print("IP地址已保存到ip.txt文件中。")


if __name__ == "__main__":
    main()
