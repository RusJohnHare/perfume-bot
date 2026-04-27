from decimal import Decimal
from pathlib import Path

import pytest
import respx
import httpx

from perfume_bot.scrapers.base import ScraperParseError
from perfume_bot.scrapers.notino import NotinoScraper

FIXTURE = (Path(__file__).parent.parent.parent / "fixtures/html/notino_product.html").read_text()
BROKEN_HTML = "<html><body><h1>Нет цены</h1></body></html>"
URL = "https://www.notino.ru/product/dior-sauvage"


@pytest.fixture
def scraper():
    return NotinoScraper()


@respx.mock
async def test_extracts_price(scraper: NotinoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=FIXTURE))
    result = await scraper.fetch_offer(URL)
    assert result.price_rub == Decimal("7450")
    assert result.shop_name == "Notino"


@respx.mock
async def test_in_stock_true(scraper: NotinoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=FIXTURE))
    result = await scraper.fetch_offer(URL)
    assert result.in_stock is True


@respx.mock
async def test_parse_error_on_broken_html(scraper: NotinoScraper):
    respx.get(URL).mock(return_value=httpx.Response(200, text=BROKEN_HTML))
    with pytest.raises(ScraperParseError):
        await scraper.fetch_offer(URL)
