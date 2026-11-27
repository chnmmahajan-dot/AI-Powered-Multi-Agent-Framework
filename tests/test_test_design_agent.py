
from pathlib import Path

from agents.requirement_reader import RequirementReaderAgent
from agents.test_design_agent import TestDesignAgent


def test_generate_test_scenarios():
    project_root = Path(__file__).resolve().parents[1]
    requirements_file = project_root / "user_stories" / "requirements.xlsx"

    reader = RequirementReaderAgent()
    requirements = reader.read_requirements(str(requirements_file))

    agent = TestDesignAgent()
    scenarios = agent.generate_test_scenarios(requirements)

    # One relevant scenario should be generated for each requirement.
    assert len(scenarios) == 3

    # Verify scenario types.
    scenario_types = {scenario["type"] for scenario in scenarios}
    assert scenario_types == {"Positive", "Negative"}

    # Verify scenario IDs.
    assert scenarios[0]["test_case_id"] == "US001_TC001"
    assert scenarios[1]["test_case_id"] == "US002_TC001"
    assert scenarios[2]["test_case_id"] == "US003_TC001"

    # Verify generated actions.
    actions = [scenario["action"] for scenario in scenarios]

    assert actions == [
        "valid_login",
        "invalid_login",
        "logout"
    ]
