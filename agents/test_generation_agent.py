from pathlib import Path
import re

from config.settings import BASE_URL

class TestGenerationAgent:
    """Generates executable Playwright tests from test scenarios."""

    __test__ = False

    def __init__(
    self,
    output_dir: str = "generated_tests",
    base_url: str = BASE_URL
):
        self.output_dir = Path(output_dir)
        self.base_url = base_url

    def generate_tests(self, scenarios: list[dict]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Remove previously generated test files
        for old_file in self.output_dir.glob("test_*.py"):
            old_file.unlink()

        generated_files = []

        for scenario in scenarios:
            test_id = scenario["test_case_id"]

            safe_test_id = re.sub(
                r"[^a-zA-Z0-9_]", "_", test_id
            )

            file_path = (
                self.output_dir / f"test_{safe_test_id.lower()}.py"
            )

            test_code = self._create_test_code(scenario)

            file_path.write_text(test_code, encoding="utf-8")
            generated_files.append(file_path)

        return generated_files

    def _create_test_code(self, scenario: dict) -> str:
        action = scenario["action"]
        test_id = scenario["test_case_id"].lower()

        test_templates = {
            "valid_login": '''
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("password123")
    page.locator("#login-button").click()

    expect(page.locator("#dashboard")).to_be_visible()
    expect(page.locator("#welcome-message")).to_contain_text(
        "successfully logged in"
    )
''',

            "invalid_login": '''
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("wrong123")
    page.locator("#login-button").click()

    expect(page.locator("#error-message")).to_have_text(
        "Invalid username or password"
    )
    expect(page.locator("#dashboard")).to_be_hidden()
''',

            "logout": '''
    page.goto(BASE_URL)

    page.locator("#username").fill("admin")
    page.locator("#password").fill("password123")
    page.locator("#login-button").click()

    expect(page.locator("#dashboard")).to_be_visible()

    page.locator("#logout-button").click()

    expect(page.locator("#login-container")).to_be_visible()
    expect(page.locator("#dashboard")).to_be_hidden()
'''
        }

        if action not in test_templates:
            raise ValueError(f"Unsupported test action: {action}")

        return f'''from playwright.sync_api import Page, expect

BASE_URL = {self.base_url!r}


def test_{test_id}(page: Page):
    """
    Test scenario: {scenario["scenario"]}
    Expected result: {scenario["expected_result"]}
    """
{test_templates[action]}
'''