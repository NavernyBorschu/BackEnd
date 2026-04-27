from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Borsch, FavoriteBorsch, Place, Review


@dataclass(frozen=True)
class TimeSeries:
    labels: list[str]
    values: list[int]


def _date_range(days: int) -> list[date]:
    days = max(1, min(int(days), 365))
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    return [start + timedelta(days=i) for i in range(days)]


def _fill_series(days: list[date], rows: list[dict[str, Any]], key: str = "day") -> TimeSeries:
    by_day: dict[date, int] = {r[key]: int(r["c"]) for r in rows}
    labels = [d.isoformat() for d in days]
    values = [by_day.get(d, 0) for d in days]
    return TimeSeries(labels=labels, values=values)


def _series_users_new(days: list[date]) -> TimeSeries:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    rows = (
        User.objects.filter(date_joined__gte=start_dt)
        .annotate(day=TruncDate("date_joined"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    return _fill_series(days, list(rows))


def _series_reviews(days: list[date]) -> TimeSeries:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    rows = (
        Review.objects.filter(created_at__gte=start_dt)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    return _fill_series(days, list(rows))


def _series_favorites(days: list[date]) -> TimeSeries:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    rows = (
        FavoriteBorsch.objects.filter(added_at__gte=start_dt)
        .annotate(day=TruncDate("added_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    return _fill_series(days, list(rows))


def _series_places(days: list[date]) -> TimeSeries:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    rows = (
        Place.objects.filter(created_at__gte=start_dt)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    return _fill_series(days, list(rows))


def _series_borsches(days: list[date]) -> TimeSeries:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    rows = (
        Borsch.objects.filter(created_at__gte=start_dt)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    return _fill_series(days, list(rows))


def _top_cities_reviews(days: list[date], limit: int = 12) -> list[dict[str, Any]]:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    qs = (
        Review.objects.filter(created_at__gte=start_dt)
        .values("borsch__place__city")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    out: list[dict[str, Any]] = []
    for r in qs[:limit]:
        out.append({"city": r["borsch__place__city"] or "—", "count": int(r["c"])})
    return out


def _top_cities_favorites(days: list[date], limit: int = 12) -> list[dict[str, Any]]:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    qs = (
        FavoriteBorsch.objects.filter(added_at__gte=start_dt)
        .values("borsch__place__city")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    out: list[dict[str, Any]] = []
    for r in qs[:limit]:
        out.append({"city": r["borsch__place__city"] or "—", "count": int(r["c"])})
    return out


def _top_cities_places(days: list[date], limit: int = 12) -> list[dict[str, Any]]:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    qs = (
        Place.objects.filter(created_at__gte=start_dt)
        .values("city")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    return [{"city": r["city"] or "—", "count": int(r["c"])} for r in qs[:limit]]


def _top_cities_borsches(days: list[date], limit: int = 12) -> list[dict[str, Any]]:
    start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
    qs = (
        Borsch.objects.filter(created_at__gte=start_dt)
        .values("place__city")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    return [{"city": r["place__city"] or "—", "count": int(r["c"])} for r in qs[:limit]]


def build_analytics_payload(days: int = 30) -> dict[str, Any]:
    dr = _date_range(days)

    users_new = _series_users_new(dr)
    reviews = _series_reviews(dr)
    favorites = _series_favorites(dr)
    places = _series_places(dr)
    borsches = _series_borsches(dr)

    return {
        "days": len(dr),
        "labels": users_new.labels,
        "series": {
            "users_new": users_new.values,
            "reviews": reviews.values,
            "favorites": favorites.values,
            "places": places.values,
            "borsches": borsches.values,
        },
        "top_cities": {
            "reviews": _top_cities_reviews(dr),
            "favorites": _top_cities_favorites(dr),
            "places": _top_cities_places(dr),
            "borsches": _top_cities_borsches(dr),
        },
        "generated_at": timezone.now().isoformat(),
    }

