"""Деплой готового index.html на Netlify через их API.

Создаёт новый сайт (уникальный поддомен *.netlify.app) и заливает один файл.
Возвращает публичный URL. Требует NETLIFY_AUTH_TOKEN.
"""
from __future__ import annotations

import hashlib
import time

import httpx

from shared.config import settings

API = "https://api.netlify.com/api/v1"


def _headers() -> dict[str, str]:
    settings.require("NETLIFY_AUTH_TOKEN")
    return {"Authorization": f"Bearer {settings.NETLIFY_AUTH_TOKEN}"}


def deploy_to_netlify(html: str, *, name: str | None = None, timeout: float = 60.0) -> str:
    """Задеплоить одностраничный сайт. Возвращает https://<...>.netlify.app.

    name — желаемое имя сайта (Netlify добавит суффикс, если занято). Если None —
    Netlify выдаст случайное имя.
    """
    hdr = _headers()
    body_bytes = html.encode("utf-8")
    sha1 = hashlib.sha1(body_bytes).hexdigest()

    with httpx.Client(timeout=timeout) as c:
        # 1) создать сайт
        payload = {"name": name} if name else {}
        r = c.post(f"{API}/sites", headers=hdr, json=payload)
        r.raise_for_status()
        site = r.json()
        site_id = site["id"]
        site_url = site.get("ssl_url") or site.get("url")

        # 2) объявить деплой с одним файлом (digest-метод)
        r = c.post(
            f"{API}/sites/{site_id}/deploys",
            headers=hdr,
            json={"files": {"/index.html": sha1}},
        )
        r.raise_for_status()
        deploy = r.json()
        deploy_id = deploy["id"]

        # 3) если файл требуется загрузить — заливаем тело
        required = deploy.get("required", [])
        if sha1 in required:
            up = c.put(
                f"{API}/deploys/{deploy_id}/files/index.html",
                headers={**hdr, "Content-Type": "application/octet-stream"},
                content=body_bytes,
            )
            up.raise_for_status()

        # 4) ждём, пока деплой станет ready
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = c.get(f"{API}/deploys/{deploy_id}", headers=hdr)
            r.raise_for_status()
            state = r.json().get("state")
            if state == "ready":
                break
            if state == "error":
                raise RuntimeError("Netlify deploy failed (state=error)")
            time.sleep(2)

    return site_url
