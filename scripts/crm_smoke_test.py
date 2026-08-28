"""Дымовой тест CRM: сквозная проверка подключения и слоя shared/db.py.

Запуск (из корня репо):
    .venv/Scripts/python.exe -m scripts.crm_smoke_test

Создаёт тестовый лид, читает, двигает по статусам, проверяет журнал событий
и удаляет за собой. Ничего постоянного в базе не оставляет.
"""
from __future__ import annotations

import sys

from shared.db import db, get_lead, set_status, upsert_lead
from shared.models import Lead, LeadStatus

TEST_PHONE = "70000000000"  # заведомо тестовый номер


def main() -> int:
    print("1) Подключение к Supabase...")
    client = db()  # бросит понятную ошибку, если ключи не заданы

    # чистим возможный хвост от прошлого прогона
    client.table("leads").delete().eq("phone", TEST_PHONE).execute()

    print("2) Создаю тестовый лид (upsert_lead)...")
    lead = upsert_lead(Lead(
        business_name="ТЕСТ Барбершоп",
        category="барбершоп",
        phone=TEST_PHONE,
        city="Астана",
        source="smoke_test",
    ))
    lead_id = lead["id"]
    print(f"   ok, id={lead_id}, status={lead['status']}")
    assert lead["status"] == "NEW", "новый лид должен быть NEW"

    print("3) Двигаю по статусам NEW -> CONTACTED -> IN_DIALOG -> QUALIFIED...")
    set_status(lead_id, LeadStatus.CONTACTED)
    set_status(lead_id, LeadStatus.IN_DIALOG)
    set_status(lead_id, LeadStatus.QUALIFIED, extra={"brief": {"agreed": True}})
    cur = get_lead(lead_id)
    print(f"   ok, текущий статус={cur['status']}")
    assert cur["status"] == "QUALIFIED"

    print("4) Проверяю защиту от невалидного перехода (QUALIFIED -> WON)...")
    try:
        set_status(lead_id, LeadStatus.WON)
        print("   ОШИБКА: недопустимый переход прошёл!")
        return 1
    except ValueError:
        print("   ok, невалидный переход заблокирован")

    print("5) Проверяю журнал событий (lead_events)...")
    events = client.table("lead_events").select("*").eq("lead_id", lead_id).execute()
    print(f"   записано событий смены статуса: {len(events.data)}")
    assert len(events.data) >= 3, "триггер журнала должен был записать переходы"

    print("6) Убираю за собой (delete)...")
    client.table("leads").delete().eq("id", lead_id).execute()
    assert get_lead(lead_id) is None
    print("   ok, тестовый лид удалён")

    print("\n✅ CRM работает: подключение, запись, статусы, журнал — всё ок.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
