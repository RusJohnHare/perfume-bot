from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OfferResult:
    shop_name: str
    perfume_name: str
    url: str
    price_rub: Decimal | None
    in_stock: bool


class ScraperError(Exception):
    def __init__(self, shop: str, url: str, reason: str) -> None:
        self.shop = shop
        self.url = url
        self.reason = reason
        super().__init__(f"[{shop}] {reason} — {url}")


class ScraperBlockedError(ScraperError):
    """Магазин вернул 403/429 или обнаружил бота."""


class ScraperParseError(ScraperError):
    """HTML получен, но цена не удалось извлечь."""


class AbstractScraper(ABC):

    @property
    @abstractmethod
    def shop_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_offer(self, url: str) -> OfferResult:
        """Получить актуальную цену и наличие по прямой ссылке."""
        ...

    @abstractmethod
    async def search_perfume(self, name: str, brand: str) -> list[str]:
        """Найти прямые URL товара по названию и бренду."""
        ...
