from __future__ import annotations

from django.contrib import admin
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path

from .admin_stats import as_template_context
from .admin_analytics import build_analytics_payload


def admin_stats_view(request):
    context = {
        **admin.site.each_context(request),
        **as_template_context(),
        "title": "Статистика",
    }
    return TemplateResponse(request, "admin/stats.html", context)


def admin_analytics_view(request):
    context = {
        **admin.site.each_context(request),
        "title": "Аналітика",
        "analytics_nav_item": {
            "title": "Аналітика",
            "url_name": "admin:analytics",
        },
    }
    return TemplateResponse(request, "admin/analytics.html", context)


def admin_analytics_data(request):
    try:
        days = int(request.GET.get("days", "30"))
    except ValueError:
        days = 30
    days = max(1, min(days, 365))
    return JsonResponse(build_analytics_payload(days=days))


def _patch_admin_urls():
    original_get_urls = admin.site.get_urls

    def get_urls():
        urls = original_get_urls()
        custom = [
            path(
                "analytics/",
                admin.site.admin_view(admin_analytics_view),
                name="analytics",
            ),
            path(
                "analytics/data/",
                admin.site.admin_view(admin_analytics_data),
                name="analytics-data",
            ),
            path(
                "stats/",
                admin.site.admin_view(admin_stats_view),
                name="stats",
            ),
        ]
        return custom + urls

    admin.site.get_urls = get_urls


_patch_admin_urls()

