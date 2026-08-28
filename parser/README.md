# parser/ — Парсер лидов [зона разработчика №2]

**Задача:** собрать бизнесы **без сайта** (2ГИС / Google Maps / Instagram) с контактным
WhatsApp/телефоном и записать их в CRM со статусом `NEW`.

## Контракт с CRM

Пиши лиды в таблицу `leads` (Supabase). Формат полей и пример запроса —
в [`../docs/PROJECT_bastau_autopilot.md`](../docs/PROJECT_bastau_autopilot.md), раздел 4.

Обязательно:
- телефон в формате `77XXXXXXXXX` (без `+`, пробелов, скобок);
- дедуп по `phone`;
- `has_site = false`, `status = "NEW"`.

На старте можно писать в CSV с теми же колонками — разработчик №1 импортирует.

## Общий код

Для записи в CRM из Python используй `shared/db.py::upsert_lead` и модель
`shared/models.py::Lead` — чтобы формат совпадал с тем, что ждут агенты.
