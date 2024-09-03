import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from loguru import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


@pytest.fixture
def driver():
    driver = webdriver.Remote(
        command_executor='http://192.168.0.105:4444/wd/hub',
        options=webdriver.ChromeOptions()
    )
    yield driver
    driver.quit()


@pytest.fixture
def wait_full_loading():
    def wait_for_full_page_load(driver, timeout=10):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "html"))
        )
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    return wait_for_full_page_load


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_element(self, by, value):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((by, value))
        )


class MainPage(BasePage):
    def open(self):
        self.driver.get("https://sbis.ru/")
        self.wait_for_element(By.TAG_NAME, "body")


class ContactsPage(BasePage):
    _contacts = []
    _region_code = None

    def open_contacts(self):
        contacts_link = self.driver.find_element(By.LINK_TEXT, "Контакты")
        contacts_link.click()
        self.wait_for_element(
            By.CSS_SELECTOR, "a.sbisru-Contacts__logo-tensor")

    def verify_geopos_link(self):
        geopos_link = self.driver.find_element(
            By.CSS_SELECTOR, "span.sbis_ru-Region-Chooser__text")

        response = requests.get('http://ipwho.is/?lang=ru')
        data = response.json()

        region = data.get('region')
        country = data.get('country_code')

        assert country == "RU", "Вы находитесь не в России."

        logger.info(f"Region: {region}")
        assert geopos_link.text.split()[0] in region, "Регион не совпадает."

    def verify_partners(self, first=True):
        partners_list = self.driver.find_element(
            By.CSS_SELECTOR, "div.sbisru-Contacts-List__col")

        assert partners_list != None, "Список партнеров не найден."

        partners_elements = partners_list.find_elements(
            By.CSS_SELECTOR, "div.sbisru-Contacts__text--md")

        if first:
            for partner in partners_elements:
                self._contacts.append(partner.text)
        else:
            contacts = []
            for partner in partners_elements:
                contacts.append(partner.text)

            assert contacts != self._contacts, "Список партнеров не изменился."

    def change_region(self):
        change_region_link = self.driver.find_element(
            By.CSS_SELECTOR, "span.sbis_ru-Region-Chooser__text")
        change_region_link.click()

        self.wait_for_element(By.CSS_SELECTOR, "div.sbis_ru-Region-Panel")

        region_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "li.sbis_ru-Region-Panel__item")
        for element in region_elements:
            if "Камчатский край" in element.text:
                element.click()
                self._region_code = element.text.split()[0]
                break

        assert "Камчатский край" in self.driver.title, "Регион не изменился в title."

        assert self._region_code not in self.driver.current_url, "Регион не изменился в url."


def test_second_scenario(driver, wait_full_loading):
    main_page = MainPage(driver)
    main_page.open()
    wait_full_loading(driver)

    contacts_page = ContactsPage(driver)
    contacts_page.open_contacts()
    wait_full_loading(driver)
    contacts_page.verify_geopos_link()
    contacts_page.verify_partners()
    contacts_page.change_region()
