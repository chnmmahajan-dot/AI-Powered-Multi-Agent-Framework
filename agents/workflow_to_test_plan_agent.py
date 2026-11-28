from agents.ai_test_plan_agent import AITestPlanAgent


class WorkflowToTestPlanAgent:
    """Converts discovered workflows into executable browser test plans."""

    def __init__(self, test_plan_agent=None):
        self.test_plan_agent = test_plan_agent or AITestPlanAgent()

    @staticmethod
    def _normalize(value):
        return "".join(
            character.lower()
            for character in str(value)
            if character.isalnum()
        )

    def _get_element_ids(self, inspection):
        return {
            element.get("id")
            for element in inspection.get("interactive_elements", [])
            if element.get("id")
        }

    def _get_login_controls(self, inspection):
        elements = inspection.get("interactive_elements", [])

        controls = {
            "username": None,
            "password": None,
            "login": None,
            "logout": None,
        }

        for element in elements:
            element_id = self._normalize(element.get("id", ""))
            element_text = self._normalize(element.get("text", ""))

            if element_id in {"username", "email"}:
                controls["username"] = element.get("id")

            elif element_id == "password":
                controls["password"] = element.get("id")

            elif (
                element_id in {"loginbutton", "signinbutton"}
                or (
                    element.get("tag") == "button"
                    and element_text in {"login", "signin"}
                )
            ):
                controls["login"] = element.get("id")

            elif (
                element_id in {"logoutbutton", "signoutbutton"}
                or (
                    element.get("tag") == "button"
                    and element_text in {"logout", "signout"}
                )
            ):
                controls["logout"] = element.get("id")

        return controls

    def _prepare_workflow(self, workflow, inspection):
        """Prepare a reliable login/logout sequence."""

        combined_steps = self._normalize(
            " ".join(workflow["steps"])
            + " "
            + workflow["title"]
            + " "
            + workflow["description"]
        )

        is_logout_workflow = "logout" in combined_steps

        is_login_workflow = (
            "login" in combined_steps
            or "signin" in combined_steps
            or "welcome" in combined_steps
            or is_logout_workflow
        )

        is_negative_workflow = any(
            keyword in combined_steps
            for keyword in [
                "invalidcredentials",
                "incorrectcredentials",
                "wrongpassword",
                "invalidpassword",
                "incorrectpassword",
                "wrongusername",
                "invalidusername",
            ]
        )

        if not is_login_workflow or is_negative_workflow:
            return workflow

        controls = self._get_login_controls(inspection)

        required_controls = ["username", "password", "login"]

        missing_controls = [
            control
            for control in required_controls
            if not controls[control]
        ]

        if missing_controls:
            raise ValueError(
                "Cannot prepare login workflow. Missing discovered "
                f"controls: {missing_controls}"
            )

        prepared_workflow = workflow.copy()

        prepared_workflow["steps"] = [
            "Enter the username into the username field",
            "Enter the password into the password field",
            "Click the Login button",
            "Verify that the Welcome message is visible",
        ]

        prepared_workflow["elements_used"] = list(dict.fromkeys(
            workflow["elements_used"]
            + [
                controls["username"],
                controls["password"],
                controls["login"],
            ]
        ))

        if is_logout_workflow:
            if not controls["logout"]:
                raise ValueError(
                    "Cannot prepare logout workflow. "
                    "The logout button was not discovered."
                )

            prepared_workflow["steps"].extend([
                "Click the Logout button",
                "Verify that the Login button is visible after logout",
            ])

            prepared_workflow["elements_used"].append(
                controls["logout"]
            )

            prepared_workflow["title"] = (
                "Complete Login and Logout Workflow"
            )

            prepared_workflow["expected_outcome"] = (
                "The user successfully logs in, sees the Welcome message, "
                "logs out, and returns to the logged-out state where "
                "the Login button is visible."
            )

        else:
            prepared_workflow["title"] = (
                "User Login and Welcome Verification"
            )

            # Keep the original expected outcome unchanged.
            prepared_workflow["expected_outcome"] = (
                workflow["expected_outcome"]
            )

        return prepared_workflow

    def generate_test_plan_for_workflow(
        self,
        workflow,
        inspection,
        test_data=None,
    ):
        """Convert one discovered workflow into an executable test plan."""

        if not isinstance(workflow, dict):
            raise ValueError("Workflow must be a dictionary.")

        required_fields = [
            "workflow_id",
            "title",
            "description",
            "steps",
            "elements_used",
            "expected_outcome",
        ]

        for field in required_fields:
            if field not in workflow:
                raise ValueError(
                    f"Workflow is missing required field: '{field}'."
                )

        if (
            not isinstance(workflow["steps"], list)
            or not workflow["steps"]
        ):
            raise ValueError(
                "Workflow must contain at least one step."
            )

        if not isinstance(inspection, dict) or not inspection.get("url"):
            raise ValueError(
                "A valid website inspection is required."
            )

        if not isinstance(workflow["elements_used"], list):
            raise ValueError(
                "Workflow elements_used must be a list."
            )

        discovered_ids = self._get_element_ids(inspection)

        for element_id in workflow["elements_used"]:
            if element_id not in discovered_ids:
                raise ValueError(
                    f"Workflow references an undiscovered element: "
                    f"'{element_id}'."
                )

        prepared_workflow = self._prepare_workflow(
            workflow,
            inspection,
        )

        controls = self._get_login_controls(inspection)

        effective_test_data = dict(test_data or {})

        if controls["username"] and controls["password"]:
            effective_test_data.setdefault("username", "admin")
            effective_test_data.setdefault("password", "password123")

        instructions = f"""
You are an expert Playwright test automation engineer.

Convert the supplied workflow into ONE executable browser test plan.

APPLICATION URL:
{inspection["url"]}

WORKFLOW TITLE:
{prepared_workflow["title"]}

ORIGINAL DISCOVERED WORKFLOW:
{workflow["steps"]}

PREPARED EXECUTION STEPS:
{prepared_workflow["steps"]}

EXPECTED OUTCOME:
{prepared_workflow["expected_outcome"]}

DISCOVERED ELEMENT IDS:
{sorted(discovered_ids)}

LOGIN CONTROL IDS:
{controls}

TEST DATA:
{effective_test_data}

WEBSITE INSPECTION:
{inspection}

STRICT EXECUTION RULES:

1. Generate a navigate action first using the application URL.

2. For username entry, use the fill action with the discovered
   username field and username from test data.

3. For password entry, use the fill action with the discovered
   password field and password from test data.

4. Click Login only after both fields have been filled.

5. Verify the Welcome message only after clicking Login.

6. For logout, click the discovered Logout button only after
   successful login.

7. After logout, verify that the LOGIN BUTTON is visible.
   Use the discovered login button ID as the locator.

8. NEVER verify that the Logout button is visible after logout.

9. NEVER click Login before entering the username and password.

10. Use only discovered website elements and supported browser actions.

11. Do not invent URLs, credentials, buttons, fields or functionality.

12. Preserve the order of the prepared execution steps.

13. Return one valid test plan matching the test plan schema.

The prepared execution steps are authoritative for execution.
"""

        requirement = {
            "requirement_id": prepared_workflow["workflow_id"],
            "description": prepared_workflow["description"],
            "application_url": inspection["url"],
            "workflow_title": prepared_workflow["title"],
            "workflow_steps": workflow["steps"],
            "prepared_workflow_steps": prepared_workflow["steps"],
            "expected_outcome": prepared_workflow["expected_outcome"],
            "elements_used": prepared_workflow["elements_used"],
            "website_inspection": inspection,
            "test_data": effective_test_data,
            "instructions": instructions,
        }

        return self.test_plan_agent.generate_test_plan(requirement)