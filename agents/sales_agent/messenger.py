"""Абстракция отправки сообщений в WhatsApp.

По умолчанию — заглушка в консоль (для тестов). В проде подменяется на
реальную отправку через GREEN-API вызовом set_sender(...).
"""
from __future__ import annotations

from typing import Callable, Optional

_sender: Optional[Callable[[str, str], None]] = None


def set_sender(fn: Callable[[str, str], None]) -> None:
    """Задать реальную функцию отправки: fn(phone, text)."""
    global _sender
    _sender = fn


def send_whatsapp(phone: str, text: str) -> None:
    """Отправить сообщение клиенту (или напечатать, если отправитель не задан)."""
    if _sender is not None:
        _sender(phone, text)
    else:
        print(f"   [WA → {phone}] {text}")
