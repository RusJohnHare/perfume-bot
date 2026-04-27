import asyncio
import random
from decimal import Decimal

import httpx
from bs4 import BeautifulSoup

from perfume_bot.scrapers.base import AbstractScraper, OfferResult, ScraperBlockedError, ScraperParseError

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
]


class RandewooScraper(AbstractScraper):

    @property
    def shop_name(self) -> str:
        return "Randewoo"

    async def fetch_offer(self, url: str) -> OfferResult:
        await asyncio.sleep(1.0)  # соблюдаем задержку (Принцип VI)
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
        # Randewoo хранит цену в элементе с классом "price-block__final-price"
        el = soup.select_one(".price-block__final-price, [data-price], .product-price__value")
        if not el:
            raise ScraperParseError(self.shop_name, url, "Элемент цены не найден")
        raw = el.get_text(strip=True).replace("\xa0", "").replace(" ", "").replace("₽", "").replace(",", ".")
        try:
            return Decimal(raw)
        except Exception:
            raise ScraperParseError(self.shop_name, url, f"Не удалось распарсить цену: {raw!r}")

    def _extract_stock(self, soup: BeautifulSoup) -> bool:
        out_el = soup.select_one(".product-status--out, .out-of-stock")
        return out_el is None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        el = soup.select_one("h1")
        return el.get_text(strip=True) if el else "Неизвестно"

    async def search_perfume(self, name: str, brand: str) -> list[str]:
        await asyncio.sleep(1.0)
        query = f"{brand} {name}".replace(" ", "+")
        search_url = f"https://randewoo.ru/search?q={query}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(search_url, headers=headers)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("a.product-card__link")
        return [f"https://randewoo.ru{a['href']}" for a in links[:3] if a.get("href")]
