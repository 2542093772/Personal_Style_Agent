import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


CHINA_SUFFIXES = (
    "特别行政区", "自治区", "自治州", "地区", "盟",
    "省", "市", "区", "县", "旗",
)


def normalize_china_place(name: str) -> str:
    text = re.sub(r"\s+", "", (name or "").strip())
    text = text.replace("中国", "")
    return text


def _request_json(url: str, headers=None, timeout=15):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Personal-Style-Agent/2.2",
            "Accept": "application/json",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _nominatim(name: str) -> Optional[Dict[str, Any]]:
    q = urllib.parse.urlencode({
        "q": f"{name}, 中国",
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "zh-CN,zh,en",
        "countrycodes": "cn",
        "limit": 8,
    })
    rows = _request_json(f"https://nominatim.openstreetmap.org/search?{q}")
    if not rows:
        return None

    # Prefer administrative places over POIs when several matches exist.
    ranked = sorted(
        rows,
        key=lambda r: (
            0 if r.get("category") in {"boundary", "place"} else 1,
            0 if r.get("type") in {"city", "administrative", "county", "town", "village"} else 1,
            -float(r.get("importance") or 0),
        ),
    )
    row = ranked[0]
    addr = row.get("address") or {}

    city = (
        addr.get("city")
        or addr.get("municipality")
        or addr.get("prefecture")
        or addr.get("county")
        or addr.get("town")
        or addr.get("village")
    )
    province = addr.get("state") or addr.get("province")
    district = addr.get("district") or addr.get("city_district") or addr.get("county")

    display = city or district or row.get("name") or name
    return {
        "query": name,
        "default_location": display,
        "display_name": display,
        "admin1": province,
        "admin2": city,
        "district": district,
        "country": addr.get("country") or "中国",
        "country_code": (addr.get("country_code") or "cn").upper(),
        "latitude": float(row["lat"]),
        "longitude": float(row["lon"]),
        "provider": "nominatim",
        "raw_display_name": row.get("display_name"),
    }


def _open_meteo(name: str) -> Optional[Dict[str, Any]]:
    q = urllib.parse.urlencode({
        "name": name,
        "count": 10,
        "language": "zh",
        "format": "json",
    })
    data = _request_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}")
    rows = data.get("results") or []
    china = [
        r for r in rows
        if str(r.get("country_code") or "").upper() == "CN"
        or str(r.get("country") or "") in {"中国", "China"}
    ]
    row = (china or rows or [None])[0]
    if not row:
        return None

    return {
        "query": name,
        "default_location": row.get("name") or name,
        "display_name": row.get("name") or name,
        "admin1": row.get("admin1"),
        "admin2": row.get("admin2"),
        "district": row.get("admin3"),
        "country": row.get("country") or "中国",
        "country_code": row.get("country_code") or "CN",
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "provider": "open_meteo",
    }


def resolve_china_location(name: str) -> Optional[Dict[str, Any]]:
    name = normalize_china_place(name)
    if not name:
        return None

    # Nominatim handles Chinese province/city/district names especially well.
    try:
        result = _nominatim(name)
        if result:
            return result
    except Exception:
        pass

    # Fall back to Open-Meteo's geocoder.
    try:
        return _open_meteo(name)
    except Exception:
        return None
