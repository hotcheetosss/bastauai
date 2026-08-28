"""Агент №2 «Сайт-билдер»: бриф -> сайт -> деплой -> ссылка в CRM.

Точки входа:
- build_from_brief(business_name, brief)  — автономно, без CRM (для тестов).
- build_site_for_lead(lead_id)            — полный цикл через CRM.
"""
from __future__ import annotations

from typing import Any

from shared.db import get_lead, set_status
from shared.models import LeadStatus

from .deploy import deploy_to_netlify
from .generator import generate_site_html
from .prompt import build_site_prompt


def build_from_brief(
    business_name: str,
    brief: dict[str, Any],
    *,
    deploy: bool = True,
) -> dict[str, Any]:
    """Сгенерировать сайт по брифу. Если deploy=True — залить на Netlify.

    Возвращает {'site_prompt', 'html', 'site_url'|None}.
    """
    site_prompt = build_site_prompt(business_name, brief)
    html = generate_site_html(site_prompt)
    site_url = deploy_to_netlify(html, name=None) if deploy else None
    return {"site_prompt": site_prompt, "html": html, "site_url": site_url}


def build_site_for_lead(lead_id: str) -> dict[str, Any]:
    """Полный цикл через CRM: QUALIFIED -> BUILDING -> SITE_READY(+site_url)."""
    lead = get_lead(lead_id)
    if lead is None:
        raise ValueError(f"Лид не найден: {lead_id}")

    # помечаем, что начали строить
    set_status(lead_id, LeadStatus.BUILDING)

    try:
        result = build_from_brief(
            business_name=lead["business_name"],
            brief=lead.get("brief") or {},
            deploy=True,
        )
    except Exception:
        # откатываем статус, чтобы лид не завис в BUILDING
        set_status(lead_id, LeadStatus.QUALIFIED, force=True)
        raise

    set_status(
        lead_id,
        LeadStatus.SITE_READY,
        extra={
            "site_prompt": result["site_prompt"],
            "site_url": result["site_url"],
        },
    )
    return result
