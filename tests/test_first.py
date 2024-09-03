import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from loguru import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger.add("file_{time}.log")


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
    def open_contacts(self):
        contacts_link = self.driver.find_element(By.LINK_TEXT, "Контакты")
        contacts_link.click()
        self.wait_for_element(
            By.CSS_SELECTOR, "a.sbisru-Contacts__logo-tensor")

    def get_tensor_logo_link(self):
        tensor_logo = self.driver.find_element(
            By.CSS_SELECTOR, "a.sbisru-Contacts__logo-tensor")
        return tensor_logo.get_attribute("href")


class AboutPage(BasePage):
    def verify_paragraph(self):
        paragraph = self.driver.find_element(
            By.XPATH, "//p[contains(text(), 'Сила в людях')]")
        assert "Сила в людях" in paragraph.text
        return paragraph

    def verify_more_info_link(self, paragraph):
        parent_div = paragraph.find_element(By.XPATH, "..")
        more_info_link = parent_div.find_element(By.LINK_TEXT, "Подробнее")
        assert more_info_link.get_attribute("href").split("/")[-1] == "about"
        return more_info_link.get_attribute("href")

    def verify_images(self):
        h2_element = self.driver.find_element(
            By.XPATH, "//h2[contains(text(), 'Работаем')]")
        parent_parent_element = h2_element.find_element(By.XPATH, "../..")
        images = parent_parent_element.find_elements(By.TAG_NAME, "img")

        first_img = images[0]
        first_width = first_img.get_attribute("width")
        first_height = first_img.get_attribute("height")

        for i, img in enumerate(images):
            width = img.get_attribute("width")
            height = img.get_attribute("height")
            logger.info(f"Image {i}: width={width}, height={height}")
            assert width == first_width
            assert height == first_height


def test_first_scenario(driver, wait_full_loading):
    main_page = MainPage(driver)
    main_page.open()
    wait_full_loading(driver)

    contacts_page = ContactsPage(driver)
    contacts_page.open_contacts()
    link = contacts_page.get_tensor_logo_link()

    driver.get(link)
    wait_full_loading(driver)

    about_page = AboutPage(driver)
    paragraph = about_page.verify_paragraph()
    more_info_link = about_page.verify_more_info_link(paragraph)

    driver.get(more_info_link)
    wait_full_loading(driver)

    about_page.verify_images()
