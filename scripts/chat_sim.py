"""Симулятор диалога агента №1 — прогон логики мозга без CRM и WhatsApp.

Гоняет скриптованную переписку через brain.decide, обновляя локальный
бриф/статус, и печатает разговор. Проверяет: сбор брифа -> qualified ->
(имитация отправки демо) -> хендофф на вопрос о цене.

    .venv/Scripts/python.exe -m scripts.chat_sim
"""
from __future__ import annotations

from agents.sales_agent.brain import decide
from agents.sales_agent.handler import _merge_brief

# Клиент (как из парсера)
LEAD = {
    "business_name": "Барбершоп Alpha",
    "category": "барбершоп",
    "city": "Астана",
    "phone": "77001234567",
}

# Скрипт сообщений клиента
CLIENT_MESSAGES = [
    "Здравствуйте, а что за сайт?",
    "Стрижки, бороды, детские стрижки делаем",
    "Давайте тёмный, посолиднее",
    # --- дальше имитируем, что демо уже отправлена (статус SENT) ---
    "О, вау, круто получилось! А сколько будет стоить?",
]


def main() -> int:
    status = "CONTACTED"
    brief: dict = {}
    conversation: list[dict] = []
    demo_sent = False

    for i, msg in enumerate(CLIENT_MESSAGES):
        # после согласия имитируем, что система сгенерила и отправила демо
        if status == "QUALIFIED" and not demo_sent:
            print("\n   [система: агент №2 сгенерировал сайт и отправил ссылку клиенту]")
            print("   Агент: Готово! Вот демо: https://alpha-xxx.netlify.app — как вам? 🙂")
            conversation.append({"role": "agent", "text": "Готово! Вот демо: https://alpha-xxx.netlify.app — как вам?"})
            status = "SENT"
            demo_sent = True

        print(f"\nКлиент: {msg}")
        conversation.append({"role": "client", "text": msg})

        d = decide(
            business_name=LEAD["business_name"], incoming=msg, status=status,
            category=LEAD["category"], city=LEAD["city"], phone=LEAD["phone"],
            brief=brief, conversation=conversation,
        )

        print(f"Агент: {d.reply}")
        print(f"   └─ action={d.action} | intent={d.intent!r}")

        # применяем локально
        brief = _merge_brief(brief, d.brief)
        conversation.append({"role": "agent", "text": d.reply})
        if d.action == "qualified":
            status = "QUALIFIED"
        elif d.action == "continue" and status == "CONTACTED":
            status = "IN_DIALOG"
        elif d.action in ("lost", "revision"):
            status = d.action.upper()
        elif d.action == "handoff":
            print("   🔔 [HANDOFF → передаём живому менеджеру, агент замолкает]")

    print("\n" + "=" * 50)
    print("ИТОГ:")
    print(f"  статус: {status}")
    print(f"  собранный бриф: {brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
