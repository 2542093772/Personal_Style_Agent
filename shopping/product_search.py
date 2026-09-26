from datetime import datetime, timezone
from urllib.parse import quote
from ddgs import DDGS


MARKET_DOMAINS = {
    "jd": "jd.com",
    "tmall": "tmall.com",
    "taobao": "taobao.com",
    "dewu": "dewu.com",
}


def search_products(query, marketplace=None, max_results=10):
    search_query = query
    if marketplace in MARKET_DOMAINS:
        search_query += f" site:{MARKET_DOMAINS[marketplace]}"

    rows = []
    with DDGS() as ddgs:
        for item in ddgs.text(search_query, max_results=max_results):
            rows.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
                "marketplace": marketplace or "web",
                "captured_at": datetime.now(timezone.utc).isoformat(),
            })
    return rows


def build_marketplace_search_url(query, marketplace):
    encoded = quote(query)
    if marketplace == "jd":
        return f"https://search.jd.com/Search?keyword={encoded}"
    if marketplace == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"
    if marketplace == "tmall":
        return f"https://list.tmall.com/search_product.htm?q={encoded}"
    return ""
