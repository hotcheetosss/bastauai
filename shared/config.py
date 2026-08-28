"""Единая точка загрузки конфигурации из .env.

Импортируй settings отсюда, не читай os.environ напрямую по проекту.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Грузим .env из корня репозитория (bastauai/.env)
load_dotenv()


class Settings:
    # --- Supabase ---
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # --- Генератор сайтов: 'gemini' (бесплатный старт) или 'claude' ---
    GENERATOR: str = os.getenv("GENERATOR", "gemini")

    # --- Claude ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- Gemini (Google AI Studio, бесплатный ключ) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # --- GREEN-API (WhatsApp) ---
    GREENAPI_ID_INSTANCE: str = os.getenv("GREENAPI_ID_INSTANCE", "")
    GREENAPI_API_TOKEN: str = os.getenv("GREENAPI_API_TOKEN", "")
    GREENAPI_API_URL: str = os.getenv("GREENAPI_API_URL", "https://api.green-api.com")

    # --- Деплой ---
    NETLIFY_AUTH_TOKEN: str = os.getenv("NETLIFY_AUTH_TOKEN", "")
    VERCEL_TOKEN: str = os.getenv("VERCEL_TOKEN", "")

    # --- Уведомления менеджеру ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MANAGER_CHAT_ID: str = os.getenv("TELEGRAM_MANAGER_CHAT_ID", "")

    def require(self, *names: str) -> None:
        """Падаем рано с понятной ошибкой, если ключа нет."""
        missing = [n for n in names if not getattr(self, n, "")]
        if missing:
            raise RuntimeError(
                f"Не заданы переменные окружения: {', '.join(missing)}. "
                f"Проверь файл .env (шаблон в .env.example)."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
