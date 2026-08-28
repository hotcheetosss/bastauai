"""Извлечение КОНТЕНТА сайта из брифа через Gemini (структурированный JSON).

ИИ не пишет дизайн — только текст и выбор темы/акцента/иконок.
Возвращает pydantic-модель SiteContent, которую рендерер вставляет в шаблон.
"""
from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from shared.config import settings

from .icons import ICON_KEYS

GEMINI_MODEL = "gemini-3.1-flash-lite"


class ServiceItem(BaseModel):
    icon: str = Field(description="ключ иконки из разрешённого списка")
    name: str
    description: str = Field(description="1-2 коротких предложения, по-человечески")
    price: str = Field(description="например 'от 5 000 ₸' или '' если цены нет")


class Stat(BaseModel):
    num: str = Field(description="короткое число, напр. '8 лет', '15 000+'")
    label: str = Field(description="подпись под числом")


class ReviewItem(BaseModel):
    text: str
    author: str
    subtitle: str = Field(description="напр. 'клиент 2 года'")


class SiteContent(BaseModel):
    theme: Literal["light", "dark"] = "light"
    accent: str = Field(description="HEX-цвет акцента, напр. '#4f6ef7'")
    eyebrow: str = Field(description="короткий бейдж над заголовком, без эмодзи")
    hero_title_prefix: str
    hero_title_accent: str = Field(description="1-3 слова, выделятся цветом")
    hero_subtitle: str
    services_title: str
    services_subtitle: str
    services: list[ServiceItem]
    stats: list[Stat]
    about_title: str
    about_text: str
    reviews_title: str
    reviews: list[ReviewItem]
    cta_title: str
    cta_text: str
    footer_tagline: str


def _system_prompt() -> str:
    return (
        "Ты — копирайтер и арт-директор. По брифу о бизнесе ты готовишь КОНТЕНТ "
        "для одностраничного сайта на русском языке. Ты НЕ пишешь HTML/CSS — только "
        "текст и параметры оформления в заданной JSON-структуре.\n\n"
        "Правила:\n"
        "- Тексты живые, конкретные, human — без канцелярита, без «Lorem», без клише "
        "вроде «мы команда профессионалов».\n"
        "- НЕ используй эмодзи нигде.\n"
        "- 4-6 услуг. Первая — самая главная (она будет крупной). Для каждой услуги "
        f"выбери icon строго из этого списка ключей: {', '.join(ICON_KEYS)}.\n"
        "- 3 показателя stats (опыт, клиенты, мастера/ассортимент — что уместно бизнесу).\n"
        "- 3 правдоподобных отзыва с именами (subtitle вроде 'клиент 2 года').\n"
        "- theme: 'dark' если бизнес/стиль тяготеет к премиум/брутал/строгому "
        "(барбершоп, бар, тату, авто, ювелирка); иначе 'light' (кафе, детское, "
        "услуги, магазин, красота, спорт).\n"
        "- accent: HEX, подходящий бизнесу и пожеланиям по стилю из брифа.\n"
        "- Если в брифе есть услуги/цены/контакты — опирайся на них, не выдумывай лишнего."
    )


def _brief_to_text(business_name: str, brief: dict[str, Any]) -> str:
    b = brief or {}
    lines = [f"Название: {business_name}"]
    for key, label in [
        ("business_type", "Сфера"), ("goal", "Цель сайта"),
        ("style", "Пожелания по стилю"),
    ]:
        if b.get(key):
            lines.append(f"{label}: {b[key]}")
    if b.get("services"):
        lines.append("Услуги: " + ", ".join(map(str, b["services"])))
    if b.get("contacts"):
        lines.append("Контакты: " + "; ".join(f"{k}={v}" for k, v in b["contacts"].items() if v))
    return "\n".join(lines)


def extract_content(business_name: str, brief: dict[str, Any]) -> SiteContent:
    """Через Gemini получить структурированный контент сайта из брифа."""
    from google import genai
    from google.genai import types

    settings.require("GEMINI_API_KEY")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=_brief_to_text(business_name, brief),
        config=types.GenerateContentConfig(
            system_instruction=_system_prompt(),
            response_mime_type="application/json",
            response_schema=SiteContent,
            max_output_tokens=4000,
        ),
    )
    # google-genai заполняет .parsed при response_schema; подстрахуемся json.loads
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, SiteContent):
        return parsed
    return SiteContent(**json.loads(resp.text))
