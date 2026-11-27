
from unittest.mock import MagicMock

from agents.website_inspection_agent import WebsiteInspectionAgent


def test_inspect_page_discovers_elements():
    page = MagicMock()
    page.url = "http://127.0.0.1:8000"
    page.title.return_value = "Demo Login"

    page.locator.return_value.evaluate_all.side_effect = [
        [
            {
                "tag": "input",
                "id": "username",
                "type": "text",
                "name": "",
                "placeholder": "Enter username",
                "aria_label": "",
                "role": "",
                "text": "",
                "href": "",
                "visible": True,
            },
            {
                "tag": "button",
                "id": "login-button",
                "type": "",
                "name": "",
                "placeholder": "",
                "aria_label": "",
                "role": "",
                "text": "Login",
                "href": "",
                "visible": True,
            },
        ],
        [
            {
                "tag": "h2",
                "text": "Login",
            }
        ],
    ]

    agent = WebsiteInspectionAgent(page)
    result = agent.inspect_page()

    assert result["url"] == "http://127.0.0.1:8000"
    assert result["title"] == "Demo Login"
    assert result["element_count"] == 2
    assert result["interactive_elements"][0]["id"] == "username"


def test_format_inspection_for_ai():
    page = MagicMock()
    agent = WebsiteInspectionAgent(page)

    inspection = {
        "url": "http://127.0.0.1:8000",
        "title": "Demo Login",
        "headings": [
            {"tag": "h2", "text": "Login"}
        ],
        "interactive_elements": [
            {
                "tag": "input",
                "id": "username",
                "type": "text",
                "name": "",
                "placeholder": "Enter username",
                "aria_label": "",
                "role": "",
                "text": "",
                "href": "",
                "visible": True,
            }
        ],
        "element_count": 1,
    }

    result = agent.format_inspection_for_ai(inspection)

    assert "Demo Login" in result
    assert "Enter username" in result
    assert "username" in result
    assert "INTERACTIVE ELEMENTS" in result


def test_inspection_handles_empty_page():
    page = MagicMock()
    page.url = "http://127.0.0.1:8000"
    page.title.return_value = "Empty Page"
    page.locator.return_value.evaluate_all.side_effect = [
        [],
        [],
    ]

    agent = WebsiteInspectionAgent(page)
    result = agent.inspect_page()

    assert result["element_count"] == 0
    assert result["interactive_elements"] == []
    assert result["headings"] == []
