# Контракт скрапера

**Дата**: 2026-04-27

Каждый скрапер магазина ДОЛЖЕН реализовывать абстрактный базовый класс `AbstractScraper`.
Класс определяется в `perfume_bot/scrapers/base.py`.

---

## Интерфейс

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class OfferResult:
    """Результат одной проверки цены."""
    shop_name: str           # название магазина (совпадает с Shop.name в БД)
    perfume_name: str        # для логирования; не пишется в БД
    url: str                 # прямая ссылка на страницу товара
    price_rub: Decimal | None  # None если цена не найдена
    in_stock: bool

class AbstractScraper(ABC):

    @property
    @abstractmethod
    def shop_name(self) -> str:
        """Должно совпадать с Shop.name в таблице shops."""
        ...

    @abstractmethod
    async def fetch_offer(self, url: str) -> OfferResult:
        """
        Получить актуальную цену и наличие по прямой ссылке на товар.
        - Должен соблюдать задержку ≥ 1 с между запросами к домену.
        - Должен применять ротацию User-Agent.
        - При любой ошибке HTTP (не 2xx) — выбрасывать ScraperError.
        """
        ...

    @abstractmethod
    async def search_perfume(self, name: str, brand: str) -> list[str]:
        """
        Найти прямые URL товара по названию и бренду.
        Возвращает список ссылок (может быть пустым).
        """
        ...
```

---

## Исключения

```python
class ScraperError(Exception):
    """Базовое исключение скрапера."""
    def __init__(self, shop: str, url: str, reason: str):
        self.shop = shop
        self.url = url
        self.reason = reason
        super().__init__(f"[{shop}] {reason} — {url}")

class ScraperBlockedError(ScraperError):
    """Магазин вернул 403/429 или обнаружил бота."""
    ...

class ScraperParseError(ScraperError):
    """HTML получен, но цена не удалось извлечь."""
    ...
```

---

## Правила circuit breaker

- Счётчик ошибок хранится в Redis: `scraper:{shop_name}:fail_count` (TTL 2 ч).
- При каждом `ScraperError` счётчик инкрементируется.
- При `fail_count ≥ 5` скрапер выставляет `scraper:{shop_name}:paused_until = now() + 3600`.
- При успешном `fetch_offer` счётчик сбрасывается.
- Перед каждым вызовом `fetch_offer` воркер проверяет флаг паузы; при активной паузе —
  пропускает магазин и логирует событие уровня WARNING.

---

## Требования к тестам

- Для каждого скрапера ДОЛЖЕН существовать файл `tests/contract/test_{shop}.py`.
- Тест ДОЛЖЕН загружать HTML-фикстуру из `fixtures/html/{shop}_product.html` и мокать
  HTTP-клиент — реальные сетевые запросы в тестах запрещены.
- Тест ДОЛЖЕН проверять: корректное извлечение цены, корректное поле `in_stock`,
  выброс `ScraperParseError` при битом HTML.
