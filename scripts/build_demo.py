"""Демо-запуск агента №2 на примере брифа (без CRM).

Генерирует сайт, сохраняет agents/site_builder/output/index.html, при флаге
--deploy заливает на Netlify и печатает публичную ссылку.

Примеры:
    .venv/Scripts/python.exe -m scripts.build_demo            # только генерация + локальный файл
    .venv/Scripts/python.exe -m scripts.build_demo --deploy   # + деплой на Netlify
"""
from __future__ import annotations

import argparse
from pathlib import Path

from agents.site_builder.deploy import deploy_to_netlify
from agents.site_builder.generator import generate_site_html
from agents.site_builder.prompt import build_site_prompt

# Пример брифа — как будто его собрал агент-продажник
SAMPLE_BUSINESS = "Барбершоп Alpha"
SAMPLE_BRIEF = {
    "business_type": "барбершоп",
    "goal": "запись клиентов онлайн",
    "services": ["мужская стрижка", "оформление бороды", "камуфляж седины", "детская стрижка"],
    "pages": ["главная", "услуги и цены", "о нас", "контакты"],
    "style": "тёмный, премиум, брутальный, акцент золотой",
    "contacts": {"whatsapp": "77001234567", "address": "Астана, пр. Кабанбай батыра 15", "phone": "+7 700 123 45 67"},
    "agreed": True,
}

OUT = Path(__file__).resolve().parent.parent / "agents" / "site_builder" / "output"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true", help="залить на Netlify")
    args = ap.parse_args()

    site_prompt = build_site_prompt(SAMPLE_BUSINESS, SAMPLE_BRIEF)
    print("=== ТЗ на сайт ===")
    print(site_prompt)
    print("\n=== Генерирую сайт через Claude (может занять до минуты)... ===")
    html = generate_site_html(site_prompt)

    OUT.mkdir(parents=True, exist_ok=True)
    index = OUT / "index.html"
    index.write_text(html, encoding="utf-8")
    print(f"Готово. Локальный файл: {index}")
    print(f"Размер: {len(html)} символов")

    if args.deploy:
        print("\n=== Деплой на Netlify... ===")
        url = deploy_to_netlify(html, name=None)
        print(f"✅ Опубликовано: {url}")
    else:
        print("\n(Деплой пропущен. Открой файл в браузере или запусти с --deploy.)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
