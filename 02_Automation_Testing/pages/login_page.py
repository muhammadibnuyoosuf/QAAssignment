from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class LoginPage:
    USERNAME_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.XPATH, "//button[@type='submit' and contains(., 'LOGIN')]")

    # confirms the crew dashboard actually loaded after login
    # (excludes <style>/<script>, whose raw text can coincidentally contain
    # this substring and would otherwise be matched as the first, invisible,
    # hit for a plain "//*[contains(text(), ...)]" locator)
    REPORTS_CARD = (
        By.XPATH,
        "//*[not(self::style or self::script)][contains(text(), 'Reports')]",
    )

    def __init__(self, driver, wait_seconds=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_seconds)

    def enter_username(self, username):
        field = self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT))
        field.clear()
        field.send_keys(username)

    def enter_password(self, password):
        field = self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))
        field.clear()
        field.send_keys(password)

    def click_login(self):
        self.wait.until(EC.element_to_be_clickable(self.LOGIN_BUTTON)).click()

    def login(self, username, password):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def is_logged_in(self):
        try:
            self.wait.until(EC.url_contains("/reporting-tool/dashboard"))
            self.wait.until(EC.visibility_of_element_located(self.REPORTS_CARD))
            return True
        except TimeoutException:
            return False
