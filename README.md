# MCP Server (mcp-tools)

This project contains a general MCP server designed to provide tools for AI agents, communicating via stdin/stdout using the Model Context Protocol (MCP).

## Available Tools

### 1. Markdown Link Checker

- **Tool Name:** `check-markdown-links`
- **Description:** Reads a Markdown file, extracts all HTTP and HTTPS links (both explicit `[text](url)` and bare URLs), checks their status (handling redirects), and reports the findings.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Absolute or relative path to the Markdown file."
      }
    },
    "required": ["file_path"]
  }
  ```
- **Output Format:** A plain text report summarizing the findings.
  ```text
  Link Check Report for: <input_file_path>
  Total Links Found: <count>
  Valid Links (<count>):
    - <url>
    ...
  Broken Links (<count>):
    - <url> (Reason: <status_code/reason>)
    ...
  Errored Links (<count>):
    - <url> (Reason: <error_type/message>)
    ...
  ```

## Setup & Usage (Using Makefile)

This project uses `uv` for environment and dependency management, orchestrated via a `Makefile`.

1.  **Navigate to the project directory:**
    Ensure you are in the root directory of *this* project (`mcp-server`).
    ```bash
    cd /path/to/mcp-server 
    ```

2.  **Install dependencies (including dev/test):**
    This command creates a local virtual environment (`.venv`) if it doesn't exist and installs all necessary packages using `uv`.

    ```bash
    make install-dev
    ```

3.  **Run Tests & Coverage:**

    ```bash
    make test
    ```

    This command runs all unit tests using `pytest` and generates a code coverage report using `coverage.py`.

    - The test run is configured to **fail if the total coverage drops below 85%** (see `Makefile`).
    - As of 2025-04-04, the coverage status is:
      - Overall: 85%
      - `src/mcp_server/server.py`: 81% (Main handlers covered; `main` loop untested)
      - `src/mcp_server/tools/link_checker.py`: 89% (Core logic covered; some edge cases in status checking untested)

4.  **Lint & Format Code:**
    Uses `ruff` to check for linting errors and format the code according to project standards.
    ```bash
    make lint
    ```

5.  **Run the Server (Manually):**
    The server listens on stdin/stdout.

    ```bash
    make run
    ```

    _(Note: Manual interaction requires sending correctly framed JSON-RPC messages, including `initialize` and `initialized` before `call_tool`.)_

6.  **Clean Up:**
    Removes the virtual environment and cache files.
    ```bash
    make clean
    ```

## Cursor MCP Integration (Linux)

This server can be integrated with Cursor as an MCP tool using the following global configuration in `~/.cursor/mcp.json` (you may need to create this file/directory):

```json
{
  "mcpServers": {
    "local-link-checker": {
      "name": "Local Link Checker", // Name displayed in Cursor
      "type": "command",
      // Use the absolute path to the python executable within THIS project's venv
      "command": "/absolute/path/to/mcp-server/.venv/bin/python", 
      "args": [
        "-m",                   // Run module
        "mcp_server.server"     // The server module to run
      ],
      // Optional: Define the working directory if needed (usually handled by -m)
      // "cwd": "/absolute/path/to/mcp-server"
    }
  }
}
```

**Important Notes for Integration:**

-   **Absolute Paths:** You MUST replace `/absolute/path/to/mcp-server` with the correct, absolute path to this project's directory on your system.
-   **Virtual Environment:** This configuration assumes you have run `make install-dev` first to create the `.venv` and install dependencies within this project directory.
-   **Working Directory & File Paths:** When run via `python -m`, the server's working directory is typically the project root (`/absolute/path/to/mcp-server`). Therefore, when invoking the tool (e.g., `@Local Link Checker`), the `file_path` argument should be relative to this project root (e.g., `file_path: test_links.md` for a file at the root) or an absolute path.
-   **Restart Cursor:** After adding or modifying `~/.cursor/mcp.json`, you must restart Cursor for the changes to take effect.

_Previous integration attempts using different methods (like `uv run` or shell wrappers) failed due to issues with Cursor's process execution environment on Linux. The direct `python -m` approach using the project's own virtual environment is the configuration proven to work._

## Adding New Tools

1.  Define the tool's schema in `handle_list_tools` (`src/mcp_server/server.py`).
2.  Implement the tool's logic under a new `elif name == "your-tool-name":` block in `handle_call_tool` (`src/mcp_server/server.py`).
    - Create helper functions in separate files under `src/mcp_server/tools/` as needed.
    - Add unit tests for the helper functions in `tests/`.
3.  Add any new dependencies to `pyproject.toml`.
4.  Update the `install-dev` target in the `Makefile` if new _test-only_ dependencies are added (base dependencies should be handled by `uv sync` within `install-dev`).
5.  Update this README.
