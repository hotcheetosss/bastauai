-- ============================================================
--  bastau ai — CRM schema (Supabase / PostgreSQL)
--  Применение: Supabase Dashboard → SQL Editor → вставить → Run.
--  Идемпотентно: можно запускать повторно.
-- ============================================================

-- ---------- 1. Статусы лида (конечный автомат) ----------
-- NEW        — парсер создал лид
-- CONTACTED  — отправлено первое касание (рассылка)
-- IN_DIALOG  — клиент ответил, агент №1 ведёт диалог
-- QUALIFIED  — согласие + бриф собран  → триггерит агента №2
-- BUILDING   — агент №2 генерирует сайт
-- SITE_READY — сайт задеплоен, site_url готов → триггерит агента №1
-- SENT       — ссылка отправлена клиенту
-- REVISION   — клиент попросил правки (дальше ручное вмешательство)
-- WON        — сделка закрыта успешно
-- LOST       — отказ / не отвечает

do $$
begin
  if not exists (select 1 from pg_type where typname = 'lead_status') then
    create type lead_status as enum (
      'NEW', 'CONTACTED', 'IN_DIALOG', 'QUALIFIED',
      'BUILDING', 'SITE_READY', 'SENT', 'REVISION', 'WON', 'LOST'
    );
  end if;
end$$;

-- ---------- 2. Таблица лидов ----------
create table if not exists public.leads (
  id             uuid primary key default gen_random_uuid(),

  -- заполняет ПАРСЕР
  business_name  text        not null,
  category       text,
  phone          text        not null,              -- формат 77XXXXXXXXX
  whatsapp       text,                               -- если отличается от phone
  city           text,
  address        text,
  source         text,                               -- '2gis' | 'google_maps' | 'instagram'
  source_url     text,
  has_site       boolean     not null default false,

  -- ведут АГЕНТЫ (шина статусов)
  status         lead_status not null default 'NEW',
  conversation   jsonb       not null default '[]'::jsonb,  -- история переписки
  brief          jsonb       not null default '{}'::jsonb,  -- собранный бриф на сайт

  -- заполняет АГЕНТ №2
  site_prompt    text,
  site_url       text,

  -- служебное
  assigned_number text,                              -- с какого WA-номера ведём лид
  note           text,                               -- заметка менеджера
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

-- Один бизнес — один лид (дедуп по телефону)
create unique index if not exists leads_phone_key on public.leads (phone);

-- Быстрая выборка по статусу (агенты постоянно фильтруют по нему)
create index if not exists leads_status_idx on public.leads (status);
create index if not exists leads_created_at_idx on public.leads (created_at desc);

-- ---------- 3. Авто-обновление updated_at ----------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end$$;

drop trigger if exists trg_leads_updated_at on public.leads;
create trigger trg_leads_updated_at
  before update on public.leads
  for each row execute function public.set_updated_at();

-- ---------- 4. Журнал событий (аудит переходов статусов) ----------
-- Помогает отлаживать стыковку агентов: кто и когда сменил статус.
create table if not exists public.lead_events (
  id          bigserial primary key,
  lead_id     uuid not null references public.leads(id) on delete cascade,
  actor       text,                                  -- 'parser' | 'outreach' | 'sales_agent' | 'site_builder' | 'human'
  from_status lead_status,
  to_status   lead_status,
  payload     jsonb default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

create index if not exists lead_events_lead_idx on public.lead_events (lead_id, created_at);

-- Автоматически логируем каждую смену статуса
create or replace function public.log_status_change()
returns trigger language plpgsql as $$
begin
  if new.status is distinct from old.status then
    insert into public.lead_events (lead_id, from_status, to_status)
    values (new.id, old.status, new.status);
  end if;
  return new;
end$$;

drop trigger if exists trg_leads_status_log on public.leads;
create trigger trg_leads_status_log
  after update on public.leads
  for each row execute function public.log_status_change();

-- ---------- 5. Row Level Security ----------
-- Бэкенд ходит с service_role ключом, который ОБХОДИТ RLS.
-- Включаем RLS, чтобы случайно нельзя было читать таблицу с anon-ключом (напр. с фронта).
alter table public.leads       enable row level security;
alter table public.lead_events enable row level security;
-- Политик не добавляем: доступ только через service_role (бэкенд). При появлении
-- фронта-дашборда сюда добавим точечные политики на select/update.

-- ============================================================
--  Готово. Проверка: select * from public.leads;
-- ============================================================
