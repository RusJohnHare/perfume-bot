import asyncio
import logging

from perfume_bot.workers.app import app

logger = logging.getLogger(__name__)


@app.task(name="perfume_bot.workers.notifier.notify_user", bind=True, max_retries=3)
def notify_user(self, tg_user_id: int, text: str) -> None:
    async def _send() -> None:
        from perfume_bot.services.notification import NotificationService
        svc = NotificationService()
        await svc.send(tg_user_id, text)

    try:
        asyncio.run(_send())
    except Exception as exc:
        logger.error("Ошибка отправки уведомления tg_user_id=%s: %s", tg_user_id, exc)
        raise self.retry(exc=exc, countdown=60)
