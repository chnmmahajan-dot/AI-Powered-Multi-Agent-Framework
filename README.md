# AI-Powered Multi-Agent Test Automation Framework

An independent Python-based project that explores how specialized agents can collaborate to automate the software testing lifecycle.

## Project Overview

This project aims to build a modular test automation framework that processes software requirements, designs test scenarios, generates Playwright test scripts, executes tests, and eventually analyzes failures and produces reports.

The framework is developed incrementally using Python, Pytest, and Playwright, with future plans to integrate a local Large Language Model (LLM) for intelligent test generation.

## Implemented Features

### 1. Requirement Reader Agent
Reads and validates software requirements from Excel and CSV files.

**Features:**
- Supports `.xlsx` and `.csv` formats.
- Validates required columns: `story_id`, `title`, and `description`.
- Normalizes column names.
- Handles missing values.
- Filters incomplete requirements.

### 2. Test Design Agent
Generates test scenarios from the processed requirements using predefined templates.

**Features:**
- Generates positive test scenarios.
- Generates negative test scenarios.
- Generates edge-case test scenarios.
- Assigns unique test case IDs.
- Associates scenarios with their original requirements.

### 3. Test Generation Agent
Converts generated test scenarios into Python Playwright test files.

**Features:**
- Generates individual Python test files.
- Creates structured Pytest test functions.
- Uses Playwright's `Page` fixture.
- Stores generated tests in the `generated_tests/` directory.

**Current limitation:** Generated tests are browser-fixture smoke-test skeletons. Actual application-specific UI interactions and business validations are planned for future development.

### 4. Test Execution Agent
Executes generated test files using Pytest through Python subprocess execution.

**Features:**
- Discovers generated test files.
- Executes tests using the project's Python environment.
- Captures standard output and error output.
- Returns execution status and exit code.

### 5. Multi-Agent Orchestrator
Coordinates the implemented agents and manages the complete automation pipeline.

**Pipeline:**

1. Read requirements from Excel.
2. Generate test scenarios.
3. Generate Playwright test files.
4. Execute generated tests.
5. Return execution results.

## Technology Stack

- Python
- Pandas
- OpenPyXL
- Pytest
- Playwright
- pytest-playwright
- Git and GitHub

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
├── core/
│   └── orchestrator.py
│
├── config/
│
├── generated_tests/
│   └── .gitkeep
│
├── logs/
│
├── reports/
│
├── tests/
│   ├── test_requirement_reader.py
│   ├── test_test_design_agent.py
│   ├── test_test_generation_agent.py
│   ├── test_test_execution_agent.py
│   └── test_orchestrator.py
│
├── user_stories/
│   └── requirements.xlsx
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- Windows, macOS, or Linux

### 1. Clone the repository

```bash
git clone https://github.com/chnmmahajan-dot/AI-Powered-Multi-Agent-Framework.git

cd AI-Powered-Multi-Agent-Framework
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install the Playwright Chromium browser

```bash
python -m playwright install chromium
```

### 5. Run the complete automation pipeline

```bash
python main.py
```

### 6. Run the test suite

```bash
python -m pytest -v
```

## Current Test Results

The current implementation has been validated with:

- 14 passing tests.
- Requirement processing tests.
- Test scenario generation tests.
- Test file generation tests.
- Test execution agent tests.
- Orchestrator integration tests.
- Playwright Chromium smoke tests.

## Planned Improvements

- Integrate a local LLM using Ollama.
- Improve requirement understanding and intelligent test scenario generation.
- Generate application-specific Playwright tests.
- Implement automated failure analysis.
- Introduce structured test execution reports.
- Improve logging and execution traceability.
- Expand multi-agent collaboration.

## Development Status

This project is under active development.

The current implementation uses deterministic, rule-based test scenario generation. LLM-powered reasoning, application-specific end-to-end validation, failure analysis, and reporting are planned enhancements.

The framework is being built incrementally, with an emphasis on modular design, testability, and maintainability.
