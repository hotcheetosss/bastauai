"""Клиент GREEN-API — реальный WhatsApp: отправка + приём входящих (опросом).

Приём через receiveNotification/deleteNotification не требует публичного
сервера — удобно для локального теста. В проде можно перейти на webhook.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from shared.config import settings


def _base() -> str:
    settings.require("GREENAPI_ID_INSTANCE", "GREENAPI_API_TOKEN")
    url = settings.GREENAPI_API_URL.rstrip("/")
    return f"{url}/waInstance{settings.GREENAPI_ID_INSTANCE}"


def _tok() -> str:
    return settings.GREENAPI_API_TOKEN


def _chat_id(phone: str) -> str:
    return re.sub(r"\D", "", phone or "") + "@c.us"


def send_by_phone(phone: str, text: str, *, timeout: float = 20.0) -> dict[str, Any]:
    """Отправить текст клиенту. Годится как sender для messenger.set_sender."""
    r = httpx.post(
        f"{_base()}/sendMessage/{_tok()}",
        json={"chatId": _chat_id(phone), "message": text},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


def receive_notification(*, receive_timeout: int = 5) -> Optional[dict[str, Any]]:
    """Забрать следующее входящее событие (или None, если очередь пуста).

    receive_timeout — сколько секунд сервер держит ответ, если очередь пуста.
    Короткое значение => цикл воркера чаще проверяет буфер (для дебаунса).
    """
    r = httpx.get(
        f"{_base()}/receiveNotification/{_tok()}",
        params={"receiveTimeout": receive_timeout},
        timeout=receive_timeout + 15,
    )
    r.raise_for_status()
    return r.json()  # {'receiptId': N, 'body': {...}} либо null


def delete_notification(receipt_id: int, *, timeout: float = 20.0) -> None:
    """Подтвердить обработку события (убрать из очереди)."""
    httpx.delete(f"{_base()}/deleteNotification/{_tok()}/{receipt_id}", timeout=timeout)


def parse_incoming(body: dict[str, Any]) -> Optional[tuple[str, str]]:
    """Из тела события вытащить (phone, text) для входящего текстового сообщения.

    Возвращает None, если это не входящий текст (статусы доставки и пр.).
    """
    if body.get("typeWebhook") != "incomingMessageReceived":
        return None
    chat_id = (body.get("senderData") or {}).get("chatId", "")
    if not chat_id.endswith("@c.us"):  # игнорируем группы/каналы
        return None
    phone = chat_id.replace("@c.us", "")
    md = body.get("messageData") or {}
    tp = md.get("typeMessage")
    if tp == "textMessage":
        text = (md.get("textMessageData") or {}).get("textMessage", "")
    elif tp == "extendedTextMessage":
        text = (md.get("extendedTextMessageData") or {}).get("text", "")
    else:
        return None  # не текст (фото/аудио/…) — пока пропускаем
    if not text:
        return None
    return phone, text
