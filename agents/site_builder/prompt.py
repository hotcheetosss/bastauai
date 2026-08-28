"""Превращение брифа (сырых данных о бизнесе) в чёткое ТЗ на сайт.

Пока делаем детерминированно на Python (без лишнего вызова Claude) — дёшево
и предсказуемо. Позже при желании можно заменить на «умный» переводчик через Claude.
"""
from __future__ import annotations

from typing import Any


def build_site_prompt(business_name: str, brief: dict[str, Any]) -> str:
    """Собрать текстовое ТЗ на сайт из названия бизнеса и брифа.

    brief — поля из shared.models.Brief (business_type, goal, pages, style,
    services, contacts).
    """
    b = brief or {}
    lines: list[str] = []
    lines.append(f"Название бизнеса: {business_name}")

    if b.get("business_type"):
        lines.append(f"Сфера/тип бизнеса: {b['business_type']}")
    if b.get("goal"):
        lines.append(f"Главная цель сайта: {b['goal']}")

    services = b.get("services") or []
    if services:
        lines.append("Услуги/товары: " + ", ".join(map(str, services)))

    pages = b.get("pages") or ["главная"]
    lines.append("Нужные блоки/разделы: " + ", ".join(map(str, pages)))

    if b.get("style"):
        lines.append(f"Пожелания по стилю/дизайну: {b['style']}")

    contacts = b.get("contacts") or {}
    if contacts:
        parts = [f"{k}: {v}" for k, v in contacts.items() if v]
        if parts:
            lines.append("Контакты: " + "; ".join(parts))

    return "\n".join(lines)
