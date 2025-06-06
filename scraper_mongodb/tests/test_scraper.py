import sys
import os
import importlib
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import TimeoutException
import pytest
from types import ModuleType
from _pytest.capture import CaptureFixture


# Set the path to import the scraper module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


@pytest.fixture
def scraper_module() -> ModuleType:
    """
    Pytest fixture to import and reload the scraper module before each test.

    Returns:
        ModuleType: The imported and reloaded scraper module.
    """
    import scraper_mongodb.aruodas_scraper as scraper
    importlib.reload(scraper)
    return scraper


@pytest.mark.parametrize("page_url, expected_saved_props_count, expected_output_substr", [
    ("puslapis/1", 3, "No cookie popup or already accepted."),
])
def test_scraper(
    scraper_module: ModuleType,
    capfd: CaptureFixture,
    page_url: str,
    expected_saved_props_count: int,
    expected_output_substr: str
) -> None:
    """
    Test the main scraping logic for various HTML conditions:
    - Normal listing
    - Missing title in <img>
    - Incomplete listing (missing rooms)
    - Handles cookie popup logic

    Asserts that the number of saved properties matches expectations and expected output appears in console.

    Args:
        scraper_module (ModuleType): The imported scraper module.
        capfd (CaptureFixture): Captures printed output during test.
        page_url (str): The test page path.
        expected_saved_props_count (int): Expected number of calls to `save_property`.
        expected_output_substr (str): Substring expected to appear in stdout.
    """
    from selenium.webdriver.common.by import By

    fake_html_page_1 = """    
    <div class="list-row-v2 object-row selflat advert">
        <div class="advert-flex">
            <a href="/butas-vilniuje-parduodamas-12345/">
                <img title="Vilnius, Senamiestis, Pilies g." />
            </a>
            <span class="list-item-price-v2">150 000 €</span>
            <span class="price-pm-v2">3 000 €/m²</span>
            <div class="list-RoomNum-v2 list-detail-v2">2</div>
            <div class="list-AreaOverall-v2 list-detail-v2">50</div>
        </div>
    </div>
    """

    fake_html_missing_title = """
    <div class="list-row-v2 object-row selflat advert">
        <div class="advert-flex">
            <a href="/butas-vilniuje-parduodamas-12345/">
                <img/>
            </a>
            <span class="list-item-price-v2">150 000 €</span>
            <span class="price-pm-v2">3 000 €/m²</span>
            <div class="list-RoomNum-v2 list-detail-v2">2</div>
            <div class="list-AreaOverall-v2 list-detail-v2">50</div>
        </div>
    </div>
    """

    fake_html_incomplete_listing = """
    <div class="advert-flex">
        <a href="/some-url"><img title="Vilnius, Naujamiestis, Mainų g."/></a>
        <span class="list-item-price-v2">€120 000</span>
        <span class="price-pm-v2">3000 €/m²</span>
        <div class="list-AreaOverall-v2 list-detail-v2">40</div>
    </div>
    """

    mock_driver = MagicMock()
    current_url = {"value": ""}

    def mock_get(url: str) -> None:
        current_url["value"] = url
        if "puslapis/2" in url:
            mock_driver.page_source = fake_html_missing_title
        elif "puslapis/3" in url:
            mock_driver.page_source = fake_html_incomplete_listing
        elif "puslapis/4" in url:
            mock_driver.page_source = fake_html_page_1
        elif "puslapis/5" in url:
            mock_driver.page_source = "<html><body></body></html>"
        elif "puslapis/6" in url:
            raise TimeoutException("Listings did not load")
        else:
            mock_driver.page_source = fake_html_page_1

    mock_driver.get.side_effect = mock_get

    with patch("scraper_mongodb.aruodas_scraper.save_property", autospec=True) as mock_save_property, \
         patch("scraper_mongodb.aruodas_scraper.webdriver.Chrome") as mock_webdriver:

        mock_webdriver.return_value = mock_driver
        mock_element = MagicMock()
        mock_element.click.return_value = None

        def fake_element_to_be_clickable(locator):
            def _condition(driver):
                if "puslapis/1" in current_url["value"] and locator == (By.ID, "onetrust-accept-btn-handler"):
                    raise Exception("No cookie popup")
                return mock_element
            return _condition

        def fake_until(self, condition):
            return condition(mock_driver)

        with patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.WebDriverWait.until", new=fake_until), \
             patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.EC.element_to_be_clickable",
                   side_effect=fake_element_to_be_clickable):
            scraper_module.scrape_aruodas()

    captured = capfd.readouterr()
    assert expected_output_substr in captured.out
    assert mock_save_property.call_count == expected_saved_props_count


def test_scraper_timeout_exception_handling(scraper_module: ModuleType, capfd: CaptureFixture) -> None:
    """
    Test that TimeoutException is caught and handled without crashing the scraper.

    Args:
        scraper_module (ModuleType): The imported scraper module.
        capfd (CaptureFixture): Captures printed output during test.
    """
    with patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.save_property", autospec=True), \
         patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.webdriver.Chrome") as mock_webdriver:
        mock_driver = MagicMock()
        current_url = {"value": ""}

        def mock_get(url: str) -> None:
            current_url["value"] = url
            if "puslapis/3" in url:
                raise TimeoutException("Listings did not load")
            mock_driver.page_source = "<html><body><div class='listing'>Listing</div></body></html>"

        mock_driver.get.side_effect = mock_get
        mock_webdriver.return_value = mock_driver

        mock_element = MagicMock()
        mock_element.click.return_value = None

        def mock_wait(*args, **kwargs):
            class DummyWait:
                def until(self, condition):
                    return mock_element
            return DummyWait()

        with patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.WebDriverWait", mock_wait):
            scraper_module.scrape_aruodas()


def test_scraper_timeout_exception_breaks_loop(scraper_module: ModuleType, capfd: CaptureFixture) -> None:
    """
    Test that the scraper stops when a TimeoutException is encountered during a page load.

    Args:
        scraper_module (ModuleType): The imported scraper module.
        capfd (CaptureFixture): Captures printed output during test.
    """
    fake_html_page_1 = """    
    <div class="list-row-v2 object-row selflat advert">
        <div class="advert-flex">
            <a href="/butas-vilniuje-parduodamas-12345/">
                <img title="Vilnius, Senamiestis, Pilies g." />
            </a>
            <span class="list-item-price-v2">150 000 €</span>
            <span class="price-pm-v2">3 000 €/m²</span>
            <div class="list-RoomNum-v2 list-detail-v2">2</div>
            <div class="list-AreaOverall-v2 list-detail-v2">50</div>
        </div>
    </div>
    """

    mock_driver = MagicMock()
    current_url = {"value": ""}

    def mock_get(url: str) -> None:
        current_url["value"] = url
        if "puslapis/2" in url:
            raise TimeoutException("Listings did not load")
        mock_driver.page_source = fake_html_page_1

    mock_driver.get.side_effect = mock_get

    with patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.webdriver.Chrome", return_value=mock_driver), \
         patch("Aruodas_web_scrape_project.scraper_mongodb.aruodas_scraper.save_property", autospec=True):
        scraper_module.scrape_aruodas()

    captured = capfd.readouterr()
    assert "Page failed to load or no listings found." in captured.out