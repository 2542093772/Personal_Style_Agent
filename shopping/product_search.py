import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from ddgs import DDGS


MARKET_DOMAINS = {
    "taobao": "taobao.com",
    "pinduoduo": "yangkeduo.com",
}


def is_concrete_product_url(url: str, marketplace: str | None = None) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()
    except Exception:
        return False

    if marketplace == "taobao":
        return (
            ("item.taobao.com" in host and "item.htm" in path and "id=" in query)
            or ("detail.tmall.com" in host and "item.htm" in path and "id=" in query)
        )

    if marketplace == "pinduoduo":
        return (
            "yangkeduo.com" in host
            and (
                ("goods.html" in path and "goods_id=" in query)
                or ("/goods" in path and "goods_id=" in query)
            )
        )

    return (
        is_concrete_product_url(url, "taobao")
        or is_concrete_product_url(url, "pinduoduo")
    )


def _extract_price(text: str):
    if not text:
        return None
    patterns = [
        r"[¥￥]\s*(\d+(?:\.\d{1,2})?)",
        r"(\d+(?:\.\d{1,2})?)\s*元",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def search_products(query, marketplace=None, max_results=12):
    domain = MARKET_DOMAINS.get(marketplace)
    search_query = query
    if domain:
        search_query += f" site:{domain}"

    rows = []
    with DDGS() as ddgs:
        for item in ddgs.text(search_query, max_results=max_results):
            url = item.get("href", "")
            if marketplace and not is_concrete_product_url(url, marketplace):
                continue

            title = item.get("title", "")
            snippet = item.get("body", "")
            rows.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "marketplace": marketplace or "web",
                "price_seen": _extract_price(f"{title} {snippet}"),
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "concrete_product": True,
            })
    return rows
