"""Генератор сайта: бриф -> контент (Gemini) -> рендер в НАШ шаблон -> HTML.

Дизайн зафиксирован в templates/base.html.j2 (наш «почерк»). ИИ отдаёт только
контент и выбор темы/акцента — слоп невозможен.

Публичная функция: generate_site_html(business_name, brief, city=None) -> html
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .content import SiteContent, extract_content
from .icons import get_icon

_TPL_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TPL_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)

_TONES = ["t-blue", "t-green", "t-amber", "t-pink", "t-violet"]
_BURGER = ('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
           'stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _valid_hex(c: str, default: str = "#4f6ef7") -> str:
    c = (c or "").strip()
    return c if re.fullmatch(r"#[0-9a-fA-F]{6}", c) else default


def _build_context(business_name: str, brief: dict[str, Any], content: SiteContent, city: str | None) -> dict[str, Any]:
    contacts = (brief or {}).get("contacts") or {}
    wa_raw = contacts.get("whatsapp") or contacts.get("phone") or ""
    wa_digits = _digits(wa_raw)
    phone_display = contacts.get("phone") or (("+" + wa_digits) if wa_digits else "")

    # услуги: иконки + чередование пастельных тонов
    services = []
    for i, s in enumerate(content.services):
        services.append({
            "icon": get_icon(s.icon),
            "name": s.name,
            "description": s.description,
            "price": s.price,
            "tone": _TONES[i % len(_TONES)],
        })

    # отзывы: звёзды + инициал
    reviews = [{
        "stars": "★★★★★",
        "text": r.text,
        "author": r.author,
        "subtitle": r.subtitle,
        "initial": (r.author or "?")[:1].upper(),
    } for r in content.reviews]

    # хлебные крошки-пилюли в hero (без выдуманного рейтинга)
    pills = []
    if content.stats:
        pills.append({"icon": get_icon("star"), "text": f"{content.stats[0].num} — {content.stats[0].label}"})
    if contacts.get("hours"):
        pills.append({"icon": get_icon("clock"), "text": contacts["hours"]})
    if contacts.get("address"):
        pills.append({"icon": get_icon("pin"), "text": contacts["address"]})

    logo_key = content.services[0].icon if content.services else "spark"

    return {
        "business_name": business_name,
        "city": city or "",
        "theme": content.theme if content.theme in ("light", "dark") else "light",
        "accent": _valid_hex(content.accent),
        "eyebrow": content.eyebrow,
        "hero_title_prefix": content.hero_title_prefix,
        "hero_title_accent": content.hero_title_accent,
        "hero_subtitle": content.hero_subtitle,
        "services_title": content.services_title,
        "services_subtitle": content.services_subtitle,
        "services": services,
        "stats": [{"num": s.num, "label": s.label} for s in content.stats],
        "about_title": content.about_title,
        "about_text": content.about_text,
        "reviews_title": content.reviews_title,
        "reviews": reviews,
        "cta_title": content.cta_title,
        "cta_text": content.cta_text,
        "footer_tagline": content.footer_tagline,
        # контакты
        "wa_link": f"https://wa.me/{wa_digits}" if wa_digits else "#contacts",
        "wa_display": ("+" + wa_digits) if wa_digits else "",
        "phone": phone_display,
        "address": contacts.get("address", ""),
        "hours": contacts.get("hours", ""),
        # иконки/служебное
        "logo_icon": get_icon(logo_key),
        "burger_icon": _BURGER,
        "wa_icon": get_icon("whatsapp"),
        "pin_icon": get_icon("pin"),
        "clock_icon": get_icon("clock"),
        "year": datetime.date.today().year,
    }


def render_site(business_name: str, brief: dict[str, Any], content: SiteContent, city: str | None = None) -> str:
    ctx = _build_context(business_name, brief, content, city)
    return _env.get_template("base.html.j2").render(**ctx)


def generate_site_html(business_name: str, brief: dict[str, Any], *, city: str | None = None) -> str:
    """Полный путь: бриф -> контент (Gemini) -> рендер нашего шаблона -> HTML."""
    content = extract_content(business_name, brief)
    return render_site(business_name, brief, content, city=city)
