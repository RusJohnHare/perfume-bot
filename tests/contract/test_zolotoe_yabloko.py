from decimal import Decimal
from pathlib import Path

import pytest
import respx
import httpx

from perfume_bot.scrapers.base import ScraperParseError
from perfume_bot.scrapers.zolotoe_yabloko import ZolotoeYablokoScraper

FIXTURE = (Path(__file__).parent.parent.parent / "fixtures/html/zolotoe_yabloko_product.html").read_text()
BROKEN_HTML = "<html><body><h1>Нет цены</h1></body></html>"
URL = "https://goldapple.ru/product/ysl-black-opium"


@pytest.fixture
def scraper():
    return ZolotoeYablokoScraper()


@respx.mock
async def test_extracts_price(scraper: ZolotoeYablokoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=FIXTURE))
    result = await scraper.fetch_offer(URL)
    assert result.price_rub == Decimal("6200")
    assert result.shop_name == "Золотое Яблоко"


@respx.mock
async def test_in_stock_true(scraper: ZolotoeYablokoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=FIXTURE))
    result = await scraper.fetch_offer(URL)
    assert result.in_stock is True


@respx.mock
async def test_parse_error_on_broken_html(scraper: ZolotoeYablokoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=BROKEN_HTML))
    with pytest.raises(ScraperParseError):
        await scraper.fetch_offer(URL)
