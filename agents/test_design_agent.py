
from core.ollama_client import OllamaClient


class TestDesignAgent:
    """Uses a local LLM to design test scenarios from requirements."""

    __test__ = False

    SUPPORTED_ACTIONS = {
        "valid_login",
        "invalid_login",
        "logout",
    }

    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client or OllamaClient()

    def generate_test_scenarios(self, requirements: list[dict]) -> list[dict]:
        if not requirements:
            return []

        prompt = self._build_prompt(requirements)

        ai_response = self.ollama_client.generate_json(prompt)

        ai_scenarios = ai_response.get("scenarios", [])

        if not isinstance(ai_scenarios, list):
            raise ValueError(
                "AI response must contain a list of scenarios."
            )

        if len(ai_scenarios) != len(requirements):
            raise ValueError(
                "AI returned an unexpected number of scenarios. "
                f"Expected {len(requirements)}, received {len(ai_scenarios)}."
            )

        scenarios = []

        for index, requirement in enumerate(requirements):
            ai_scenario = ai_scenarios[index]

            if not isinstance(ai_scenario, dict):
                raise ValueError(
                    f"AI returned an invalid scenario for requirement "
                    f"'{requirement['story_id']}'. Expected a JSON object."
                )

            action = str(
                ai_scenario.get("action", "")
            ).strip().lower()

            if action not in self.SUPPORTED_ACTIONS:
                raise ValueError(
                    f"AI generated unsupported action '{action}' "
                    f"for requirement '{requirement['story_id']}'. "
                    f"Supported actions: {sorted(self.SUPPORTED_ACTIONS)}"
                )

            scenario_description = str(
                ai_scenario.get("scenario", "")
            ).strip()

            expected_result = str(
                ai_scenario.get("expected_result", "")
            ).strip()

            if not scenario_description:
                raise ValueError(
                    f"AI generated an empty scenario for requirement "
                    f"'{requirement['story_id']}'."
                )

            if not expected_result:
                raise ValueError(
                    f"AI generated an empty expected result for requirement "
                    f"'{requirement['story_id']}'."
                )

            scenario_type = (
                "Negative" if action == "invalid_login" else "Positive"
            )

            scenarios.append({
                "test_case_id": (
                    f"{str(requirement['story_id']).strip()}_TC001"
                ),
                "story_id": str(requirement["story_id"]).strip(),
                "requirement_title": str(requirement["title"]).strip(),
                "type": scenario_type,
                "scenario": scenario_description,
                "action": action,
                "expected_result": expected_result,
            })

        return scenarios

    def _build_prompt(self, requirements: list[dict]) -> str:
        requirement_text = ""

        for index, requirement in enumerate(requirements, start=1):
            requirement_text += (
                f"\nRequirement {index}:\n"
                f"Story ID: {requirement['story_id']}\n"
                f"Title: {requirement['title']}\n"
                f"Description: {requirement['description']}\n"
            )

        return f"""
You are an expert software test engineer.

Analyse the following software requirements.

Generate EXACTLY one test scenario for each requirement.
Keep the scenarios in the same order as the requirements.

For each requirement, choose exactly one action from this list:

1. valid_login
   Use for successful login with valid credentials.

2. invalid_login
   Use for unsuccessful login, incorrect credentials,
   invalid passwords, or failed authentication.

3. logout
   Use for logging out or ending an authenticated session.

Return ONLY valid JSON using this exact structure:

{{
    "scenarios": [
        {{
            "scenario": "Clear test scenario description",
            "action": "valid_login",
            "expected_result": "Clear expected application behaviour"
        }}
    ]
}}

Rules:
- Return exactly {len(requirements)} scenario objects.
- Do not skip any requirement.
- Use only the three supported actions.
- Do not include Markdown or explanations.
- Make scenario descriptions specific to each requirement.
- Every scenario must have a non-empty expected result.

Requirements:
{requirement_text}
"""
