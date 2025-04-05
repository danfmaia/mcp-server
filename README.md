# MCP Server (mcp-tools)

This project contains a general MCP server designed to provide tools for AI agents, communicating via stdin/stdout using the Model Context Protocol (MCP).

## Tools Provided

The server currently offers the following tools, callable via the `call_tool` endpoint:

### `check_markdown_link_file`

- **Description:** Checks HTTP/HTTPS links in a single specified Markdown file.
- **Arguments:**
  - `file_path` (string, required): The path to the Markdown file (relative to the project root or absolute).
- **Example `arguments`:**
  ```json
  {
    "file_path": "docs/usage.md"
  }
  ```
- **Output:** A text report detailing the status of links found in the file (total, valid, broken, errors).

### `check_markdown_link_files`

- **Description:** Checks HTTP/HTTPS links within a provided list of Markdown files.
- **Arguments:**
  - `file_paths` (list of strings, required): A list of paths to the Markdown files (relative to the project root or absolute).
- **Example `arguments`:**
  ```json
  {
    "file_paths": [
      "README.md",
      "docs/requirements/link_checker_tool_enhancements_reqs.md"
    ]
  }
  ```
- **Output:** A consolidated text report summarizing the link status across all processed files.

### `check_markdown_link_directory`

- **Description:** Recursively scans a specified directory for `*.md` files and checks HTTP/HTTPS links within them.
- **Arguments:**
  - `directory_path` (string, required): The path to the directory to scan.
- **Example `arguments`:**
  ```json
  {
    "directory_path": "docs/"
  }
  ```
- **Output:** A consolidated text report summarizing the link status across all Markdown files found in the directory.

## Setup & Usage (Using Makefile)

This project uses `uv` for environment and dependency management, orchestrated via a `Makefile`.

1.  **Navigate to the project directory:**
    Ensure you are in the root directory of _this_ project (`mcp-server`).

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
        "-m", // Run module
        "mcp_server.server" // The server module to run
      ]
      // Optional: Define the working directory if needed (usually handled by -m)
      // "cwd": "/absolute/path/to/mcp-server"
    }
  }
}
```

**Important Notes for Integration:**

- **Absolute Paths:** You MUST replace `/absolute/path/to/mcp-server` with the correct, absolute path to this project's directory on your system.
- **Virtual Environment:** This configuration assumes you have run `make install-dev` first to create the `.venv` and install dependencies within this project directory.
- **Working Directory & File Paths:** When run via `python -m`, the server's working directory is typically the project root (`/absolute/path/to/mcp-server`). Therefore, when invoking the tool (e.g., `@Local Link Checker`), the `file_path` argument should be relative to this project root (e.g., `file_path: test_links.md` for a file at the root) or an absolute path.
- **Restart Cursor:** After adding or modifying `~/.cursor/mcp.json`, you must restart Cursor for the changes to take effect.

_Previous integration attempts using different methods (like `uv run` or shell wrappers) failed due to issues with Cursor's process execution environment on Linux. The direct `python -m` approach using the project's own virtual environment is the configuration proven to work._

## Adding New Tools

1.  Define the tool's schema in `handle_list_tools` (`src/mcp_server/server.py`).
2.  Implement the tool's logic under a new `elif name == "your-tool-name":` block in `handle_call_tool` (`src/mcp_server/server.py`).
    - Create helper functions in separate files under `src/mcp_server/tools/` as needed.
    - Add unit tests for the helper functions in `tests/`.
3.  Add any new dependencies to `pyproject.toml`.
4.  Update the `install-dev` target in the `Makefile` if new _test-only_ dependencies are added (base dependencies should be handled by `uv sync` within `install-dev`).
5.  Update this README.

## Contributing

Contributions are welcome! Please follow standard coding practices and ensure tests pass (`make test`) before submitting pull requests.

## License

[Specify your license here]
