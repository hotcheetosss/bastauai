"""Локальный WhatsApp-воркер (GREEN-API, без публичного сервера).

Крутит цикл:
  1) продвигает лидов по конвейеру (QUALIFIED->сайт->ссылка) — orchestrator.poll_once
  2) забирает входящее сообщение WhatsApp -> агент №1 отвечает
Реальная отправка идёт через GREEN-API (messenger.set_sender).

    .venv/Scripts/python.exe -m scripts.whatsapp_worker            # с деплоем на Netlify
    .venv/Scripts/python.exe -m scripts.whatsapp_worker --no-deploy

Останов — Ctrl+C. Лиды должны быть в CRM (их создаёт парсер/рассылка);
отправитель, которого нет в базе, игнорируется.
"""
from __future__ import annotations

import argparse
import time

from agents.sales_agent import greenapi
from agents.sales_agent.handler import process_incoming
from agents.sales_agent.messenger import set_sender
from agents import orchestrator


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-deploy", action="store_true", help="не деплоить на Netlify (site_url локальный)")
    args = ap.parse_args()
    deploy = not args.no_deploy

    # все исходящие (ответы + ссылка на демо) идут в реальный WhatsApp
    set_sender(greenapi.send_by_phone)
    print(f"WhatsApp-воркер запущен (deploy={deploy}). Ctrl+C для остановки.\n")

    # Дебаунс: копим быстрые сообщения клиента и обрабатываем как одно
    # после DEBOUNCE секунд тишины (как живой человек — ждём, пока допишут).
    DEBOUNCE = 4.0
    buffers: dict[str, dict] = {}  # phone -> {"parts": [...], "ts": float}

    while True:
        try:
            # 1) продвинуть конвейер (сборка сайтов, отправка ссылок)
            moved = orchestrator.poll_once(deploy=deploy)
            if moved.get("built") or moved.get("sent"):
                print(f"[конвейер] {moved}")

            # 2) забрать входящее сообщение -> в буфер (не отвечаем сразу)
            note = greenapi.receive_notification(receive_timeout=3)
            if note:
                receipt = note.get("receiptId")
                try:
                    parsed = greenapi.parse_incoming(note.get("body") or {})
                    if parsed:
                        phone, text = parsed
                        print(f"[вход] {phone}: {text}")
                        buf = buffers.setdefault(phone, {"parts": [], "ts": 0.0})
                        buf["parts"].append(text)
                        buf["ts"] = time.time()
                finally:
                    if receipt is not None:
                        greenapi.delete_notification(receipt)

            # 3) обработать буферы, где наступила тишина (склеив сообщения)
            now = time.time()
            for phone in list(buffers):
                buf = buffers[phone]
                if buf["parts"] and now - buf["ts"] >= DEBOUNCE:
                    combined = "\n".join(buf["parts"])
                    del buffers[phone]
                    reply = process_incoming(phone, combined)
                    if reply:
                        greenapi.send_by_phone(phone, reply)
                        print(f"[ответ] {phone}: {reply}")
                    else:
                        print(f"[пропуск] {phone} нет в CRM — игнор")

            if not note:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nОстановлен.")
            return 0
        except Exception as e:  # воркер не должен падать из-за одной ошибки
            print(f"[ошибка] {type(e).__name__}: {e}")
            time.sleep(3)


if __name__ == "__main__":
    raise SystemExit(main())
