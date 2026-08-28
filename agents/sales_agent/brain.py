"""Мозг агента-продажника: одно сообщение клиента -> решение (AgentDecision).

Stateless: вся память (история, бриф, статус) приходит аргументами.
Использует Gemini со структурированным выводом. Требует GEMINI_API_KEY.
"""
from __future__ import annotations

import json
from typing import Any

from shared.config import settings

from .models import AgentDecision

MODEL = "gemini-3.1-flash-lite"

SYSTEM_PROMPT = """\
Ты — менеджер агентства «SAQ Agency». Общаешься с потенциальным клиентом в WhatsApp
и ведёшь его к БЕСПЛАТНОЙ демо-версии сайта для его бизнеса.

СТИЛЬ ОБЩЕНИЯ:
- Коротко и по-человечески, на «вы». WhatsApp-стиль: 1–3 предложения.
- Русский язык; если клиент пишет на казахском — отвечай на казахском.
- Тепло, без напора и канцелярита. Без спама эмодзи (максимум один уместный).

УВАЖЕНИЕ К ОТКАЗУ (обязательно):
- Если клиент просит не писать, отписаться, злится на рассылку или говорит «стоп»/
  «не беспокойте» — НЕМЕДЛЕННО вежливо извинись за беспокойство, попрощайся и
  верни action="lost". Не уговаривай, не дожимай, больше ничего не предлагай.

ТВОЯ ЦЕЛЬ ПО ШАГАМ:
1. Если клиент только вышел на связь — тепло представься (от лица SAQ Agency) и
   предложи БЕСПЛАТНО показать демо-сайт. НЕ предполагай тип бизнеса и НЕ упоминай его
   в первом сообщении (не пиши «для вашего барбершопа/магазина/салона X»). Сначала
   мягко узнай, чем занимается бизнес и какие основные услуги.
2. Собери МИНИ-бриф — достаточно двух вещей:
   • какие основные услуги/товары предлагает (services);
   • стиль: строгий тёмный премиум ИЛИ светлый и дружелюбный (style).
   Не задавай много вопросов. Если клиент не знает про стиль — предложи сам по типу бизнеса.
   Адрес и часы можешь уточнить, но это НЕ обязательно.
3. Как только знаешь услуги + стиль и клиент согласен посмотреть демо — верни
   action="qualified" и ответь коротко в духе «Отлично, готовлю вариант, пара минут».
   Дальше сайт сделает система, тебе больше ничего собирать не нужно.

ПОСЛЕ отправки демо (СТАТУС ЛИДА = SENT):
- Клиент доволен / спрашивает цену / хочет заказать → action="handoff".
  Ответь тепло, что сейчас подключится коллега по деталям. Цену НЕ называй.
- Клиент хочет что-то изменить в сайте → action="revision".

ПРАВИЛА action:
- "continue"  — обычный ход диалога, ещё собираем бриф.
- "qualified" — есть услуги + стиль + согласие; ТОЛЬКО до отправки демо.
- "handoff"   — вопрос цены/сроков, торг, «хочу заказать», агрессия, сложный
                нестандартный вопрос, ИЛИ любая реакция на уже отправленную демо.
- "revision"  — клиент просит изменить уже показанную демо.
- "lost"      — ТОЛЬКО при явном отказе: «мне не нужен сайт», «не интересно»,
                «не пишите». НЕ ставь lost из-за странных сообщений, шуток,
                проверок или оффтопа.

НЕ ЗАКАНЧИВАЙ ДИАЛОГ ПРЕЖДЕВРЕМЕННО:
- Клиент шлёт оффтоп (математика, код, посторонние темы, провокации) — коротко и
  дружелюбно верни разговор к сайту, НЕ прощайся и НЕ ставь lost.
- Принимай ЛЮБЫЕ пожелания по стилю/дизайну, даже необычные («японский киберпанк»,
  «в стиле смешариков» и т.п.) — это бесплатное демо, мы можем попробовать что угодно.
  НЕ отказывай в стиле и НЕ говори, что «работаем только в классических стилях».
- Прощайся ТОЛЬКО когда клиент сам явно отказался (тогда action="lost").

СТРОГО ЗАПРЕЩЕНО:
- Называть цену, сроки, гарантии. На вопрос о цене → action="handoff".
- Выдумывать факты о бизнесе клиента.
- Длинные полотна текста.

В поле brief клади ТОЛЬКО реально услышанное. agreed=true — лишь при явном согласии
посмотреть демо. Всегда возвращай JSON заданной структуры.
"""


def _state_block(
    *, business_name: str, category: str | None, city: str | None,
    phone: str | None, status: str, brief: dict[str, Any],
    conversation: list[dict[str, Any]], incoming: str,
) -> str:
    transcript = "\n".join(
        f"{'Клиент' if m.get('role') == 'client' else 'Агент'}: {m.get('text','')}"
        for m in (conversation or [])
    ) or "(переписки ещё не было)"
    brief_str = json.dumps(brief, ensure_ascii=False) if brief else "пусто"
    return (
        "БИЗНЕС КЛИЕНТА:\n"
        f"- Название: {business_name}\n"
        f"- Категория: {category or '—'}\n"
        f"- Город: {city or '—'}\n"
        f"- Телефон: {phone or '—'}\n\n"
        f"СТАТУС ЛИДА: {status}  "
        "(CONTACTED=только вышел на связь; IN_DIALOG=идёт диалог; SENT=демо уже отправлена)\n\n"
        f"УЖЕ ИЗВЕСТНО (бриф): {brief_str}\n\n"
        f"ИСТОРИЯ ПЕРЕПИСКИ:\n{transcript}\n\n"
        f"НОВОЕ СООБЩЕНИЕ КЛИЕНТА:\n{incoming}\n\n"
        "Ответь клиенту и верни решение в заданной структуре."
    )


def decide(
    *,
    business_name: str,
    incoming: str,
    status: str = "CONTACTED",
    category: str | None = None,
    city: str | None = None,
    phone: str | None = None,
    brief: dict[str, Any] | None = None,
    conversation: list[dict[str, Any]] | None = None,
) -> AgentDecision:
    """Принять одно сообщение клиента, вернуть решение агента."""
    from google import genai
    from google.genai import types

    settings.require("GEMINI_API_KEY")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    state = _state_block(
        business_name=business_name, category=category, city=city, phone=phone,
        status=status, brief=brief or {}, conversation=conversation or [], incoming=incoming,
    )
    resp = client.models.generate_content(
        model=MODEL,
        contents=state,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AgentDecision,
            max_output_tokens=1200,
        ),
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, AgentDecision):
        return parsed
    return AgentDecision(**json.loads(resp.text))
