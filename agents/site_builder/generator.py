"""Генерация HTML-сайта из ТЗ через Claude API.

Сменный бэкенд: сегодня — Anthropic API (по ключу ANTHROPIC_API_KEY),
завтра при желании можно добавить путь через подписку (Claude Code headless).
Публичная функция одна: generate_site_html(site_prompt) -> html.
"""
from __future__ import annotations

import re

import anthropic

from shared.config import settings

# Модель по умолчанию. Для максимального качества — claude-opus-5.
# Чтобы удешевить в 1.5-2 раза, поменяй на "claude-sonnet-5".
MODEL = "claude-opus-5"
MAX_TOKENS = 16000

SYSTEM_PROMPT = """\
Ты — сильный веб-дизайнер и фронтенд-разработчик. По ТЗ о бизнесе ты создаёшь \
готовый одностраничный сайт (лендинг) как ОДИН HTML-файл.

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


def _strip_code_fences(text: str) -> str:
    """На случай, если модель всё же обернёт ответ в ```html ... ```."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n", "", t)
        t = re.sub(r"\n```$", "", t)
    return t.strip()


def generate_site_html(site_prompt: str, *, model: str = MODEL) -> str:
    """Сгенерировать HTML-лендинг по текстовому ТЗ. Требует ANTHROPIC_API_KEY."""
    settings.require("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    user_msg = (
        "Создай сайт по этому ТЗ. Помни: в ответе — только HTML-файл.\n\n"
        f"{site_prompt}"
    )

    # Стриминг, чтобы не упереться в HTTP-таймаут на длинной генерации.
    with client.messages.stream(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        message = stream.get_final_message()

    html = "".join(b.text for b in message.content if b.type == "text")
    return _strip_code_fences(html)
