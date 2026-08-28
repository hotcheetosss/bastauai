"""Быстро добавить лид в CRM (для теста WhatsApp-воркера).

Телефон — это номер, С КОТОРОГО ты будешь писать боту (отправитель).
Агент №1 ищет лид по номеру отправителя, поэтому он должен быть в базе.

    .venv/Scripts/python.exe -m scripts.add_lead 77012223344 "Барбершоп Alpha" барбершоп Астана
"""
from __future__ import annotations

import re
import sys

from shared.db import upsert_lead
from shared.models import Lead, LeadStatus


def main() -> int:
    if len(sys.argv) < 3:
        print("Использование: add_lead <phone> <business_name> [category] [city]")
        return 1
    phone = re.sub(r"\D", "", sys.argv[1])
    lead = upsert_lead(Lead(
        business_name=sys.argv[2],
        category=sys.argv[3] if len(sys.argv) > 3 else None,
        city=sys.argv[4] if len(sys.argv) > 4 else None,
        phone=phone,
        status=LeadStatus.CONTACTED,   # как будто первое касание уже отправлено
        source="manual_test",
    ))
    print(f"Лид создан: {lead['business_name']} / {phone} / статус {lead['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
