"""Агент №2 «Сайт-билдер»: генерация сайта из брифа и деплой на Netlify."""
from .runner import build_from_brief, build_site_for_lead

__all__ = ["build_from_brief", "build_site_for_lead"]
