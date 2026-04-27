import asyncio
import logging

from perfume_bot.workers.app import app

logger = logging.getLogger(__name__)


@app.task(name="perfume_bot.workers.catalog_updater.update_catalog")
def update_catalog() -> None:
    """Инкрементальное обновление каталога — заглушка для MVP."""
    logger.info("update_catalog: MVP использует статический датасет; живое обновление в Phase 4+")
