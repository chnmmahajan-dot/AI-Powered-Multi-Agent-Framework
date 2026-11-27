
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8000"


def test_valid_login(page: Page):
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("password123")

    page.locator("#login-button").click()

    expect(page.locator("#dashboard")).to_be_visible()
    expect(page.locator("#welcome-message")).to_contain_text(
        "successfully logged in"
    )


def test_invalid_login(page: Page):
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("wrong123")

    page.locator("#login-button").click()

    expect(page.locator("#error-message")).to_have_text(
        "Invalid username or password"
    )

    expect(page.locator("#dashboard")).to_be_hidden()


def test_logout(page: Page):
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("password123")

    page.locator("#login-button").click()

    expect(page.locator("#dashboard")).to_be_visible()

    page.locator("#logout-button").click()

    expect(page.locator("#login-container")).to_be_visible()
    expect(page.locator("#dashboard")).to_be_hidden()
