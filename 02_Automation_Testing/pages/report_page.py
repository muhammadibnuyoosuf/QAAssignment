from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ReportPage:
    # dashboard tile that opens the report-type grid
    REPORTS_CARD = (By.XPATH, "//button[contains(., 'Reports')]")

    # intro modal shown before a report type's form
    START_REPORTING_BUTTON = (By.XPATH, "//button[contains(., 'Start Reporting')]")

    # "Report Submission Type" (anonymous) modal - default choice (No) is kept as-is
    SUBMISSION_NEXT_BUTTON = (By.XPATH, "//button[contains(., 'Next')]")

    DESCRIPTION_TEXTAREA = (
        By.XPATH,
        "//p[contains(text(), 'Description Of Observation')]/following::textarea[1]",
    )
    REVIEW_BUTTON = (By.XPATH, "//button[normalize-space(.)='Review']")
    SUBMIT_BUTTON = (By.XPATH, "//button[normalize-space(.)='Submit']")
    # same <style>/<script> exclusion as LoginPage.REPORTS_CARD - see that
    # locator's comment for why
    SUCCESS_MESSAGE = (
        By.XPATH,
        "//*[not(self::style or self::script)][contains(text(), 'Successfully submitted')]",
    )

    # the app blocks a report type once its monthly submission cap is hit,
    # showing this instead of the normal intro modal (e.g. "You have reached
    # your Positive Findings limit [4] for September 2026.")
    LIMIT_REACHED_MESSAGE = (
        By.XPATH,
        "//*[not(self::style or self::script)][contains(text(), 'You have reached your')]",
    )

    def __init__(self, driver, wait_seconds=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_seconds)

    def _click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def _report_type_tile(self, report_type_name):
        # report-type tiles share a common component class; matching on that
        # plus the visible label picks the exact tile without relying on the
        # per-build CSS hash suffix MUI/Next.js appends to class names
        return (
            By.XPATH,
            f"//a[contains(@class, 'homeReportTypeCard')][contains(., '{report_type_name}')]",
        )

    def _observation_tag(self, tag_name):
        return (By.XPATH, f"//li[text()='{tag_name}']")

    def open_reports(self):
        self._click(self.REPORTS_CARD)

    def select_report_type(self, report_type_name):
        self._click(self._report_type_tile(report_type_name))

        # the tile click leads to either the normal intro modal or, if the
        # monthly cap for this report type has been hit, a blocking message -
        # wait for whichever one actually shows up
        self.wait.until(
            EC.any_of(
                EC.visibility_of_element_located(self.START_REPORTING_BUTTON),
                EC.visibility_of_element_located(self.LIMIT_REACHED_MESSAGE),
            )
        )
        limit_message = self.driver.find_elements(*self.LIMIT_REACHED_MESSAGE)
        if limit_message:
            raise RuntimeError(
                "Report submission blocked by application limit: "
                f"{limit_message[0].text.strip()}"
            )

        self._click(self.START_REPORTING_BUTTON)
        self._click(self.SUBMISSION_NEXT_BUTTON)
        self.wait.until(EC.visibility_of_element_located(self.DESCRIPTION_TEXTAREA))

    def create_report(self, tag, description):
        self._click(self._observation_tag(tag))

        description_field = self.wait.until(
            EC.visibility_of_element_located(self.DESCRIPTION_TEXTAREA)
        )
        description_field.send_keys(description)

        self._click(self.REVIEW_BUTTON)
        self._click(self.SUBMIT_BUTTON)

    def is_report_created(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.SUCCESS_MESSAGE))
            return True
        except TimeoutException:
            return False
