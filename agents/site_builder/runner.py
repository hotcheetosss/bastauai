"""Агент №2 «Сайт-билдер»: бриф -> сайт -> деплой -> ссылка в CRM.

Точки входа:
- build_from_brief(business_name, brief)  — автономно, без CRM (для тестов).
- build_site_for_lead(lead_id)            — полный цикл через CRM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.db import get_lead, set_status
from shared.models import LeadStatus

from .deploy import deploy_to_netlify
from .generator import generate_site_html

_OUTPUT = Path(__file__).resolve().parent / "output"


def build_from_brief(
    business_name: str,
    brief: dict[str, Any],
    *,
    city: str | None = None,
    deploy: bool = True,
) -> dict[str, Any]:
    """Сгенерировать сайт по брифу. Если deploy=True — залить на Netlify.

    Возвращает {'html', 'site_url'|None}.
    """
    html = generate_site_html(business_name, brief, city=city)
    site_url = deploy_to_netlify(html, name=None) if deploy else None
    return {"html": html, "site_url": site_url}


def build_site_for_lead(lead_id: str, *, deploy: bool = True) -> dict[str, Any]:
    """Полный цикл через CRM: QUALIFIED -> BUILDING -> SITE_READY(+site_url).

    deploy=False — без Netlify (бережём кредиты): сайт сохраняется локально,
    site_url указывает на файл. Для тестов конвейера.
    """
    lead = get_lead(lead_id)
    if lead is None:
        raise ValueError(f"Лид не найден: {lead_id}")

    prev_status = lead["status"]  # QUALIFIED (первая сборка) или REVISION (пересборка)
    set_status(lead_id, LeadStatus.BUILDING, force=True)
    try:
        result = build_from_brief(
            business_name=lead["business_name"],
            brief=lead.get("brief") or {},
            city=lead.get("city"),
            deploy=deploy,
        )
    except Exception:
        set_status(lead_id, LeadStatus(prev_status), force=True)  # не зависаем в BUILDING
        raise

    site_url = result["site_url"]
    if site_url is None:  # без деплоя — сохраняем локально
        _OUTPUT.mkdir(parents=True, exist_ok=True)
        f = _OUTPUT / f"lead_{lead_id[:8]}.html"
        f.write_text(result["html"], encoding="utf-8")
        site_url = f.resolve().as_uri()

    set_status(lead_id, LeadStatus.SITE_READY, extra={"site_url": site_url})
    result["site_url"] = site_url
    return result
