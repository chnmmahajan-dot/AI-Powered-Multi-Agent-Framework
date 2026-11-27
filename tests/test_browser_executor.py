
import pytest
from unittest.mock import MagicMock

from core.browser_executor import BrowserExecutor


@pytest.fixture
def mock_page():
    """Create a simulated Playwright page."""
    return MagicMock()


@pytest.fixture
def executor(mock_page):
    """Create the browser executor using the simulated page."""
    return BrowserExecutor(mock_page)


def test_navigate_action(executor, mock_page):
    step = {
        "action": "navigate",
        "url": "http://127.0.0.1:8000"
    }

    result = executor.execute_step(step)

    mock_page.goto.assert_called_once_with(
        "http://127.0.0.1:8000",
        wait_until="domcontentloaded",
        timeout=5000
    )

    assert result["status"] == "passed"
    assert result["action"] == "navigate"


def test_fill_action(executor, mock_page):
    step = {
        "action": "fill",
        "target": {
            "by": "label",
            "value": "Username"
        },
        "value": "admin"
    }

    result = executor.execute_step(step)

    mock_page.get_by_label.assert_called_once_with(
        "Username",
        exact=False
    )

    mock_page.get_by_label.return_value.fill.assert_called_once_with(
        "admin",
        timeout=5000
    )

    assert result["status"] == "passed"


def test_click_action(executor, mock_page):
    step = {
        "action": "click",
        "target": {
            "by": "role",
            "role": "button",
            "value": "Login"
        }
    }

    result = executor.execute_step(step)

    mock_page.get_by_role.assert_called_once_with(
        "button",
        name="Login",
        exact=False
    )

    mock_page.get_by_role.return_value.click.assert_called_once_with(
        timeout=5000
    )

    assert result["status"] == "passed"


def test_verify_text_action(executor, mock_page):
    step = {
        "action": "verify_text",
        "expected": "Dashboard"
    }

    result = executor.execute_step(step)

    mock_page.get_by_text.assert_called_once_with("Dashboard")

    mock_page.get_by_text.return_value.first.wait_for.assert_called_once_with(
        state="visible",
        timeout=5000
    )

    assert result["status"] == "passed"


def test_unsupported_action_raises_error(executor):
    step = {
        "action": "delete_everything"
    }

    with pytest.raises(ValueError, match="Unsupported action"):
        executor.execute_step(step)


def test_missing_navigation_url_raises_error(executor):
    step = {
        "action": "navigate"
    }

    with pytest.raises(ValueError, match="url"):
        executor.execute_step(step)


def test_complete_test_plan(executor, mock_page):
    test_plan = {
        "test_case_id": "US001_TC001",
        "title": "Verify successful login",
        "steps": [
            {
                "action": "navigate",
                "url": "http://127.0.0.1:8000"
            },
            {
                "action": "fill",
                "target": {
                    "by": "label",
                    "value": "Username"
                },
                "value": "admin"
            },
            {
                "action": "click",
                "target": {
                    "by": "role",
                    "role": "button",
                    "value": "Login"
                }
            }
        ]
    }

    result = executor.execute_test_plan(test_plan)

    assert result["test_case_id"] == "US001_TC001"
    assert result["status"] == "passed"
    assert result["total_steps"] == 3
    assert result["passed_steps"] == 3
    assert result["failed_steps"] == 0

    mock_page.goto.assert_called_once()
    mock_page.get_by_label.assert_called_once()
    mock_page.get_by_role.assert_called_once()


def test_invalid_timeout_raises_error(executor):
    step = {
        "action": "navigate",
        "url": "http://127.0.0.1:8000",
        "timeout": 60000
    }

    with pytest.raises(ValueError, match="Timeout"):
        executor.execute_step(step)
