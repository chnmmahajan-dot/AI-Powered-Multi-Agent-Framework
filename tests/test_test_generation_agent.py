
from agents.test_generation_agent import TestGenerationAgent


def test_generate_playwright_test_files(tmp_path):
    scenarios = [
        {
            "test_case_id": "US001_TC001",
            "scenario": "Verify successful login",
            "expected_result": "The dashboard should be visible.",
            "action": "valid_login",
        },
        {
            "test_case_id": "US002_TC001",
            "scenario": "Verify invalid login",
            "expected_result": "An error should appear.",
            "action": "invalid_login",
        },
        {
            "test_case_id": "US003_TC001",
            "scenario": "Verify logout",
            "expected_result": "The login screen should be visible.",
            "action": "logout",
        },
    ]

    agent = TestGenerationAgent(output_dir=str(tmp_path))
    generated_files = agent.generate_tests(scenarios)

    assert len(generated_files) == 3

    for file_path in generated_files:
        assert file_path.exists()
        assert file_path.suffix == ".py"

    login_content = generated_files[0].read_text(encoding="utf-8")
    invalid_content = generated_files[1].read_text(encoding="utf-8")
    logout_content = generated_files[2].read_text(encoding="utf-8")

    assert 'page.locator("#login-button").click()' in login_content
    assert 'page.locator("#error-message")' in invalid_content
    assert 'page.locator("#logout-button").click()' in logout_content

    assert "from playwright.sync_api import Page, expect" in login_content
