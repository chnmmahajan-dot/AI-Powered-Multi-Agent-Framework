
import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from config.settings import PROJECT_ROOT
from core.ollama_client import OllamaClient


class AITestPlanAgent:
    """Generates, normalizes, and validates browser-executable test plans."""

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

    # =========================================================
    # REQUIREMENT HANDLING
    # =========================================================

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

    # =========================================================
    # AI OUTPUT NORMALIZATION
    # =========================================================

    def _normalize_locator(self, target: Any) -> dict:
        """
        Convert AI-generated locator strings into locator objects.

        The website inspection and locator grounding stages will
        subsequently determine whether the locator actually exists.
        """

        if isinstance(target, dict):
            return target

        if isinstance(target, str):
            target = target.strip()

            if not target:
                raise ValueError(
                    "AI generated an empty locator."
                )

            # CSS selectors can be recognized directly.
            if (
                target.startswith("#")
                or target.startswith(".")
                or target.startswith("[")
            ):
                return {
                    "by": "css",
                    "value": target,
                }

            # If the AI returns a plain element identifier,
            # interpret it as an element ID.
            #
            # Example:
            # "login-button" -> "#login-button"
            #
            # The inspection agent and locator grounding layer
            # will validate this against the real website.
            if (
                target.replace("-", "")
                .replace("_", "")
                .isalnum()
            ):
                return {
                    "by": "css",
                    "value": f"#{target}",
                }

            # Otherwise treat it as visible text.
            return {
                "by": "text",
                "value": target,
            }

        raise ValueError(
            f"Unsupported locator format: {type(target).__name__}"
        )

    def normalize_test_plan(self, test_plan: Any) -> dict:
        """
        Repair common structural mistakes in AI-generated output
        without inventing test steps or changing test behavior.
        """

        if not isinstance(test_plan, dict):
            raise ValueError(
                "AI must generate a JSON object for the test plan."
            )

        if not isinstance(test_plan.get("steps"), list):
            raise ValueError(
                "AI-generated test plan must contain a steps list."
            )

        normalized_plan = dict(test_plan)
        normalized_steps = []

        for index, step in enumerate(test_plan["steps"], start=1):

            if not isinstance(step, dict):
                raise ValueError(
                    f"Step {index} must be a JSON object."
                )

            normalized_step = dict(step)

            if "target" in normalized_step:
                normalized_step["target"] = (
                    self._normalize_locator(
                        normalized_step["target"]
                    )
                )

            normalized_steps.append(normalized_step)

        normalized_plan["steps"] = normalized_steps

        return normalized_plan

    # =========================================================
    # ACTION VALIDATION
    # =========================================================

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

        if action not in required_fields:
            raise ValueError(
                f"Unsupported browser action: {action}"
            )

        for field in required_fields[action]:
            if field not in step or step[field] in (None, ""):
                raise ValueError(
                    f"Action '{action}' requires field '{field}'."
                )

        if "target" in step:
            target = step["target"]

            if not isinstance(target, dict):
                raise ValueError(
                    "Target must be a locator object."
                )

            if "by" not in target:
                raise ValueError(
                    "Locator must contain the 'by' field."
                )

            if target["by"] == "role":
                if not target.get("role"):
                    raise ValueError(
                        "A role locator must include "
                        "a non-empty 'role'."
                    )

            elif not target.get("value"):
                raise ValueError(
                    "A locator must include a non-empty 'value'."
                )

    # =========================================================
    # TEST PLAN VALIDATION
    # =========================================================

    def validate_test_plan(self, test_plan: dict) -> dict:
        """Validate AI output against the schema and action rules."""

        try:
            validate(
                instance=test_plan,
                schema=self.schema,
            )

        except ValidationError as error:
            raise ValueError(
                f"AI generated an invalid test plan: "
                f"{error.message}"
            ) from error

        for index, step in enumerate(
            test_plan["steps"],
            start=1,
        ):
            try:
                self._validate_action_fields(step)

            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid instruction at step {index}: {error}"
                ) from error

        return test_plan

    # =========================================================
    # PROMPT GENERATION
    # =========================================================

    def _build_prompt(self, requirement_text: str) -> str:
        """Build a detailed prompt for generating an executable plan."""

        return f"""
You are an expert software test automation engineer.

Your task is to convert the supplied software requirement or
discovered user workflow into ONE executable browser test plan.

SOFTWARE REQUIREMENT:
{requirement_text}

Return ONLY one valid JSON object.

Do not return Markdown.
Do not return explanations.
Do not return multiple test plans.
Do not wrap the JSON in code fences.

REQUIRED STRUCTURE:

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
                "by": "css",
                "value": "#username"
            }},
            "value": "admin"
        }},
        {{
            "action": "click",
            "target": {{
                "by": "css",
                "value": "#login-button"
            }}
        }},
        {{
            "action": "verify_text",
            "expected": "Welcome"
        }}
    ]
}}

SUPPORTED ACTIONS:

1. navigate
   Required: url

2. click
   Required: target

3. fill
   Required: target, value

4. press
   Required: target, value

5. select_option
   Required: target, value

6. check
   Required: target

7. uncheck
   Required: target

8. verify_text
   Required: expected

9. verify_visible
   Required: target

10. verify_url
    Required: expected

11. wait_for
    Required: target

SUPPORTED LOCATOR STRATEGIES:

1. role
   Example:
   {{
       "by": "role",
       "role": "button",
       "value": "Login"
   }}

2. label
   Example:
   {{
       "by": "label",
       "value": "Username"
   }}

3. placeholder
   Example:
   {{
       "by": "placeholder",
       "value": "Enter username"
   }}

4. text
   Example:
   {{
       "by": "text",
       "value": "Login"
   }}

5. test_id
   Example:
   {{
       "by": "test_id",
       "value": "login-button"
   }}

6. css
   Example:
   {{
       "by": "css",
       "value": "#login-button"
   }}

IMPORTANT TEST GENERATION RULES:

1. Generate only supported browser actions.

2. Every action must be a valid JSON object.

3. Every locator must be a locator object.
   NEVER return a locator as a plain string.

4. Use the actual website inspection information when supplied.

5. Use exact element IDs, labels, placeholders, roles,
   and text from the inspection wherever possible.

6. Never invent elements, buttons, fields, URLs, credentials,
   or application behavior.

7. If test_data is supplied, use those exact values when
   the workflow requires them.

8. Never invent credentials.

9. If the workflow requires login, ensure the username AND
   password fields are filled when the application requires
   both credentials.

10. Do not skip steps required to reach the expected state.

11. Follow the supplied workflow steps in the exact order.

12. Do not add unrelated steps or unrelated workflows.

13. Include meaningful verification actions.

14. Verification must check the expected final state,
    not merely that an action was attempted.

15. When verifying text, use text that is explicitly supported
    by the requirement or website inspection.

16. When verifying a URL, use a URL supported by the
    requirement or website inspection.

17. Do not generate Python, JavaScript, or executable code.

18. Every test plan must contain at least one step.

19. Return exactly one valid JSON object.

20. If the requirement is a discovered workflow, convert the
    workflow into a test plan. Do not redesign the workflow.

21. If the workflow starts from an already authenticated
    state, do not assume that authentication exists.
    Include authentication steps only when required to
    establish the state needed for the workflow.

22. For logout workflows, establish an authenticated state
    before attempting logout, unless the requirement explicitly
    states that the application is already authenticated.

23. Use the supplied application URL. Do not invent another URL.

24. Do not replace actual workflow steps with assumptions.

25. Keep the plan deterministic and suitable for automated
    execution.

Return only the JSON object.
"""

    # =========================================================
    # TEST PLAN GENERATION
    # =========================================================

    def generate_test_plan(self, requirement: Any) -> dict:
        """Generate, normalize, and validate a browser test plan."""

        requirement_text = self._format_requirement(
            requirement
        )

        prompt = self._build_prompt(
            requirement_text
        )

        # Ask the local LLM to generate a plan.
        test_plan = self.ollama_client.generate_json(
            prompt
        )

        # Normalize common structural locator mistakes.
        test_plan = self.normalize_test_plan(
            test_plan
        )

        # Validate against our strict schema and supported actions.
        return self.validate_test_plan(
            test_plan
        )

