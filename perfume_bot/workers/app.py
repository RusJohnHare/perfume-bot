from celery import Celery
from celery.schedules import crontab

from perfume_bot.core.config import settings

app = Celery("perfume_bot")
app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
    task_routes={
        "perfume_bot.workers.price_checker.check_prices": {"queue": "prices"},
        "perfume_bot.workers.notifier.notify_user": {"queue": "notifications"},
        "perfume_bot.workers.catalog_updater.update_catalog": {"queue": "catalog"},
    },
    beat_schedule={
        "check-prices-every-6h": {
            "task": "perfume_bot.workers.price_checker.check_prices",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "update-catalog-daily": {
            "task": "perfume_bot.workers.catalog_updater.update_catalog",
            "schedule": crontab(minute=0, hour=3),
        },
    },
)
