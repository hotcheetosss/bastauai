"""Структура решения агента-продажника (structured output от LLM)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Действие, которое агент предлагает по итогам сообщения:
# continue  — обычный ход диалога (собираем бриф)
# qualified — есть услуги+стиль+согласие на демо → запустить генерацию сайта
# handoff   — передать живому человеку (цена/заказ/агрессия/реакция на демо)
# revision  — клиент просит правки уже показанной демо
# lost      — клиент отказался / не интересно
Action = Literal["continue", "qualified", "handoff", "revision", "lost"]


class BriefUpdate(BaseModel):
    """Что нового агент узнал о бизнесе (кладём только реально услышанное)."""
    business_type: Optional[str] = None
    goal: Optional[str] = None
    services: list[str] = Field(default_factory=list)
    style: Optional[str] = None
    address: Optional[str] = None
    hours: Optional[str] = None
    agreed: Optional[bool] = None


class AgentDecision(BaseModel):
    reply: str = Field(description="сообщение клиенту в WhatsApp, коротко")
    action: Action = "continue"
    intent: str = Field(default="", description="короткий ярлык настроя клиента")
    brief: BriefUpdate = Field(default_factory=BriefUpdate)
