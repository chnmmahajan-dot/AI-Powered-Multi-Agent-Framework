# AI-Powered Multi-Agent Test Automation Framework

A Python-based multi-agent test automation framework that uses a local Large Language Model (LLM) to design software test scenarios, generates executable Playwright tests, and runs them through an automated testing pipeline.

The project demonstrates how specialized agents can collaborate across different stages of the software testing lifecycle.

## Project Overview

The framework accepts software requirements from Excel or CSV files and processes them through a sequence of specialized agents.

A locally running LLM (Ollama with Llama 3.2) is used by the Test Design Agent to generate structured test scenarios. The Test Generation Agent converts supported scenarios into executable Playwright scripts, which are then executed by the Test Execution Agent.

An orchestrator coordinates the complete workflow and saves structured JSON execution reports.

## Architecture

```text
              Software Requirements
                 (Excel / CSV)
                       |
                       v
             Requirement Reader Agent
                       |
                       v
                Test Design Agent
                 (Ollama LLM)
                       |
                       v
              Test Generation Agent
                (Playwright)
                       |
                       v
              Test Execution Agent
                  (Pytest)
                       |
                       v
             Execution Results
                       |
                       v
              JSON Execution Report

          Test Automation Orchestrator
             Coordinates all agents
```

## Implemented Features

### 1. Requirement Reader Agent

Reads and validates software requirements from Excel and CSV files.

Features:
- Supports `.xlsx` and `.csv` formats.
- Validates required columns: `story_id`, `title`, and `description`.
- Normalizes column names.
- Handles missing values.
- Filters incomplete requirements.

### 2. Test Design Agent

Uses a locally hosted LLM through Ollama to generate structured test scenarios from software requirements.

Features:
- Integrates the Llama 3.2 model through Ollama.
- Generates structured JSON responses.
- Produces one scenario per requirement.
- Supports positive and negative login scenarios.
- Associates generated scenarios with their original requirements.
- Validates AI responses and rejects unsupported actions or incomplete scenarios.
- Maintains consistent test case IDs.

### 3. Test Generation Agent

Converts validated scenarios into executable Python Playwright test files.

Features:
- Generates individual test files.
- Uses Playwright's `Page` fixture and assertions.
- Supports successful login, unsuccessful login, and logout workflows.
- Validates scenarios before replacing previously generated test files.
- Stores generated tests in `generated_tests/`.

**Implementation detail:** The LLM designs the test scenarios, while the generation agent uses predefined Playwright templates for the supported actions. The framework does not currently generate arbitrary Playwright code using the LLM.

### 4. Test Execution Agent

Executes generated test files using Pytest through Python subprocess execution.

Features:
- Discovers generated test files.
- Executes tests using the active Python environment.
- Captures standard output and error output.
- Collects passed, failed, skipped, and other execution counts.
- Measures execution duration.
- Applies a 300-second execution timeout.
- Returns execution status and exit code.

### 5. Multi-Agent Orchestrator

Coordinates all agents and manages the complete automation pipeline.

Pipeline:
1. Read requirements from Excel or CSV.
2. Generate test scenarios using the local LLM.
3. Validate the generated scenarios.
4. Generate Playwright test files.
5. Execute generated tests using Pytest.
6. Collect execution metrics.
7. Save a timestamped JSON execution report.

### 6. Automated Execution Reporting

The orchestrator generates timestamped JSON reports under `reports/`.

Reports include:
- Execution timestamp and overall status.
- Requirements processed.
- Scenarios generated.
- Test files generated and discovered.
- Total, passed, failed, and skipped tests.
- Execution duration and return code.
- Generated scenarios and test filenames.
- Pytest execution output and errors.

### 7. CI/CD Integration

The project includes a GitHub Actions workflow.

Implemented capabilities:
- Runs automatically on pushes and pull requests to `main`.
- Sets up Python 3.13.
- Installs project dependencies.
- Installs Playwright Chromium.
- Starts the demo application.
- Runs the selected automated test suites.
- Uploads test artifacts.

The GitHub Actions workflow runs the tests that do not require a locally hosted Ollama model. LLM-dependent integration tests are validated separately in the local development environment.

## Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python |
| AI / LLM | Ollama, Llama 3.2 |
| Test framework | Pytest |
| Browser automation | Playwright |
| Data processing | Pandas |
| Excel support | OpenPyXL |
| Process execution | Python subprocess |
| CI/CD | GitHub Actions |
| Version control | Git and GitHub |

## Project Structure

```text
AI-Powered-Multi-Agent-Framework/
│
├── agents/
│   ├── __init__.py
│   ├── requirement_reader.py
│   ├── test_design_agent.py
│   ├── test_generation_agent.py
│   └── test_execution_agent.py
│
├── config/
│   └── settings.py
│
├── core/
│   ├── orchestrator.py
│   └── ollama_client.py
│
├── demo_app/
│   └── index.html
│
├── generated_tests/
│   └── .gitkeep
│
├── reports/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── tests/
│   ├── test_demo_login.py
│   ├── test_requirement_reader.py
│   ├── test_test_design_agent.py
│   ├── test_test_generation_agent.py
│   ├── test_test_execution_agent.py
│   └── test_orchestrator.py
│
├── user_stories/
│   └── requirements.xlsx
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.10 or later.
- Git.
- Ollama.
- Llama 3.2 model.
- Playwright-supported Chromium browser.

### 1. Clone the repository

```bash
git clone https://github.com/chnmmahajan-dot/AI-Powered-Multi-Agent-Framework.git

cd AI-Powered-Multi-Agent-Framework
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install Playwright Chromium

```bash
python -m playwright install chromium
```

### 5. Set up Ollama

Install Ollama, then download the Llama 3.2 model:

```bash
ollama pull llama3.2
```

Ensure the Ollama service is running before executing the LLM-dependent pipeline.

### 6. Start the demo application

Open a separate terminal from the project directory and run:

```powershell
python -m http.server 8000 --directory demo_app
```

The demo application will be available at:

`http://127.0.0.1:8000`

Keep this terminal running while executing browser tests.

### 7. Run the complete automation pipeline

From the project terminal:

```powershell
python main.py
```

The pipeline reads requirements, generates AI-designed scenarios, creates Playwright tests, executes them, and saves a JSON report.

### 8. Run the complete test suite

With the demo server and Ollama running:

```powershell
python -m pytest .\tests -v
```

## Current Validation Results

Latest local validation:

| Validation | Result |
|---|---:|
| Complete regression suite | 8 passed |
| Requirements processed | 3 |
| AI scenarios generated | 3 |
| Playwright test files generated | 3 |
| Generated browser tests passed | 3/3 |
| Failed generated tests | 0 |

The complete pipeline was also executed successfully using `python main.py`.

**Note:** These are local development results. The GitHub Actions workflow runs a separate CI-compatible subset that does not require Ollama.

## Current Limitations

- The LLM currently selects from three supported login-related actions.
- Playwright test code is generated using predefined templates rather than arbitrary AI-generated code.
- The demo login application is a simple client-side demonstration, not a production authentication system.
- Failure classification and AI-powered root-cause analysis are not yet implemented.
- LLM-dependent integration tests require a locally available Ollama model.

## Future Improvements

- Expand supported application workflows and test actions.
- Improve requirement understanding and scenario coverage.
- Add AI-assisted failure analysis and root-cause suggestions.
- Introduce richer execution reports and logging.
- Improve test generation for different application types.
- Expand CI/CD coverage for LLM-dependent workflows.

## Development Status

The core multi-agent automation pipeline is implemented and locally validated.

The project focuses on modular agent design, local LLM integration, browser automation, automated execution, input validation, and CI/CD practices.

Built independently as a hands-on project to explore AI-assisted software test automation.