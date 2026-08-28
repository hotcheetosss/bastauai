# bastau ai — Autopilot

Автоворонка: находим бизнесы **без сайта** → WhatsApp-касание → ИИ-продажник ведёт
диалог → ИИ генерит сайт и деплоит → отправляем клиенту готовую демо-ссылку.
Всё автоматически; ручное вмешательство только на этапе правок.

Полное ТЗ: [`docs/PROJECT_bastau_autopilot.md`](docs/PROJECT_bastau_autopilot.md)

## Структура монорепозитория

```
bastauai/
├── crm/              Схема Supabase (CRM = шина между компонентами)
├── shared/           Общий код: конфиг, клиент БД, модели Lead/Brief/статусы
├── agents/
│   ├── sales_agent/    ИИ-агент №1 «Продажник» (WhatsApp-диалог)
│   └── site_builder/   ИИ-агент №2 «Сайт-билдер» (Claude → сайт → деплой)
├── parser/           Парсер лидов без сайта      [зона разработчика №2]
├── outreach/         WhatsApp-рассылка касания    [зона разработчика №2]
├── docs/             Документация
├── .env.example      Шаблон ключей (в git)
└── .env              Реальные ключи (НЕ в git)
```

## Зоны ответственности

| Компонент | Владелец |
|---|---|
| `crm/`, `shared/`, `agents/` | Разработчик №1 |
| `parser/`, `outreach/` | Разработчик №2 |

Компоненты общаются **только через CRM** (Supabase), не вызывая друг друга напрямую.
Граница интеграции — таблица `leads` и её статусы.

## Быстрый старт (разработчик №1)

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # заполнить ключи
```

1. Поднять CRM: см. [`crm/README.md`](crm/README.md).
2. Дальше собираем агентов (`agents/site_builder` → `agents/sales_agent`).

## Правила

- **Секреты только в `.env`** (нет в git). В репо — `.env.example` с пустыми значениями.
- Запись в CRM — через `shared/db.py`, не напрямую, чтобы переходы статусов были валидны.
- Каждый работает в своей папке → минимум git-конфликтов.
