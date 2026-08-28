"""Оркестратор агента №1: входящее сообщение -> решение -> запись в CRM.

process_incoming(phone, text) — единая точка входа (её дёрнет webhook GREEN-API).
Ответ агента возвращается строкой (её отправит слой WhatsApp).
"""
from __future__ import annotations

from typing import Any, Optional

from shared.db import append_message, get_lead, get_lead_by_phone, set_status, update_lead
from shared.models import LeadStatus

from .brain import decide
from .models import AgentDecision


def _merge_brief(current: dict[str, Any], upd) -> dict[str, Any]:
    """Слить новое, что узнал агент, в существующий бриф."""
    b = dict(current or {})
    data = upd.model_dump(exclude_none=True)
    # услуги — объединяем без дублей
    new_services = data.pop("services", None)
    if new_services:
        existing = list(b.get("services") or [])
        for s in new_services:
            if s not in existing:
                existing.append(s)
        b["services"] = existing
    # контакты — в под-объект
    for key in ("address", "hours"):
        if key in data:
            b.setdefault("contacts", {})[key] = data.pop(key)
    b.update(data)  # business_type, goal, style, agreed
    return b


def _apply_action(lead_id: str, current_status: str, action: str) -> None:
    # force=True: решение агента авторитетно; статусы не должны бросать исключение
    # и стопорить живой диалог (иначе воркер зациклится на одном сообщении).
    st = LeadStatus(current_status)
    if action == "qualified":
        if st != LeadStatus.IN_DIALOG:
            set_status(lead_id, LeadStatus.IN_DIALOG, force=True)
        set_status(lead_id, LeadStatus.QUALIFIED, force=True)   # → триггерит агента №2
    elif action == "lost":
        set_status(lead_id, LeadStatus.LOST, force=True)
    elif action == "revision":
        set_status(lead_id, LeadStatus.REVISION, force=True)
    elif action == "continue":
        if st in (LeadStatus.CONTACTED, LeadStatus.LOST):
            set_status(lead_id, LeadStatus.IN_DIALOG, force=True)
    # handoff — статус не трогаем, ниже отдельно уведомляем человека


def notify_human(lead: dict[str, Any], decision: AgentDecision) -> None:
    """Уведомить менеджера о хендоффе. Пока — лог; позже Telegram."""
    print(f"[HANDOFF] лид {lead.get('business_name')} ({lead.get('phone')}) "
          f"intent={decision.intent!r} — нужен человек.")


def process_incoming(phone: str, text: str) -> Optional[str]:
    """Обработать входящее WhatsApp-сообщение. Вернуть ответ агента (или None)."""
    lead = get_lead_by_phone(phone)
    if lead is None:
        # отправитель не из нашей базы лидов — игнорируем
        return None

    append_message(lead["id"], "client", text)
    lead = get_lead(lead["id"])  # свежая история

    decision = decide(
        business_name=lead["business_name"],
        incoming=text,
        status=lead["status"],
        category=lead.get("category"),
        city=lead.get("city"),
        phone=lead.get("phone"),
        brief=lead.get("brief") or {},
        conversation=lead.get("conversation") or [],
    )

    # 1) обновить бриф
    merged = _merge_brief(lead.get("brief") or {}, decision.brief)
    update_lead(lead["id"], {"brief": merged})

    # 2) применить действие/статус
    _apply_action(lead["id"], lead["status"], decision.action)
    if decision.action == "handoff":
        notify_human(lead, decision)

    # 3) сохранить ответ агента и вернуть его для отправки
    if decision.reply:
        append_message(lead["id"], "agent", decision.reply)
    return decision.reply
