from pages.login_page import LoginPage
from pages.report_page import ReportPage


def test_crew_can_create_a_report(driver, config):
    username = config["app"]["username"]
    password = config["app"]["password"]
    report_type_name = config["report"]["report_type_name"]
    observation_tag = config["report"]["observation_tag"]
    description = config["report"]["description"]
    wait_seconds = config.getint("browser", "explicit_wait_seconds")

    login_page = LoginPage(driver, wait_seconds)
    login_page.login(username, password)
    assert login_page.is_logged_in(), "Crew user was not redirected to the dashboard after login"

    report_page = ReportPage(driver, wait_seconds)
    report_page.open_reports()
    report_page.select_report_type(report_type_name)
    report_page.create_report(tag=observation_tag, description=description)

    assert report_page.is_report_created(), "Report submission was not confirmed"
