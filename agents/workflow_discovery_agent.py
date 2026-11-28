import json
import re
from pathlib import Path

from jsonschema import validate, ValidationError

from config.settings import PROJECT_ROOT
from core.ollama_client import OllamaClient


class WorkflowDiscoveryAgent:
    """Discovers workflows and filters out unsupported website journeys."""

    def __init__(self, ollama_client=None, schema_path=None):
        self.ollama_client = ollama_client or OllamaClient()

        self.schema_path = (
            Path(schema_path)
            if schema_path
            else PROJECT_ROOT / "schemas" / "workflow.schema.json"
        )

        with self.schema_path.open("r", encoding="utf-8") as file:
            self.schema = json.load(file)

        self.rejected_workflows = []

        self.workflow_schema = (
            self.schema["properties"]["workflows"]["items"]
        )

    @staticmethod
    def _normalize(value):
        return "".join(
            character.lower()
            for character in str(value)
            if character.isalnum()
        )

    def _get_available_element_ids(self, inspection):
        return {
            element["id"]
            for element in inspection.get("interactive_elements", [])
            if element.get("id")
        }

    def _find_element_id(self, elements, possible_ids):
        normalized_ids = {
            self._normalize(value)
            for value in possible_ids
        }

        for element in elements:
            element_id = element.get("id", "")

            if self._normalize(element_id) in normalized_ids:
                return element_id

        return None

    def _get_login_controls(self, inspection):
        elements = inspection.get("interactive_elements", [])

        username_id = self._find_element_id(
            elements,
            {"username", "user", "email"}
        )

        password_id = self._find_element_id(
            elements,
            {"password", "pass"}
        )

        login_id = self._find_element_id(
            elements,
            {"login-button", "login", "signin-button", "signin"}
        )

        return username_id, password_id, login_id

    def _has_matching_control(self, step, elements, control_type):
        """Check whether a step refers to a discovered control."""

        if control_type == "link":
            candidates = [
                element for element in elements
                if element.get("tag") == "a"
                or element.get("role") == "link"
            ]

        elif control_type == "button":
            candidates = [
                element for element in elements
                if element.get("tag") == "button"
                or element.get("role") == "button"
            ]

        else:
            return True

        if not candidates:
            return False

        words = re.findall(r"[a-z0-9]+", step.lower())

        ignored_words = {
            "click", "press", "the", "a", "an", "to",
            "on", "and", "then", "button", "link",
            "user", "users", "page"
        }

        meaningful_words = [
            word for word in words
            if word not in ignored_words
        ]

        if not meaningful_words:
            return True

        for element in candidates:
            element_values = [
                element.get("id", ""),
                element.get("text", ""),
                element.get("aria_label", ""),
                element.get("name", "")
            ]

            normalized_values = [
                self._normalize(value)
                for value in element_values
                if value
            ]

            for word in meaningful_words:
                normalized_word = self._normalize(word)

                if any(
                    normalized_word in value
                    for value in normalized_values
                ):
                    return True

        return False

    def _validate_workflow_controls(self, workflow, inspection):
        """Reject steps that require controls absent from the website."""

        elements = inspection.get("interactive_elements", [])

        for step in workflow["steps"]:
            normalized_step = self._normalize(step)

            if "link" in normalized_step:
                if not self._has_matching_control(
                    step,
                    elements,
                    "link"
                ):
                    return (
                        f"Step references a link that was not discovered: "
                        f"'{step}'"
                    )

            if "button" in normalized_step:
                if not self._has_matching_control(
                    step,
                    elements,
                    "button"
                ):
                    return (
                        f"Step references a button that was not discovered: "
                        f"'{step}'"
                    )

        return None

    def _reject_workflow(self, workflow, reason):
        """Record a rejected workflow and its reason."""

        self.rejected_workflows.append({
            "workflow_id": workflow.get("workflow_id", "UNKNOWN"),
            "title": workflow.get("title", "Untitled workflow"),
            "reason": reason
        })

    def _add_login_prerequisite(self, workflow, inspection):
        """Make logout workflows executable from a fresh browser session."""

        uses_logout = (
            any(
                "logout" in self._normalize(step)
                for step in workflow["steps"]
            )
            or any(
                "logout" in self._normalize(element_id)
                for element_id in workflow["elements_used"]
            )
        )

        if not uses_logout:
            return None

        username_id, password_id, login_id = (
            self._get_login_controls(inspection)
        )

        if not all([username_id, password_id, login_id]):
            return (
                "Logout workflow requires login first, but the "
                "username, password or login button was not discovered."
            )

        normalized_steps = [
            self._normalize(step)
            for step in workflow["steps"]
        ]

        has_username_step = any(
            "username" in step or "email" in step
            for step in normalized_steps
        )

        has_password_step = any(
            "password" in step
            for step in normalized_steps
        )

        has_login_button_step = any(
            "login" in step
            for step in normalized_steps
        )

        if not (
            has_username_step
            and has_password_step
            and has_login_button_step
        ):
            login_steps = [
                "Enter username",
                "Enter password",
                "Click Login button",
                "Verify Welcome message"
            ]

            workflow["steps"] = login_steps + workflow["steps"]

        workflow["elements_used"] = list(dict.fromkeys(
            [
                username_id,
                password_id,
                login_id
            ] + workflow["elements_used"]
        ))

        return None

    def _validate_workflows(self, result, inspection):
        """Validate workflow schemas and filter unsupported journeys."""

        if not isinstance(result, dict):
            raise ValueError(
                "AI workflow response must be a dictionary."
            )

        if not isinstance(result.get("workflows"), list):
            raise ValueError(
                "AI workflow response must contain a workflows list."
            )

        available_ids = self._get_available_element_ids(inspection)

        workflow_ids = [
            workflow.get("workflow_id")
            for workflow in result["workflows"]
            if isinstance(workflow, dict)
        ]

        if len(workflow_ids) != len(set(workflow_ids)):
            raise ValueError("Workflow IDs must be unique.")

        valid_workflows = []
        self.rejected_workflows = []

        for workflow in result["workflows"]:

            # STEP 1: Validate the structure before semantic filtering.
            # Invalid AI output must raise jsonschema.ValidationError.
            validate(
                instance=workflow,
                schema=self.workflow_schema
            )

            # STEP 2: The workflow is structurally valid.
            # Now check whether it matches the inspected website.

            invalid_ids = [
                element_id
                for element_id in workflow["elements_used"]
                if element_id not in available_ids
            ]

            if invalid_ids:
                self._reject_workflow(
                    workflow,
                    "References undiscovered element(s): "
                    + ", ".join(str(element_id) for element_id in invalid_ids)
                )
                continue

            # STEP 3: Add login prerequisites to logout workflows.
            prerequisite_error = self._add_login_prerequisite(
                workflow,
                inspection
            )

            if prerequisite_error:
                self._reject_workflow(
                    workflow,
                    prerequisite_error
                )
                continue

            # STEP 4: Check button and link references.
            control_error = self._validate_workflow_controls(
                workflow,
                inspection
            )

            if control_error:
                self._reject_workflow(
                    workflow,
                    control_error
                )
                continue

            # STEP 5: Validate again after adding prerequisites.
            validate(
                instance=workflow,
                schema=self.workflow_schema
            )

            valid_workflows.append(workflow)

        if not valid_workflows:
            reasons = "\n".join(
                f"{item['workflow_id']}: {item['reason']}"
                for item in self.rejected_workflows
            )

            raise ValueError(
                "No valid workflows remain after website validation.\n"
                + reasons
            )

        result["workflows"] = valid_workflows

        return result

    def discover_workflows(self, inspection):
        """Generate workflows and filter out unsupported journeys."""

        if not isinstance(inspection, dict):
            raise ValueError(
                "Website inspection must be a dictionary."
            )

        if not inspection.get("url"):
            raise ValueError(
                "Website inspection is missing its URL."
            )

        elements = inspection.get("interactive_elements", [])

        if not elements:
            raise ValueError(
                "No interactive website elements were discovered."
            )

        available_ids = self._get_available_element_ids(inspection)

        if not available_ids:
            raise ValueError(
                "Discovered elements do not contain usable element IDs."
            )

        prompt = f"""
You are an expert software test architect.

Discover realistic, executable user workflows from this website.

WEBSITE INSPECTION:
{json.dumps(inspection, indent=2)}

AVAILABLE ELEMENT IDS:
{json.dumps(sorted(available_ids))}

DISCOVERED INTERACTIVE ELEMENTS:
{json.dumps(elements, indent=2)}

STRICT RULES:

1. Only use controls that actually exist in the inspection.
2. Never invent links, buttons, fields, pages or functionality.
3. Every elements_used entry must be an exact discovered element ID.
4. Do not invent forgot-password, registration, reset-password,
   search, payment or other unsupported features.
5. Do not reference IDs outside AVAILABLE ELEMENT IDS.
6. Describe expected outcomes as expectations, not proven facts.
7. Return between 1 and 5 distinct workflows.
8. Return valid JSON only.

IMPORTANT STATEFUL WORKFLOW RULE:

Every workflow must be executable from a fresh browser session.

If a workflow uses Logout, it MUST first include:
- Entering a username.
- Entering a password.
- Clicking the discovered Login button.
- Verifying the logged-in or welcome state.
- Clicking the discovered Logout button.
- Verifying the logged-out or login state.

Do not create a standalone logout workflow that clicks a hidden
logout button before logging in.

Return this structure:
{{
  "workflows": [
    {{
      "workflow_id": "WF_001",
      "title": "Short workflow title",
      "description": "User goal",
      "steps": [
        "First user action",
        "Second user action"
      ],
      "elements_used": [
        "actual-element-id"
      ],
      "expected_outcome": "Expected result"
    }}
  ]
}}
"""

        result = self.ollama_client.generate_json(prompt)

        return self._validate_workflows(result, inspection)