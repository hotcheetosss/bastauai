"""Общие модели данных проекта bastau ai.

Используются всеми компонентами (парсер, агенты) для единообразной
работы с CRM. Меняешь схему лида здесь — меняется у всех.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    """Конечный автомат лида. Порядок = движение по воронке."""
    NEW = "NEW"                 # парсер создал лид
    CONTACTED = "CONTACTED"     # отправлено первое касание
    IN_DIALOG = "IN_DIALOG"     # клиент ответил, агент №1 в диалоге
    QUALIFIED = "QUALIFIED"     # согласие + бриф → триггер агента №2
    BUILDING = "BUILDING"       # агент №2 строит сайт
    SITE_READY = "SITE_READY"   # сайт готов → триггер агента №1
    SENT = "SENT"               # ссылка отправлена клиенту
    REVISION = "REVISION"       # правки (дальше ручное вмешательство)
    WON = "WON"                 # успех
    LOST = "LOST"               # отказ


# Разрешённые переходы статусов. Защищает шину от невалидных скачков.
ALLOWED_TRANSITIONS: dict[LeadStatus, set[LeadStatus]] = {
    LeadStatus.NEW:        {LeadStatus.CONTACTED, LeadStatus.LOST},
    LeadStatus.CONTACTED:  {LeadStatus.IN_DIALOG, LeadStatus.LOST},
    LeadStatus.IN_DIALOG:  {LeadStatus.QUALIFIED, LeadStatus.LOST},
    LeadStatus.QUALIFIED:  {LeadStatus.BUILDING, LeadStatus.LOST},
    LeadStatus.BUILDING:   {LeadStatus.SITE_READY, LeadStatus.LOST},
    LeadStatus.SITE_READY: {LeadStatus.SENT, LeadStatus.LOST},
    LeadStatus.SENT:       {LeadStatus.REVISION, LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.REVISION:   {LeadStatus.SENT, LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.WON:        set(),
    LeadStatus.LOST:       {LeadStatus.IN_DIALOG},  # передумал — можно вернуть
}


def can_transition(src: LeadStatus, dst: LeadStatus) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


class Brief(BaseModel):
    """Бриф на сайт — собирает агент №1, потребляет агент №2."""
    business_type: Optional[str] = None
    goal: Optional[str] = None
    pages: list[str] = Field(default_factory=list)
    style: Optional[str] = None
    services: list[str] = Field(default_factory=list)
    contacts: dict[str, Any] = Field(default_factory=dict)
    agreed: bool = False

    def is_ready(self) -> bool:
        """Достаточно ли данных, чтобы запускать агента №2."""
        return self.agreed and bool(self.business_type) and bool(self.goal)


class Lead(BaseModel):
    """Строка таблицы leads."""
    id: Optional[str] = None
    business_name: str
    category: Optional[str] = None
    phone: str
    whatsapp: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    has_site: bool = False
    status: LeadStatus = LeadStatus.NEW
    conversation: list[dict[str, Any]] = Field(default_factory=list)
    brief: dict[str, Any] = Field(default_factory=dict)
    site_prompt: Optional[str] = None
    site_url: Optional[str] = None
    assigned_number: Optional[str] = None
    note: Optional[str] = None
