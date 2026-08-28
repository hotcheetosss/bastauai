"""Оркестратор — связывает агентов через статусы CRM (без ручного вмешательства).

Событийная логика:
  QUALIFIED   -> запустить агента №2 (сборка сайта) -> SITE_READY (+site_url)
  SITE_READY  -> агент №1 отправляет клиенту ссылку -> SENT

Функцию advance()/run_pipeline() дёргает воркер-поллер или Supabase-webhook.
Идемпотентно: делает ровно один следующий автоматический шаг по статусу лида.
"""
from __future__ import annotations

from typing import Optional

from shared.db import append_message, get_lead, leads_by_status, set_status
from shared.models import LeadStatus

from agents.sales_agent.messenger import send_whatsapp
from agents.site_builder import build_site_for_lead

# Шаблон сообщения с готовой демо-ссылкой (тон правим позже под шаблоны пользователя)
SITE_READY_MESSAGE = (
    "Готово! 🙌 Подготовил для вас демо-версию сайта:\n{url}\n\n"
    "Посмотрите — как вам? Что бы поправили?"
)


def on_qualified(lead_id: str, *, deploy: bool = True) -> dict:
    """QUALIFIED -> собрать сайт (агент №2) -> SITE_READY."""
    return build_site_for_lead(lead_id, deploy=deploy)


def on_site_ready(lead_id: str) -> str:
    """SITE_READY -> отправить клиенту ссылку (агент №1) -> SENT."""
    lead = get_lead(lead_id)
    url = lead.get("site_url") or ""
    msg = SITE_READY_MESSAGE.format(url=url)
    send_whatsapp(lead["phone"], msg)
    append_message(lead_id, "agent", msg)
    set_status(lead_id, LeadStatus.SENT)
    return msg


def advance(lead_id: str, *, deploy: bool = True) -> Optional[str]:
    """Сделать один автоматический шаг по текущему статусу. Вернуть что сделал."""
    lead = get_lead(lead_id)
    if lead is None:
        return None
    status = lead["status"]
    if status == LeadStatus.QUALIFIED.value:
        on_qualified(lead_id, deploy=deploy)
        return "built"
    if status == LeadStatus.SITE_READY.value:
        on_site_ready(lead_id)
        return "sent"
    return None


def run_pipeline(lead_id: str, *, deploy: bool = True, max_steps: int = 4) -> list[str]:
    """Прокрутить все автошаги подряд: QUALIFIED -> SITE_READY -> SENT."""
    done: list[str] = []
    for _ in range(max_steps):
        step = advance(lead_id, deploy=deploy)
        if step is None:
            break
        done.append(step)
    return done


def poll_once(*, deploy: bool = True) -> dict[str, int]:
    """Один проход воркера: продвинуть все лиды, ждущие автошага.

    Продакшн-воркер вызывает это по кругу (или заменяется на Supabase-webhook).
    """
    counts = {"built": 0, "sent": 0}
    for status in (LeadStatus.QUALIFIED, LeadStatus.SITE_READY):
        for lead in leads_by_status(status):
            step = advance(lead["id"], deploy=deploy)
            if step in counts:
                counts[step] += 1
    return counts
