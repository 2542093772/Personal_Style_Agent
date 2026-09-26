import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str, default):
    p = ROOT / path
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _button(label: str, url: str) -> str:
    if not url:
        return ""
    return f'<a class="btn" href="{_esc(url)}" target="_blank">{_esc(label)}</a>'


def render_daily_html(plan: Dict[str, Any], survey: Dict[str, Any] | None = None) -> str:
    survey = survey or {}
    outfit = plan.get("outfit_plan", {}) or {}
    internet = outfit.get("internet_recommendation", []) or []
    wardrobe = outfit.get("wardrobe_recommendation", {}) or {}
    purchase = (plan.get("optional_purchase_gap", {}) or {}).get("items", []) or []
    rules = (plan.get("personal_baseline", {}) or {}).get("top_visual_rules", []) or []
    ctx = plan.get("today_context", {}) or {}
    today = datetime.now().strftime("%Y-%m-%d")

    cards = []

    # Internet outfit
    rows = []
    for item in internet[:4]:
        rows.append(
            f"<div class='item'><b>{_esc(item.get('title') or '穿搭建议')}</b>"
            + (f"<div>组合：{_esc(' + '.join(item.get('formula') or []))}</div>" if item.get("formula") else "")
            + (f"<div class='muted'>原因：{_esc(item.get('reason'))}</div>" if item.get("reason") else "")
            + "</div>"
        )
    cards.append("<section><h2>今日建议穿搭</h2>" + ("".join(rows) if rows else "<p class='muted'>今日暂无足够学习信号。</p>") + "</section>")

    # Wardrobe
    witems = wardrobe.get("items", []) or []
    if witems:
        body = "".join(f"<div class='item'>{_esc(x.get('category'))}：<b>{_esc(x.get('name'))}</b></div>" for x in witems)
    else:
        body = f"<p class='muted'>{_esc(wardrobe.get('reason') or '衣柜数据暂不足。')}</p>"
    cards.append("<section><h2>现有衣柜可穿方案</h2>" + body + "</section>")

    # Purchase
    purchase_html = []
    for item in purchase[:4]:
        candidates = item.get("live_candidates", []) or []
        candidate_html = []
        for cand in candidates[:4]:
            platform = "淘宝" if cand.get("marketplace") == "taobao" else "拼多多"
            price = cand.get("price_seen")
            price_text = f" · 抓取价约 ¥{_esc(price)}" if price else ""
            candidate_html.append(
                "<div class='product'>"
                f"<div><b>{_esc(platform)}｜{_esc(cand.get('title') or '商品候选')}</b>{price_text}</div>"
                f"<div class='muted'>抓取时间：{_esc(cand.get('captured_at'))}</div>"
                f"<div class='buttons'>{_button('打开具体商品', cand.get('url') or '')}</div>"
                "</div>"
            )
        if not candidate_html:
            candidate_html.append("<p class='muted'>本轮未抓到可靠的淘宝/拼多多具体商品详情页，因此不展示泛搜索链接。</p>")
        purchase_html.append(
            "<div class='item'>"
            f"<div class='tag'>{_esc(item.get('priority'))}</div>"
            f"<h3>{_esc(item.get('item'))}</h3>"
            f"<p>{_esc(item.get('why'))}</p>"
            f"<p class='muted'>预计可覆盖约 {_esc(item.get('estimated_outfits'))} 套搭配</p>"
            + "".join(candidate_html)
            + "</div>"
        )
    cards.append("<section><h2>采购建议</h2>" + ("".join(purchase_html) if purchase_html else "<p class='muted'>当前暂无核心采购缺口。</p>") + "</section>")

    # Learning
    learn_rows = []
    for src in (survey.get("sources", []) or [])[:8]:
        title = src.get("title") or "未命名来源"
        url = src.get("url") or ""
        learn_rows.append(
            "<div class='item'>"
            + (f"<a href='{_esc(url)}' target='_blank'><b>{_esc(title)}</b></a>" if url else f"<b>{_esc(title)}</b>")
            + (f"<div class='muted'>{_esc(src.get('snippet'))}</div>" if src.get("snippet") else "")
            + "</div>"
        )
    cards.append(
        "<section><h2>学习调查</h2>"
        f"<p>检索主题：{_esc(survey.get('query_count', 0))} ｜ 有效来源：{_esc(survey.get('source_count', 0))} ｜ 候选规则：{_esc(len(survey.get('candidate_rules', []) or []))}</p>"
        + ("".join(learn_rows) if learn_rows else "<p class='muted'>今天还没有学习调查数据。</p>")
        + "</section>"
    )

    # Rules
    rule_html = "".join(f"<li>{_esc(r.get('title'))}</li>" for r in rules[:6]) or "<li>暂无稳定个人规则</li>"
    cards.append(f"<section><h2>个人规则</h2><ul>{rule_html}</ul></section>")

    weather = _esc(ctx.get("weather_summary") or "天气暂不可用")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>今日穿搭与学习报告 - {today}</title>
<style>
body{{margin:0;background:#f4f5f7;color:#171717;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.65}}
.wrap{{max-width:860px;margin:0 auto;padding:24px 16px 56px}}
.hero{{padding:30px;border-radius:20px;background:#111827;color:#fff;margin-bottom:18px}}
.hero h1{{margin:0 0 8px;font-size:30px}} .hero p{{margin:4px 0;color:#d1d5db}}
section{{background:#fff;border-radius:18px;padding:22px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
h2{{margin-top:0}} .item{{padding:14px 0;border-bottom:1px solid #eee}} .item:last-child{{border-bottom:0}}
.muted{{color:#6b7280;font-size:14px}} .tag{{display:inline-block;padding:2px 8px;border-radius:999px;background:#eef2ff;font-size:12px}}
.product{padding:12px 0;border-top:1px dashed #e5e7eb}.buttons{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}} .btn{{text-decoration:none;background:#111827;color:white;padding:8px 12px;border-radius:10px}}
a{{color:#2563eb}}
</style>
</head>
<body><div class="wrap">
<div class="hero"><h1>今日穿搭与学习报告</h1><p>{today}</p><p>天气：{weather}</p></div>
{''.join(cards)}
</div></body></html>"""


def build_today_report_file(plan: Dict[str, Any], survey: Dict[str, Any] | None = None, out_path: str | None = None) -> str:
    out = Path(out_path) if out_path else ROOT / "reports" / "daily_style_report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_daily_html(plan, survey), encoding="utf-8")
    return str(out)
