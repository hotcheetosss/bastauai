"""Генерация HTML-сайта из ТЗ. Сменный бэкенд: Gemini (по умолчанию) или Claude.

Выбор бэкенда — переменной GENERATOR в .env ('gemini' | 'claude'),
либо аргументом backend=... . Публичная функция одна:
    generate_site_html(site_prompt) -> html
"""
from __future__ import annotations

import re

from shared.config import settings

# Модели по умолчанию
GEMINI_MODEL = "gemini-3.1-flash-lite"   # быстрый/дешёвый; для качества — gemini-3.1-pro-preview
CLAUDE_MODEL = "claude-opus-5"      # для качества; дешевле — claude-sonnet-5
MAX_OUTPUT_TOKENS = 32000

SYSTEM_PROMPT = """\
Ты — сильный веб-дизайнер и фронтенд-разработчик. По ТЗ о бизнесе ты создаёшь \
готовый одностраничный сайт (лендинг) как ОДИН HTML-файл — превью того, как \
мог бы выглядеть сайт клиента.

Жёсткие требования к результату:
- Выводи ТОЛЬКО код HTML-файла, начиная с <!DOCTYPE html>. Без markdown, без \
пояснений, без ``` — только сам файл.
- Весь CSS — внутри <style> в <head>. Допустимы Google Fonts через <link>. \
Минимальный inline-JS допустим (бургер-меню, плавный скролл). Без внешних JS-библиотек.
- Дизайн современный, чистый, адаптивный (мобильный + десктоп). Аккуратная типографика, \
воздух, сетка, hover-эффекты. Не шаблонно — под конкретный бизнес.
- Язык контента — русский (если в ТЗ не сказано иначе). Тексты живые и по делу, \
без «Lorem ipsum». Заголовки, выгоды, блок услуг, «о нас», отзывы (правдоподобные), \
призыв к действию, контакты/футер.
- Обязательно кнопка-CTA на WhatsApp: ссылка вида https://wa.me/<номер> если номер \
есть в контактах; иначе — заметная кнопка «Связаться».
- Никаких битых изображений: используй CSS-градиенты, фигуры, эмодзи или \
inline-SVG вместо внешних картинок.
- Сайт должен выглядеть «вау» — так, чтобы владелец бизнеса захотел его купить.
"""

_USER_TEMPLATE = "Создай сайт по этому ТЗ. Помни: в ответе — только HTML-файл.\n\n{spec}"


def _strip_code_fences(text: str) -> str:
    """На случай, если модель обернёт ответ в ```html ... ```."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n", "", t)
        t = re.sub(r"\n```$", "", t)
    return t.strip()


def _generate_gemini(site_prompt: str, model: str) -> str:
    from google import genai
    from google.genai import types

    settings.require("GEMINI_API_KEY")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=model,
        contents=_USER_TEMPLATE.format(spec=site_prompt),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )
    return _strip_code_fences(resp.text or "")


def _generate_claude(site_prompt: str, model: str) -> str:
    import anthropic

    settings.require("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    with client.messages.stream(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _USER_TEMPLATE.format(spec=site_prompt)}],
    ) as stream:
        message = stream.get_final_message()
    html = "".join(b.text for b in message.content if b.type == "text")
    return _strip_code_fences(html)


def generate_site_html(
    site_prompt: str,
    *,
    backend: str | None = None,
    model: str | None = None,
) -> str:
    """Сгенерировать HTML-лендинг по текстовому ТЗ.

    backend: 'gemini' | 'claude' (по умолчанию из settings.GENERATOR).
    """
    backend = (backend or settings.GENERATOR or "gemini").lower()
    if backend == "gemini":
        return _generate_gemini(site_prompt, model or GEMINI_MODEL)
    if backend == "claude":
        return _generate_claude(site_prompt, model or CLAUDE_MODEL)
    raise ValueError(f"Неизвестный GENERATOR: {backend!r} (ожидается 'gemini' или 'claude')")
