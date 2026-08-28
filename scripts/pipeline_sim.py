"""Сквозной тест ВСЕГО конвейера на реальной CRM (без WhatsApp).

Поток: создаём лид -> диалог (агент №1 пишет в CRM) -> QUALIFIED ->
оркестратор строит сайт (агент №2) -> SITE_READY -> агент №1 шлёт ссылку ->
SENT -> вопрос о цене -> HANDOFF. В конце — чистит тестовый лид.

    .venv/Scripts/python.exe -m scripts.pipeline_sim            # без деплоя (бесплатно)
    .venv/Scripts/python.exe -m scripts.pipeline_sim --deploy   # + реальный Netlify
"""
from __future__ import annotations

import argparse

from agents.orchestrator import run_pipeline
from agents.sales_agent.handler import process_incoming
from shared.db import db, get_lead_by_phone, upsert_lead
from shared.models import Lead, LeadStatus

TEST_PHONE = "70000000009"

PRE_DEMO = [
    "Здравствуйте, а что за сайт?",
    "Стрижки, бороды, детские стрижки делаем",
    "Давайте тёмный, посолиднее",
]
POST_DEMO_MSG = "О, вау, круто получилось! А сколько будет стоить?"


def _print_lead(lead: dict) -> None:
    print(f"   статус={lead['status']}  site_url={lead.get('site_url')}")
    print(f"   бриф={lead.get('brief')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true", help="реальный деплой на Netlify")
    ap.add_argument("--keep", action="store_true", help="не удалять тестовый лид")
    args = ap.parse_args()

    # чистим хвост и создаём тестовый лид (как после первого касания)
    db().table("leads").delete().eq("phone", TEST_PHONE).execute()
    upsert_lead(Lead(
        business_name="Барбершоп Alpha", category="барбершоп", city="Астана",
        phone=TEST_PHONE, status=LeadStatus.CONTACTED, source="pipeline_sim",
    ))
    print(f"Создан тестовый лид ({TEST_PHONE}), статус CONTACTED\n")

    print("--- ДИАЛОГ (агент №1) ---")
    for msg in PRE_DEMO:
        print(f"Клиент: {msg}")
        reply = process_incoming(TEST_PHONE, msg)
        print(f"Агент:  {reply}\n")

    lead = get_lead_by_phone(TEST_PHONE)
    print(f"[после диалога] статус: {lead['status']}")

    if lead["status"] == LeadStatus.QUALIFIED.value:
        print("\n--- ОРКЕСТРАТОР: QUALIFIED -> сайт -> ссылка ---")
        steps = run_pipeline(lead["id"], deploy=args.deploy)
        print(f"   автошаги: {steps}")

    lead = get_lead_by_phone(TEST_PHONE)
    print("\n[после конвейера]")
    _print_lead(lead)

    print(f"\n--- РЕАКЦИЯ НА ДЕМО ---\nКлиент: {POST_DEMO_MSG}")
    reply = process_incoming(TEST_PHONE, POST_DEMO_MSG)
    print(f"Агент:  {reply}")

    lead = get_lead_by_phone(TEST_PHONE)
    print("\n" + "=" * 54)
    print("ИТОГ КОНВЕЙЕРА:")
    _print_lead(lead)
    print(f"   сообщений в истории: {len(lead.get('conversation') or [])}")

    if not args.keep:
        db().table("leads").delete().eq("phone", TEST_PHONE).execute()
        print("\n(тестовый лид удалён)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
