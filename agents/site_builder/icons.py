"""Курируемый набор инлайн-SVG line-иконок (без эмодзи — это анти-слоп).

ИИ выбирает иконку по ключу из ICON_KEYS; Python подставляет готовый SVG.
Неизвестный ключ → аккуратный дефолт.
"""
from __future__ import annotations

# ключ -> внутренность <svg viewBox="0 0 24 24">
_PATHS: dict[str, str] = {
    "scissors": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.5 15.5M14.5 14.5 20 20"/>',
    "beard": '<path d="M4 6c4 2 12 2 16 0M6 6c0 6 2 10 6 10s6-4 6-10"/>',
    "razor": '<path d="M14 3 21 10 10 21H3v-7L14 3Z"/><path d="M12 5l7 7"/>',
    "child": '<circle cx="12" cy="8" r="4"/><path d="M5 21c0-4 3-6 7-6s7 2 7 6"/>',
    "crown": '<path d="M3 8l4 4 5-7 5 7 4-4-2 11H5L3 8Z"/>',
    "spark": '<path d="M12 3a9 9 0 1 0 9 9M12 3v9l6-3"/>',
    "star": '<path d="m12 3 2.5 5 5.5.8-4 4 1 5.5-5-2.6-5 2.6 1-5.5-4-4 5.5-.8Z"/>',
    "coffee": '<path d="M4 8h13v4a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8Z"/><path d="M17 9h2a2 2 0 0 1 0 4h-2M6 3v2M10 3v2M14 3v2"/>',
    "cup": '<path d="M6 2h12l-1 7a5 5 0 0 1-10 0L6 2Z"/><path d="M9 22h6M12 14v8"/>',
    "car": '<path d="M3 13l2-5a3 3 0 0 1 3-2h8a3 3 0 0 1 3 2l2 5v5h-3M3 13v5h3M3 13h18"/><circle cx="7.5" cy="18" r="1.5"/><circle cx="16.5" cy="18" r="1.5"/>',
    "wrench": '<path d="M15 3a5 5 0 0 0-4.9 6L3 16.1V21h4.9l7.1-7.1A5 5 0 1 0 15 3Z"/>',
    "gear": '<circle cx="12" cy="12" r="3.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    "shop": '<path d="M4 9h16l-1-4H5L4 9Z"/><path d="M4 9v11h16V9M9 20v-6h6v6"/>',
    "bag": '<path d="M6 8h12l1 12H5L6 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    "dumbbell": '<path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10"/>',
    "heart": '<path d="M12 20s-7-4.5-9-9a5 5 0 0 1 9-3 5 5 0 0 1 9 3c-2 4.5-9 9-9 9Z"/>',
    "leaf": '<path d="M5 20c0-9 6-15 15-15 0 9-6 15-15 15Z"/><path d="M5 20 15 10"/>',
    "flame": '<path d="M12 3c3 4 5 6 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-6 1-9Z"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="3"/><circle cx="12" cy="13" r="3.5"/><path d="M8 7l1.5-2h5L16 7"/>',
    "tooth": '<path d="M12 4c2-1 5-1 6 2s-1 5-1 8-1 6-2 6-1-4-3-4-2 4-3 4-2-3-2-6-2-5-1-8 4-3 6-2Z"/>',
    "brush": '<path d="M4 20c0-2 1-3 3-3 1.5 0 2 1 2 2s-1 2-3 2H4v-1Z"/><path d="M9 15 20 4a2 2 0 0 0-3-3L6 12"/>',
    "flower": '<circle cx="12" cy="12" r="2.5"/><path d="M12 9V4M12 15v5M9 12H4M15 12h5M9.5 9.5 6 6M14.5 9.5 18 6M9.5 14.5 6 18M14.5 14.5 18 18"/>',
    "check": '<path d="M4 12l5 5 11-11"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "pin": '<path d="M20 10c0 6-8 11-8 11s-8-5-8-11a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    "phone": '<path d="M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z"/>',
    "whatsapp": '<path d="M21 11.5a8.5 8.5 0 0 1-12.5 7.5L3 21l2-5.5A8.5 8.5 0 1 1 21 11.5Z"/>',
    "home": '<path d="M4 11 12 4l8 7M6 10v10h12V10"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6l8-3Z"/>',
    "gift": '<rect x="3" y="8" width="18" height="4"/><path d="M5 12v9h14v-9M12 8v13"/><path d="M12 8S9 3 7 5s5 3 5 3Zm0 0s3-5 5-3-5 3-5 3Z"/>',
    "truck": '<path d="M3 6h11v9H3zM14 9h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.5"/><circle cx="17" cy="18" r="1.5"/>',
}

ICON_KEYS = sorted(_PATHS.keys())
_DEFAULT = "spark"


def get_icon(key: str) -> str:
    """Вернуть готовую SVG-разметку иконки по ключу (или дефолт)."""
    inner = _PATHS.get((key or "").strip().lower(), _PATHS[_DEFAULT])
    return (
        '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>"
    )
