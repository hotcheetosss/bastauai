"""Клиент CRM (Supabase) + помощники для работы с лидами.

Вся запись/чтение лидов идёт через эти функции — чтобы и парсер,
и агенты работали с базой одинаково и переходы статусов были валидными.
"""
from __future__ import annotations

from typing import Any, Optional

from supabase import Client, create_client

from .config import settings
from .models import Lead, LeadStatus, can_transition

_client: Optional[Client] = None


def db() -> Client:
    """Ленивое создание клиента Supabase (service_role)."""
    global _client
    if _client is None:
        settings.require("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _client


# ---------- Создание / поиск ----------

def upsert_lead(lead: Lead) -> dict[str, Any]:
    """Создать лид (или обновить существующий по phone). Для парсера."""
    data = lead.model_dump(exclude_none=True, mode="json")
    data.pop("id", None)  # id генерит база
    res = db().table("leads").upsert(data, on_conflict="phone").execute()
    return res.data[0]


def get_lead_by_phone(phone: str) -> Optional[dict[str, Any]]:
    res = db().table("leads").select("*").eq("phone", phone).limit(1).execute()
    return res.data[0] if res.data else None


def get_lead(lead_id: str) -> Optional[dict[str, Any]]:
    res = db().table("leads").select("*").eq("id", lead_id).limit(1).execute()
    return res.data[0] if res.data else None


def leads_by_status(status: LeadStatus) -> list[dict[str, Any]]:
    res = db().table("leads").select("*").eq("status", status.value).execute()
    return res.data


# ---------- Обновления ----------

def update_lead(lead_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    res = db().table("leads").update(fields).eq("id", lead_id).execute()
    return res.data[0]


def set_status(
    lead_id: str,
    new_status: LeadStatus,
    *,
    extra: Optional[dict[str, Any]] = None,
    force: bool = False,
) -> dict[str, Any]:
    """Сменить статус лида с проверкой валидности перехода.

    extra — доп. поля для записи в той же операции (site_url, brief, ...).
    force — пропустить проверку перехода (для ручных правок).
    """
    lead = get_lead(lead_id)
    if lead is None:
        raise ValueError(f"Лид не найден: {lead_id}")

    current = LeadStatus(lead["status"])
    if not force and not can_transition(current, new_status):
        raise ValueError(
            f"Недопустимый переход {current.value} → {new_status.value} "
            f"(lead {lead_id}). Используй force=True, если это ручная правка."
        )

    fields: dict[str, Any] = {"status": new_status.value}
    if extra:
        fields.update(extra)
    return update_lead(lead_id, fields)


def append_message(lead_id: str, role: str, text: str) -> dict[str, Any]:
    """Добавить сообщение в историю переписки лида (conversation jsonb)."""
    lead = get_lead(lead_id)
    if lead is None:
        raise ValueError(f"Лид не найден: {lead_id}")
    conversation = lead.get("conversation") or []
    conversation.append({"role": role, "text": text})
    return update_lead(lead_id, {"conversation": conversation})
