"""Демо-запуск агента №2 на примере брифа (без CRM).

Генерирует сайт через дизайн-систему, сохраняет
agents/site_builder/output/index.html; при флаге --deploy заливает на Netlify.

    .venv/Scripts/python.exe -m scripts.build_demo
    .venv/Scripts/python.exe -m scripts.build_demo --deploy
    .venv/Scripts/python.exe -m scripts.build_demo --case cafe
"""
from __future__ import annotations

import argparse
from pathlib import Path

from agents.site_builder.deploy import deploy_to_netlify
from agents.site_builder.generator import generate_site_html

CASES = {
    "barber": ("Барбершоп Alpha", "Астана", {
        "business_type": "барбершоп",
        "goal": "запись клиентов онлайн",
        "services": ["мужская стрижка", "оформление бороды", "камуфляж седины", "детская стрижка"],
        "style": "тёмный, премиум, брутальный, золотой акцент",
        "contacts": {"whatsapp": "77001234567", "address": "Астана, пр. Кабанбай батыра 15",
                     "phone": "+7 700 123 45 67", "hours": "Ежедневно 10:00–22:00"},
        "agreed": True,
    }),
    "cafe": ("Кофейня Semble", "Алматы", {
        "business_type": "кофейня",
        "goal": "привлекать гостей и показать меню",
        "services": ["спешелти-кофе", "завтраки", "десерты ручной работы", "кофе с собой"],
        "style": "светлый, уютный, тёплый, дружелюбный",
        "contacts": {"whatsapp": "77012223344", "address": "Алматы, ул. Достык 89",
                     "phone": "+7 701 222 33 44", "hours": "Пн–Вс 08:00–23:00"},
        "agreed": True,
    }),
}

OUT = Path(__file__).resolve().parent.parent / "agents" / "site_builder" / "output"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--case", choices=list(CASES), default="barber")
    args = ap.parse_args()

    name, city, brief = CASES[args.case]
    print(f"=== Кейс: {args.case} — {name} ===")
    print("Генерирую (Gemini -> контент -> наш шаблон)...")
    html = generate_site_html(name, brief, city=city)

    OUT.mkdir(parents=True, exist_ok=True)
    index = OUT / "index.html"
    index.write_text(html, encoding="utf-8")
    print(f"Готово: {index}  ({len(html)} символов)")

    if args.deploy:
        print("Деплой на Netlify...")
        print("✅", deploy_to_netlify(html, name=None))
    else:
        print("(Деплой пропущен. Открой файл или запусти с --deploy.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
