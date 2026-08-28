"""ЭКСПЕРИМЕНТ: полная генерация сайта бесплатной Gemini (весь HTML сама).

Не трогает рабочий конвейер (design-system). Просто показывает, как выглядит
свободная генерация на бесплатной модели — сохраняет файлы локально в output/.

    .venv/Scripts/python.exe -m scripts.fullgen_demo
"""
from __future__ import annotations

import re
from pathlib import Path

from google import genai
from google.genai import types

from shared.config import settings

_DIR = Path(__file__).resolve().parent.parent / "agents" / "site_builder"
REFERENCE = (_DIR / "templates" / "flagship_light.html").read_text(encoding="utf-8")
OUT = _DIR / "output"

# лучшие бесплатные flash-модели по убыванию силы
FREE_MODELS = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]

RULES = """\
Ты — сильный веб-дизайнер и фронтенд-разработчик. По брифу создаёшь ОДИН готовый
HTML-файл — современный одностраничный сайт уровня топовых SaaS-лендингов.

ФОРМАТ: выводи ТОЛЬКО код, начиная с <!DOCTYPE html>. Без markdown, без ```.
Весь CSS внутри <style>. Google Fonts можно. Внешних JS-библиотек и картинок НЕТ.

ЗАПРЕЩЕНО (это слоп): эмодзи вместо иконок (только инлайн-SVG line-иконки);
фиолетовые градиенты по умолчанию; больше одного акцента; всё по центру мелким
шрифтом; вода и клише («в современном мире», «команда профессионалов», Lorem);
битые <img>; «© 2025» (ставь текущий год 2026).

ОБЯЗАТЕЛЬНО: шрифт Manrope; крупные жирные заголовки, плотный трекинг, много
воздуха (секции ~100px); нейтральная база + ОДИН акцент под бизнес; инлайн-SVG
иконки; секции — sticky-нав, hero с eyebrow и CTA на WhatsApp, показатели,
услуги (bento-сетка с ценами), о нас, отзывы с именами, финальный CTA, футер.
Тёмная премиум-тема для барбершоп/бар/авто/ювелирка; светлая дружелюбная для
кафе/детское/красота/услуги. Тексты живые, по-русски, без эмодзи в тексте.
Сделай ВИЗУАЛЬНО РАЗНООБРАЗНО — не копируй структуру примера один-в-один.
"""

CASES = {
    "coffee": ("Кофейня Semble", "Алматы",
               "кофейня, спешелти-кофе, завтраки, десерты; стиль светлый уютный тёплый; "
               "контакты: whatsapp 77012223344, ул. Достык 89, 08:00–23:00"),
    "auto": ("Detailing Garage", "Астана",
             "детейлинг авто: мойка, полировка, химчистка, керамика; стиль тёмный премиум; "
             "контакты: whatsapp 77015556677, пр. Туран 40, 09:00–21:00"),
    "dent": ("Стоматология Dental", "Астана",
             "стоматология: лечение, имплантация, отбеливание, брекеты; стиль светлый, "
             "чистый, доверие; контакты: whatsapp 77018889900, ул. Сыганак 10"),
}


def _strip(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n", "", t); t = re.sub(r"\n```$", "", t)
    i = t.find("<!DOCTYPE")
    return (t[i:] if i > 0 else t).strip()


def _gen(model: str, brief: str) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    user = (f"БРИФ: {brief}\n\nПример эталонного качества (адаптируй, НЕ копируй):\n"
            f"{REFERENCE}\n\nСгенерируй сайт. Только HTML.")
    resp = client.models.generate_content(
        model=model, contents=user,
        config=types.GenerateContentConfig(system_instruction=RULES, max_output_tokens=32000),
    )
    return _strip(resp.text or "")


def main() -> int:
    settings.require("GEMINI_API_KEY")
    OUT.mkdir(parents=True, exist_ok=True)
    for case, (name, city, brief) in CASES.items():
        full = f"Название: {name}. Город: {city}. {brief}"
        html, used = "", ""
        for m in FREE_MODELS:
            try:
                html = _gen(m, full)
                if html:
                    used = m; break
            except Exception as e:
                print(f"  {case}: {m} -> {type(e).__name__}: {str(e)[:70]}")
        if not html:
            print(f"{case}: не удалось сгенерировать"); continue
        f = OUT / f"fullgen_{case}.html"
        f.write_text(html, encoding="utf-8")
        print(f"{case}: {used} -> {f}  ({len(html)} симв)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
