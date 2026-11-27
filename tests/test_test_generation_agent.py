from agents.test_generation_agent import TestGenerationAgent


def test_generate_playwright_test_files(tmp_path):
    scenarios = [
        {
            "test_case_id": "US001_TC001",
            "scenario": "Verify successful Login",
            "expected_result": "User should successfully log in.",
        },
        {
            "test_case_id": "US001_TC002",
            "scenario": "Verify invalid Login",
            "expected_result": "Invalid credentials should be rejected.",
        },
    ]

    agent = TestGenerationAgent(output_dir=str(tmp_path))
    generated_files = agent.generate_tests(scenarios)

    # Verify that two files were generated.
    assert len(generated_files) == 2

    # Verify that the generated files exist.
    assert generated_files[0].exists()
    assert generated_files[1].exists()

    # Verify the generated test content.
    content = generated_files[0].read_text(encoding="utf-8")

    assert "def test_us001_tc001(page: Page):" in content
    assert "Verify successful Login" in content
    assert "User should successfully log in." in content
    assert "from playwright.sync_api import Page" in content