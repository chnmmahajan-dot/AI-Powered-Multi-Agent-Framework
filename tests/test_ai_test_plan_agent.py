
import pytest
from unittest.mock import MagicMock

from agents.ai_test_plan_agent import AITestPlanAgent


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def agent(mock_client):
    return AITestPlanAgent(ollama_client=mock_client)


def valid_plan():
    return {
        "test_case_id": "TC_001",
        "requirement_id": "REQ_001",
        "title": "Verify successful login",
        "description": "Verify that a user can log in.",
        "expected_result": "Welcome message is displayed.",
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
            {
                "action": "verify_text",
                "expected": "Welcome",
            },
        ],
    }


def test_generate_valid_test_plan(agent, mock_client):
    mock_client.generate_json.return_value = valid_plan()

    result = agent.generate_test_plan(
        "Users should be able to log in."
    )

    assert result["test_case_id"] == "TC_001"
    assert len(result["steps"]) == 4
    mock_client.generate_json.assert_called_once()


def test_reject_unsupported_action(agent):
    plan = valid_plan()
    plan["steps"][0] = {
        "action": "execute_python",
        "url": "http://127.0.0.1:8000",
    }

    with pytest.raises(ValueError):
        agent.validate_test_plan(plan)


def test_reject_fill_without_value(agent):
    plan = valid_plan()
    plan["steps"][1].pop("value")

    with pytest.raises(ValueError):
        agent.validate_test_plan(plan)


def test_reject_role_locator_without_role(agent):
    plan = valid_plan()
    plan["steps"][2]["target"].pop("role")

    with pytest.raises(ValueError):
        agent.validate_test_plan(plan)


def test_reject_empty_steps(agent):
    plan = valid_plan()
    plan["steps"] = []

    with pytest.raises(ValueError):
        agent.validate_test_plan(plan)


def test_reject_invalid_requirement(agent):
    with pytest.raises(ValueError):
        agent.generate_test_plan(12345)


def test_accept_string_requirement(agent, mock_client):
    mock_client.generate_json.return_value = valid_plan()

    result = agent.generate_test_plan(
        "A user should be able to log in."
    )

    assert result["title"] == "Verify successful login"


def test_accept_dictionary_requirement(agent, mock_client):
    mock_client.generate_json.return_value = valid_plan()

    result = agent.generate_test_plan({
        "requirement_id": "REQ_001",
        "description": "Users should be able to log in.",
    })

    assert result["requirement_id"] == "REQ_001"
