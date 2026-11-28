
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.browser_executor import BrowserExecutor


@pytest.fixture
def mock_page():
    """Create a simulated Playwright page."""
    page = MagicMock()
    page.url = "http://127.0.0.1:8000/"
    page.title.return_value = "Multi-Agent Automation Demo"
    return page


@pytest.fixture
def executor(mock_page, tmp_path):
    """Create the browser executor using the simulated page."""
    return BrowserExecutor(
        mock_page,
        artifacts_dir=str(tmp_path / "artifacts"),
    )


def test_navigate_action(executor, mock_page):
    step = {
        "action": "navigate",
        "url": "http://127.0.0.1:8000",
    }

    result = executor.execute_step(step)

    mock_page.goto.assert_called_once_with(
        "http://127.0.0.1:8000",
        wait_until="domcontentloaded",
        timeout=5000,
    )

    assert result["status"] == "passed"
    assert result["action"] == "navigate"


def test_fill_action(executor, mock_page):
    step = {
        "action": "fill",
        "target": {
            "by": "label",
            "value": "Username",
        },
        "value": "admin",
    }

    result = executor.execute_step(step)

    mock_page.get_by_label.assert_called_once_with(
        "Username",
        exact=False,
    )

    mock_page.get_by_label.return_value.fill.assert_called_once_with(
        "admin",
        timeout=5000,
    )

    assert result["status"] == "passed"


def test_click_action(executor, mock_page):
    step = {
        "action": "click",
        "target": {
            "by": "role",
            "role": "button",
            "value": "Login",
        },
    }

    result = executor.execute_step(step)

    mock_page.get_by_role.assert_called_once_with(
        "button",
        name="Login",
        exact=False,
    )

    mock_page.get_by_role.return_value.click.assert_called_once_with(
        timeout=5000,
    )

    assert result["status"] == "passed"


def test_verify_text_action(executor, mock_page):
    step = {
        "action": "verify_text",
        "expected": "Dashboard",
    }

    result = executor.execute_step(step)

    mock_page.get_by_text.assert_called_once_with("Dashboard")

    mock_page.get_by_text.return_value.first.wait_for.assert_called_once_with(
        state="visible",
        timeout=5000,
    )

    assert result["status"] == "passed"


def test_unsupported_action_raises_error(executor):
    step = {
        "action": "delete_everything",
    }

    with pytest.raises(ValueError, match="Unsupported action"):
        executor.execute_step(step)


def test_missing_navigation_url_raises_error(executor):
    step = {
        "action": "navigate",
    }

    with pytest.raises(ValueError, match="url"):
        executor.execute_step(step)


def test_invalid_timeout_raises_error(executor):
    step = {
        "action": "navigate",
        "url": "http://127.0.0.1:8000",
        "timeout": 60000,
    }

    with pytest.raises(ValueError, match="Timeout"):
        executor.execute_step(step)


def test_complete_test_plan(executor, mock_page):
    test_plan = {
        "test_case_id": "US001_TC001",
        "title": "Verify successful login",
        "steps": [
            {
                "action": "navigate",
                "url": "http://127.0.0.1:8000",
            },
            {
                "action": "fill",
                "target": {
                    "by": "label",
                    "value": "Username",
                },
                "value": "admin",
            },
            {
                "action": "click",
                "target": {
                    "by": "role",
                    "role": "button",
                    "value": "Login",
                },
            },
        ],
    }

    result = executor.execute_test_plan(test_plan)

    assert result["test_case_id"] == "US001_TC001"
    assert result["status"] == "passed"
    assert result["total_steps"] == 3
    assert result["passed_steps"] == 3
    assert result["failed_steps"] == 0
    assert result["duration_ms"] >= 0

    assert Path(result["report_path"]).exists()

    mock_page.goto.assert_called_once()
    mock_page.get_by_label.assert_called_once()
    mock_page.get_by_role.assert_called_once()


def test_failed_step_captures_failure_details(
    executor,
    mock_page,
):
    mock_page.get_by_role.return_value.click.side_effect = (
        RuntimeError("Button could not be clicked")
    )

    test_plan = {
        "test_case_id": "FAIL001",
        "title": "Test failure capture",
        "steps": [
            {
                "action": "navigate",
                "url": "http://127.0.0.1:8000",
            },
            {
                "action": "click",
                "target": {
                    "by": "role",
                    "role": "button",
                    "value": "Login",
                },
            },
        ],
    }

    with pytest.raises(RuntimeError) as error_info:
        executor.execute_test_plan(test_plan)

    error = error_info.value
    report = error.execution_result

    assert report["status"] == "failed"
    assert report["total_steps"] == 2
    assert report["passed_steps"] == 1
    assert report["failed_steps"] == 1
    assert report["failed_step_number"] == 2

    failure = report["failure_details"]

    assert failure["action"] == "click"
    assert failure["status"] == "failed"
    assert failure["error"]["type"] == "RuntimeError"
    assert "could not be clicked" in failure["error"]["message"]

    assert failure["browser_state"]["url"] == (
        "http://127.0.0.1:8000/"
    )
    assert failure["browser_state"]["title"] == (
        "Multi-Agent Automation Demo"
    )

    assert report["report_path"] is not None
    assert Path(report["report_path"]).exists()

    assert report["screenshot_error"] if "screenshot_error" in report else True


def test_failure_report_is_valid_json(
    executor,
    mock_page,
):
    mock_page.goto.side_effect = RuntimeError(
        "Navigation failed"
    )

    test_plan = {
        "test_case_id": "JSON001",
        "title": "Verify JSON failure report",
        "steps": [
            {
                "action": "navigate",
                "url": "http://invalid.local",
            },
        ],
    }

    with pytest.raises(RuntimeError) as error_info:
        executor.execute_test_plan(test_plan)

    report_path = Path(
        error_info.value.execution_result["report_path"]
    )

    with report_path.open(
        "r",
        encoding="utf-8",
    ) as report_file:
        saved_report = json.load(report_file)

    assert saved_report["status"] == "failed"
    assert saved_report["failure_details"]["error"]["message"] == (
        "Navigation failed"
    )


def test_screenshot_failure_does_not_hide_original_error(
    executor,
    mock_page,
):
    mock_page.goto.side_effect = RuntimeError(
        "Original navigation failure"
    )
    mock_page.screenshot.side_effect = RuntimeError(
        "Screenshot could not be saved"
    )

    test_plan = {
        "test_case_id": "SCREENSHOT001",
        "title": "Verify screenshot error handling",
        "steps": [
            {
                "action": "navigate",
                "url": "http://invalid.local",
            },
        ],
    }

    with pytest.raises(RuntimeError) as error_info:
        executor.execute_test_plan(test_plan)

    report = error_info.value.execution_result

    assert report["status"] == "failed"
    assert report["failure_details"]["error"]["message"] == (
        "Original navigation failure"
    )
    assert report["failure_details"]["screenshot_path"] is None
    assert "Screenshot could not be saved" in (
        report["failure_details"]["screenshot_error"]
    )

import json
from pathlib import Path

import pytest

from core.browser_executor import BrowserExecutor


def test_real_browser_failure_creates_screenshot_and_report(
    page,
    tmp_path,
):
    """
    Verify that a real Chromium failure creates:
    1. A screenshot of the failed browser page.
    2. A JSON execution report.
    """

    demo_url = "http://127.0.0.1:8000/"

    page.goto(
        demo_url,
        wait_until="domcontentloaded",
    )

    artifacts_dir = tmp_path / "artifacts"

    executor = BrowserExecutor(
        page,
        artifacts_dir=str(artifacts_dir),
    )

    test_plan = {
        "test_case_id": "REAL_BROWSER_FAILURE_001",
        "title": "Verify real browser failure capture",
        "steps": [
            {
                "action": "navigate",
                "url": demo_url,
            },
            {
                "action": "verify_visible",
                "target": {
                    "by": "css",
                    "value": "#element-that-does-not-exist",
                },
                "timeout": 1000,
            },
        ],
    }

    with pytest.raises(RuntimeError) as error_info:
        executor.execute_test_plan(test_plan)

    execution_result = error_info.value.execution_result
    failure_details = execution_result["failure_details"]

    assert execution_result["status"] == "failed"
    assert execution_result["total_steps"] == 2
    assert execution_result["passed_steps"] == 1
    assert execution_result["failed_steps"] == 1
    assert execution_result["failed_step_number"] == 2

    assert failure_details["action"] == "verify_visible"
    assert failure_details["status"] == "failed"

    assert failure_details["browser_state"]["url"] == demo_url
    assert failure_details["browser_state"]["title"] == (
        "Multi-Agent Automation Demo"
    )

    # Verify that a real screenshot was created.
    screenshot_path = Path(
        failure_details["screenshot_path"]
    )

    assert screenshot_path.exists()
    assert screenshot_path.stat().st_size > 0

    with screenshot_path.open("rb") as screenshot_file:
        assert screenshot_file.read(8) == b"\x89PNG\r\n\x1a\n"

    # Verify that the JSON execution report was created.
    report_path = Path(
        execution_result["report_path"]
    )

    assert report_path.exists()

    with report_path.open(
        "r",
        encoding="utf-8",
    ) as report_file:
        saved_report = json.load(report_file)

    assert saved_report["status"] == "failed"
    assert saved_report["test_case_id"] == (
        "REAL_BROWSER_FAILURE_001"
    )

    assert saved_report["failure_details"]["action"] == (
        "verify_visible"
    )

    assert Path(
        saved_report["failure_details"]["screenshot_path"]
    ).exists()

    print("\nREAL BROWSER FAILURE CAPTURE VERIFIED")
    print(f"Screenshot: {screenshot_path}")
    print(f"JSON report: {report_path}")
