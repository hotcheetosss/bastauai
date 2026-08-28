"""Общий код проекта bastau ai: конфиг, клиент CRM, модели данных."""
from .config import settings
from .models import Brief, Lead, LeadStatus, can_transition

__all__ = ["settings", "Brief", "Lead", "LeadStatus", "can_transition"]
