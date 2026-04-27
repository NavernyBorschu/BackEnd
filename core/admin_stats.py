from __future__ import annotations

import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django import get_version as get_django_version
from django.conf import settings


_PROCESS_START_MONO = time.monotonic()


@dataclass(frozen=True)
class AdminStats:
    generated_at_utc: datetime
    uptime_seconds: int
    python_version: str
    django_version: str
    debug: bool
    allowed_hosts: list[str]
    base_dir: str
    static_root: str | None
    media_root: str | None
    media_files_count: int | None
    media_total_bytes: int | None
    os_platform: str
    machine: str
    processor: str


def _dir_stats(path: Path) -> tuple[int, int]:
    files = 0
    total = 0
    for root, _dirs, filenames in os.walk(path):
        for name in filenames:
            files += 1
            fp = Path(root) / name
            try:
                total += fp.stat().st_size
            except OSError:
                # Файл міг бути видалений/недоступний під час обходу
                pass
    return files, total


def collect_admin_stats() -> AdminStats:
    now = datetime.now(timezone.utc)
    uptime = int(time.monotonic() - _PROCESS_START_MONO)

    media_root: str | None = str(settings.MEDIA_ROOT) if getattr(settings, "MEDIA_ROOT", None) else None
    static_root: str | None = str(settings.STATIC_ROOT) if getattr(settings, "STATIC_ROOT", None) else None

    media_files_count: int | None = None
    media_total_bytes: int | None = None
    if media_root:
        p = Path(media_root)
        if p.exists() and p.is_dir():
            media_files_count, media_total_bytes = _dir_stats(p)

    return AdminStats(
        generated_at_utc=now,
        uptime_seconds=uptime,
        python_version=sys.version.split()[0],
        django_version=get_django_version(),
        debug=bool(getattr(settings, "DEBUG", False)),
        allowed_hosts=list(getattr(settings, "ALLOWED_HOSTS", [])),
        base_dir=str(getattr(settings, "BASE_DIR", "")),
        static_root=static_root,
        media_root=media_root,
        media_files_count=media_files_count,
        media_total_bytes=media_total_bytes,
        os_platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor(),
    )


def as_template_context() -> dict[str, Any]:
    stats = collect_admin_stats()
    return {
        "stats": stats,
        "stats_nav_item": {
            "title": "Статистика",
            "url_name": "admin:stats",
        },
    }

