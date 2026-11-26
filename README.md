# \# AI-Powered Multi-Agent Test Automation Framework

# 

# An independent Python-based project exploring how multiple specialized agents can work together to automate software testing.

# 

# \## Project Overview

# 

# The goal is to develop a multi-agent framework that can read software requirements, design test scenarios, generate automated tests, execute them, analyze failures, and produce test reports.

# 

# The project is being developed incrementally using Python, Pytest, and Playwright.

# 

# \## Current Implementation

# 

# \### 1. Requirement Reader Agent

# 

# The first implemented module reads software requirements from Excel and CSV files.

# 

# \*\*Features:\*\*

# \- Reads `.xlsx` and `.csv` files.

# \- Validates required columns: `story\_id`, `title`, and `description`.

# \- Normalizes column names.

# \- Handles missing values.

# \- Filters out incomplete requirements.

# 

# \*\*Testing:\*\* Pytest test case implemented and passing.

# 

# \## Technology Stack

# 

# \- Python

# \- Pandas

# \- OpenPyXL

# \- Pytest

# \- Playwright

# \- Requests

# 

# \## Project Structure

# 

# ```text

# AI-Powered-Multi-Agent-Framework/

# ├── agents/

# │   ├── \_\_init\_\_.py

# │   └── requirement\_reader.py

# ├── config/

# ├── core/

# ├── generated\_tests/

# ├── logs/

# ├── reports/

# ├── tests/

# │   └── test\_requirement\_reader.py

# ├── user\_stories/

# │   └── requirements.xlsx

# ├── .gitignore

# └── requirements.txt

# ```

# 

# \## Run the Tests

# 

# Install dependencies:

# 

# ```bash

# pip install -r requirements.txt

# ```

# 

# Run the test suite:

# 

# ```bash

# python -m pytest -v

# ```

# 

# \## Planned Development

# 

# \- Test Design Agent

# \- LLM integration for intelligent test scenario generation

# \- Automated Test Generation Agent

# \- Playwright Test Execution Agent

# \- Failure Analysis Agent

# \- Test Reporting

# \- Multi-Agent Orchestration

# 

# \## Development Status

# 

# This project is under active development. Features listed under Planned Development are not yet implemented.

# 



