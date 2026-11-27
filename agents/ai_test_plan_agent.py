
import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from config.settings import PROJECT_ROOT
from core.ollama_client import OllamaClient


class AITestPlanAgent:
    """Generates and validates browser-executable test plans using AI."""

    def __init__(
        self,
        ollama_client=None,
        schema_path=None,
    ):
        self.ollama_client = ollama_client or OllamaClient()

        self.schema_path = Path(
            schema_path
            or PROJECT_ROOT / "schemas" / "test_plan.schema.json"
        )

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Test plan schema not found: {self.schema_path}"
            )

        with self.schema_path.open("r", encoding="utf-8") as file:
            self.schema = json.load(file)

    def _format_requirement(self, requirement: Any) -> str:
        """Convert a requirement into readable text for the AI."""

        if isinstance(requirement, dict):
            return json.dumps(
                requirement,
                indent=2,
                ensure_ascii=False,
            )

        if isinstance(requirement, str):
            return requirement

        raise ValueError(
            "Requirement must be a string or dictionary."
        )

    def _validate_action_fields(self, step: dict) -> None:
        """Validate fields required by each supported browser action."""

        action = step["action"]

        required_fields = {
            "navigate": ["url"],
            "click": ["target"],
            "fill": ["target", "value"],
            "press": ["target", "value"],
            "select_option": ["target", "value"],
            "check": ["target"],
            "uncheck": ["target"],
            "verify_text": ["expected"],
            "verify_visible": ["target"],
            "verify_url": ["expected"],
            "wait_for": ["target"],
        }

        for field in required_fields[action]:
            if field not in step or step[field] in (None, ""):
                raise ValueError(
                    f"Action '{action}' requires field '{field}'."
                )

        if "target" in step:
            target = step["target"]

            if target["by"] == "role" and not target.get("role"):
                raise ValueError(
                    "A role locator must include a non-empty 'role'."
                )

    def validate_test_plan(self, test_plan: dict) -> dict:
        """Validate AI output against the JSON schema and action rules."""

        try:
            validate(
                instance=test_plan,
                schema=self.schema,
            )
        except ValidationError as error:
            raise ValueError(
                f"AI generated an invalid test plan: {error.message}"
            ) from error

        for index, step in enumerate(test_plan["steps"], start=1):
            try:
                self._validate_action_fields(step)
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid instruction at step {index}: {error}"
                ) from error

        return test_plan

    def generate_test_plan(self, requirement: Any) -> dict:
        """Ask Ollama to generate a browser-executable test plan."""

        requirement_text = self._format_requirement(requirement)

        prompt = f"""
You are an expert software test automation engineer.

Your task is to convert the following software requirement into
ONE detailed, executable browser test plan.

SOFTWARE REQUIREMENT:
{requirement_text}

Return ONLY one valid JSON object.

The JSON must follow this structure:

{{
    "test_case_id": "TC_001",
    "requirement_id": "REQ_001",
    "title": "Meaningful test title",
    "description": "What this test verifies",
    "expected_result": "Expected final outcome",
    "steps": [
        {{
            "action": "navigate",
            "url": "http://127.0.0.1:8000"
        }},
        {{
            "action": "fill",
            "target": {{
                "by": "label",
                "value": "Username"
            }},
            "value": "admin"
        }},
        {{
            "action": "click",
            "target": {{
                "by": "role",
                "role": "button",
                "value": "Login"
            }}
        }},
        {{
            "action": "verify_text",
            "expected": "Welcome"
        }}
    ]
}}

SUPPORTED ACTIONS:
- navigate: requires url
- click: requires target
- fill: requires target and value
- press: requires target and value
- select_option: requires target and value
- check: requires target
- uncheck: requires target
- verify_text: requires expected
- verify_visible: requires target
- verify_url: requires expected
- wait_for: requires target

SUPPORTED LOCATOR STRATEGIES:
- role: requires by, role, value
- label: requires by, value
- placeholder: requires by, value
- text: requires by, value
- test_id: requires by, value
- css: requires by, value

IMPORTANT RULES:
1. Generate only the supported actions listed above.
2. Do not generate Python, JavaScript, or executable code.
3. Do not invent URLs, credentials, or application elements.
4. Use only information supported by the requirement.
5. Use the supplied requirement to identify expected behavior.
6. Include meaningful verification steps.
7. Every test plan must have at least one step.
8. Every step must be a valid JSON object.
9. Do not include Markdown or explanations outside JSON.
10. Use exact locator information when it is provided.
"""

        test_plan = self.ollama_client.generate_json(prompt)

        return self.validate_test_plan(test_plan)
