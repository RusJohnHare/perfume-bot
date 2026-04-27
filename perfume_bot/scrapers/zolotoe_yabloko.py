import asyncio
import random
from decimal import Decimal

import httpx
from bs4 import BeautifulSoup

from perfume_bot.scrapers.base import AbstractScraper, OfferResult, ScraperBlockedError, ScraperParseError

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
]


class ZolotoeYablokoScraper(AbstractScraper):

    @property
    def shop_name(self) -> str:
        return "Золотое Яблоко"

    async def fetch_offer(self, url: str) -> OfferResult:
        await asyncio.sleep(1.0)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(url, headers=headers)
        if response.status_code in (403, 429):
            raise ScraperBlockedError(self.shop_name, url, f"HTTP {response.status_code}")
        if response.status_code != 200:
            raise ScraperBlockedError(self.shop_name, url, f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        price = self._extract_price(soup, url)
        in_stock = self._extract_stock(soup)
        return OfferResult(
            shop_name=self.shop_name,
            perfume_name=self._extract_name(soup),
            url=url,
            price_rub=price,
            in_stock=in_stock,
        )

    def _extract_price(self, soup: BeautifulSoup, url: str) -> Decimal | None:
        el = soup.select_one(".ga-price, .price-value, [class*='price']")
        if not el:
            raise ScraperParseError(self.shop_name, url, "Элемент цены не найден")
        raw = el.get_text(strip=True).replace("\xa0", "").replace(" ", "").replace("₽", "").replace(",", ".")
        try:
            return Decimal(raw)
        except Exception:
            raise ScraperParseError(self.shop_name, url, f"Не удалось распарсить цену: {raw!r}")

    def _extract_stock(self, soup: BeautifulSoup) -> bool:
        out_el = soup.select_one(".not-available, .out-of-stock")
        return out_el is None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        el = soup.select_one("h1")
        return el.get_text(strip=True) if el else "Неизвестно"

    async def search_perfume(self, name: str, brand: str) -> list[str]:
        return []
