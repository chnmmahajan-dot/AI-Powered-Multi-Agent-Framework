
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

        if len(ai_scenarios) != len(requirements):
            raise ValueError(
                "AI returned an unexpected number of scenarios. "
                f"Expected {len(requirements)}, received {len(ai_scenarios)}."
            )

        scenarios = []

        for index, requirement in enumerate(requirements):
            ai_scenario = ai_scenarios[index]

            action = str(ai_scenario.get("action", "")).strip().lower()

            if action not in self.SUPPORTED_ACTIONS:
                action = self._fallback_action(requirement)

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
                "scenario": str(
                    ai_scenario.get("scenario", "")
                ).strip() or "Review generated scenario",
                "action": action,
                "expected_result": str(
                    ai_scenario.get("expected_result", "")
                ).strip() or "Expected result requires manual review.",
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

Requirements:
{requirement_text}
"""
    
    def _fallback_action(self, requirement: dict) -> str:
        """Use simple rules if the AI returns an unsupported action."""

        text = (
            f"{requirement.get('title', '')} "
            f"{requirement.get('description', '')}"
        ).lower()

        if any(keyword in text for keyword in [
            "logout",
            "log out",
            "sign out",
            "end session",
        ]):
            return "logout"

        if any(keyword in text for keyword in [
            "invalid",
            "incorrect",
            "wrong password",
            "failed login",
            "unsuccessful login",
        ]):
            return "invalid_login"

        return "valid_login"
