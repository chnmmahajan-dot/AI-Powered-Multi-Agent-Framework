
from pathlib import Path
import re

from config.settings import BASE_URL


class TestGenerationAgent:
    """Generates executable Playwright tests from validated scenarios."""

    __test__ = False

    SUPPORTED_ACTIONS = {
        "valid_login",
        "invalid_login",
        "logout",
    }

    def __init__(
        self,
        output_dir: str = "generated_tests",
        base_url: str = BASE_URL
    ):
        self.output_dir = Path(output_dir)
        self.base_url = base_url

    def generate_tests(self, scenarios: list[dict]) -> list[Path]:
        if not scenarios:
            return []

        # Validate all scenarios before modifying existing files.
        self._validate_scenarios(scenarios)

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

            generated_files.append((file_path, test_code))

        # Write files only after all test code has been generated.
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for old_file in self.output_dir.glob("test_*.py"):
            old_file.unlink()

        generated_paths = []

        for file_path, test_code in generated_files:
            file_path.write_text(test_code, encoding="utf-8")
            generated_paths.append(file_path)

        return generated_paths

    def _validate_scenarios(self, scenarios: list[dict]) -> None:
        seen_test_ids = set()

        for index, scenario in enumerate(scenarios, start=1):
            if not isinstance(scenario, dict):
                raise ValueError(
                    f"Scenario {index} must be a dictionary."
                )

            required_fields = [
                "test_case_id",
                "scenario",
                "expected_result",
                "action",
            ]

            missing_fields = [
                field for field in required_fields
                if not str(scenario.get(field, "")).strip()
            ]

            if missing_fields:
                raise ValueError(
                    f"Scenario {index} is missing required fields: "
                    f"{missing_fields}"
                )

            action = str(scenario["action"]).strip().lower()

            if action not in self.SUPPORTED_ACTIONS:
                raise ValueError(
                    f"Unsupported test action '{action}' in scenario "
                    f"'{scenario['test_case_id']}'."
                )

            test_id = str(scenario["test_case_id"]).strip().lower()

            if test_id in seen_test_ids:
                raise ValueError(
                    f"Duplicate test case ID found: {test_id}"
                )

            seen_test_ids.add(test_id)

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

        return f'''from playwright.sync_api import Page, expect

BASE_URL = {self.base_url!r}


def test_{test_id}(page: Page):
    """
    Test scenario: {scenario["scenario"]}
    Expected result: {scenario["expected_result"]}
    """
{test_templates[action]}
'''
