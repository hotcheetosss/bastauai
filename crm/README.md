# CRM (Supabase)

Единая база проекта. Через неё общаются все компоненты (парсер, агенты).
Таблица `leads` — шина статусов; `lead_events` — журнал переходов.

## Как поднять

1. Создать проект на [supabase.com](https://supabase.com) (регион — ближайший, напр. Frankfurt).
2. Dashboard → **SQL Editor** → New query → вставить содержимое [`schema.sql`](schema.sql) → **Run**.
3. Settings → API → скопировать:
   - `Project URL` → в `.env` как `SUPABASE_URL`
   - `service_role` key → в `.env` как `SUPABASE_SERVICE_KEY` (секрет! только для бэкенда)
4. Проверить: SQL Editor → `select * from public.leads;` → пустая таблица без ошибок.

## Схема статусов

```
NEW → CONTACTED → IN_DIALOG → QUALIFIED → BUILDING → SITE_READY → SENT → REVISION → WON / LOST
```

Переходы валидируются в коде (`shared/models.py::ALLOWED_TRANSITIONS`) и логируются
триггером в `lead_events`.

## Кто что пишет

| Поле | Кто |
|---|---|
| `business_name, phone, category, city, source...` | парсер |
| `status = NEW → CONTACTED` | парсер / рассылка |
| `conversation, brief, status (диалог)` | агент №1 |
| `site_prompt, site_url, status (BUILDING/SITE_READY)` | агент №2 |

## Доступ для парсера друга

Дать другу отдельный ограниченный доступ (не делись service_role). Варианты:
- на старте — парсер пишет в CSV в формате колонок `leads`, ты импортируешь;
- позже — заведём отдельный ключ/политику RLS только на вставку в `leads`.
