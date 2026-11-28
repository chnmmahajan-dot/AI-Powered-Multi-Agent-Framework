
import pytest

from jsonschema import ValidationError

from agents.workflow_discovery_agent import WorkflowDiscoveryAgent


class MockOllamaClient:
    def __init__(self, response):
        self.response = response
        self.last_prompt = None

    def generate_json(self, prompt):
        self.last_prompt = prompt
        return self.response


@pytest.fixture
def inspection():
    return {
        "url": "http://127.0.0.1:8000/",
        "title": "Multi-Agent Automation Demo",
        "headings": [
            {"tag": "h2", "text": "Login"},
            {"tag": "h2", "text": "Welcome!"}
        ],
        "interactive_elements": [
            {
                "tag": "input",
                "id": "username",
                "placeholder": "Enter username",
                "visible": True
            },
            {
                "tag": "input",
                "id": "password",
                "placeholder": "Enter password",
                "visible": True
            },
            {
                "tag": "button",
                "id": "login-button",
                "text": "Login",
                "visible": True
            },
            {
                "tag": "button",
                "id": "logout-button",
                "text": "Logout",
                "visible": False
            }
        ]
    }


@pytest.fixture
def valid_response():
    return {
        "workflows": [
            {
                "workflow_id": "WF_001",
                "title": "Successful user login",
                "description": "A user logs in with valid credentials.",
                "steps": [
                    "Enter a username.",
                    "Enter a password.",
                    "Click the Login button.",
                    "Verify that the welcome page appears."
                ],
                "elements_used": [
                    "username",
                    "password",
                    "login-button"
                ],
                "expected_outcome": "The user reaches the welcome page."
            },
            {
                "workflow_id": "WF_002",
                "title": "User logout",
                "description": "An authenticated user logs out.",
                "steps": [
                    "Log in successfully.",
                    "Click the Logout button.",
                    "Verify that the login screen appears."
                ],
                "elements_used": [
                    "username",
                    "password",
                    "login-button",
                    "logout-button"
                ],
                "expected_outcome": "The user returns to the login screen."
            }
        ]
    }


def test_discovers_valid_workflows(inspection, valid_response):
    client = MockOllamaClient(valid_response)
    agent = WorkflowDiscoveryAgent(ollama_client=client)

    result = agent.discover_workflows(inspection)

    assert len(result["workflows"]) == 2
    assert result["workflows"][0]["workflow_id"] == "WF_001"
    assert "AVAILABLE ELEMENT IDS" in client.last_prompt


def test_rejects_undiscovered_element(inspection, valid_response):
    response = {
        "workflows": [dict(valid_response["workflows"][0])]
    }
    response["workflows"][0]["elements_used"] = [
        "username",
        "fake-button"
    ]

    agent = WorkflowDiscoveryAgent(
        ollama_client=MockOllamaClient(response)
    )

    with pytest.raises(ValueError, match="undiscovered element"):
        agent.discover_workflows(inspection)


def test_rejects_duplicate_workflow_ids(inspection, valid_response):
    response = {
        "workflows": [
            dict(valid_response["workflows"][0]),
            dict(valid_response["workflows"][1])
        ]
    }
    response["workflows"][1]["workflow_id"] = "WF_001"

    agent = WorkflowDiscoveryAgent(
        ollama_client=MockOllamaClient(response)
    )

    with pytest.raises(ValueError, match="unique"):
        agent.discover_workflows(inspection)


def test_rejects_invalid_workflow_structure(inspection):
    response = {
        "workflows": [
            {
                "workflow_id": "WF_001",
                "title": "Incomplete workflow"
            }
        ]
    }

    agent = WorkflowDiscoveryAgent(
        ollama_client=MockOllamaClient(response)
    )

    with pytest.raises(ValidationError):
        agent.discover_workflows(inspection)


def test_rejects_empty_inspection():
    agent = WorkflowDiscoveryAgent(
        ollama_client=MockOllamaClient({"workflows": []})
    )

    with pytest.raises(ValueError, match="No interactive"):
        agent.discover_workflows({
            "url": "http://127.0.0.1:8000/",
            "interactive_elements": []
        })
