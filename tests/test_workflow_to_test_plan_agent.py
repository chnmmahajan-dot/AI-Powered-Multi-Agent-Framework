
import pytest

from agents.workflow_to_test_plan_agent import WorkflowToTestPlanAgent


class MockTestPlanAgent:
    def __init__(self, response=None):
        self.response = response or {
            "test_case_id": "TC_WF_001",
            "title": "Verify successful login",
            "steps": [
                {
                    "action": "navigate",
                    "url": "http://127.0.0.1:8000/"
                },
                {
                    "action": "fill",
                    "target": {
                        "by": "placeholder",
                        "value": "Enter username"
                    },
                    "value": "admin"
                },
                {
                    "action": "verify_text",
                    "expected": "Welcome!"
                }
            ]
        }
        self.received_requirement = None

    def generate_test_plan(self, requirement):
        self.received_requirement = requirement
        return self.response


@pytest.fixture
def inspection():
    return {
        "url": "http://127.0.0.1:8000/",
        "title": "Multi-Agent Automation Demo",
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
            }
        ]
    }


@pytest.fixture
def workflow():
    return {
        "workflow_id": "WF_001",
        "title": "Successful user login",
        "description": "A user logs in with valid credentials.",
        "steps": [
            "Enter valid username.",
            "Enter valid password.",
            "Click Login.",
            "Verify the welcome message."
        ],
        "elements_used": [
            "username",
            "password",
            "login-button"
        ],
        "expected_outcome": "The welcome page is displayed."
    }


def test_converts_workflow_into_test_plan(inspection, workflow):
    mock_agent = MockTestPlanAgent()
    agent = WorkflowToTestPlanAgent(
        test_plan_agent=mock_agent
    )

    result = agent.generate_test_plan_for_workflow(
        workflow,
        inspection,
        test_data={
            "username": "admin",
            "password": "password123"
        }
    )

    assert result["test_case_id"] == "TC_WF_001"
    assert len(result["steps"]) == 3
    assert mock_agent.received_requirement["requirement_id"] == "WF_001"


def test_passes_workflow_steps_to_test_plan_agent(
    inspection,
    workflow
):
    mock_agent = MockTestPlanAgent()
    agent = WorkflowToTestPlanAgent(
        test_plan_agent=mock_agent
    )

    agent.generate_test_plan_for_workflow(workflow, inspection)

    requirement = mock_agent.received_requirement

    assert requirement["workflow_steps"] == workflow["steps"]
    assert requirement["expected_outcome"] == workflow["expected_outcome"]
    assert requirement["application_url"] == inspection["url"]


def test_passes_test_data_to_test_plan_agent(inspection, workflow):
    mock_agent = MockTestPlanAgent()
    agent = WorkflowToTestPlanAgent(
        test_plan_agent=mock_agent
    )

    test_data = {
        "username": "admin",
        "password": "password123"
    }

    agent.generate_test_plan_for_workflow(
        workflow,
        inspection,
        test_data=test_data
    )

    assert mock_agent.received_requirement["test_data"] == test_data


def test_rejects_missing_workflow_field(inspection):
    agent = WorkflowToTestPlanAgent(
        test_plan_agent=MockTestPlanAgent()
    )

    with pytest.raises(ValueError, match="workflow_id"):
        agent.generate_test_plan_for_workflow(
            {"title": "Incomplete workflow"},
            inspection
        )


def test_rejects_workflow_with_no_steps(inspection, workflow):
    workflow["steps"] = []

    agent = WorkflowToTestPlanAgent(
        test_plan_agent=MockTestPlanAgent()
    )

    with pytest.raises(ValueError, match="at least one step"):
        agent.generate_test_plan_for_workflow(
            workflow,
            inspection
        )


def test_rejects_undiscovered_element(inspection, workflow):
    workflow["elements_used"] = [
        "username",
        "fake-button"
    ]

    agent = WorkflowToTestPlanAgent(
        test_plan_agent=MockTestPlanAgent()
    )

    with pytest.raises(ValueError, match="undiscovered element"):
        agent.generate_test_plan_for_workflow(
            workflow,
            inspection
        )


def test_rejects_invalid_inspection(workflow):
    agent = WorkflowToTestPlanAgent(
        test_plan_agent=MockTestPlanAgent()
    )

    with pytest.raises(ValueError, match="inspection"):
        agent.generate_test_plan_for_workflow(
            workflow,
            {}
        )
