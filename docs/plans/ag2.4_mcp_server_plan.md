# Implementation Plan: General MCP Server (Initial Tool: Link Checker)

**Date:** 2025-04-03
**Agent:** Developer Agent (Instance 4)
**Goal:** Create a general MCP server, initially exposing a tool to check links within Markdown files.
**Reference Analysis:** `ag2.4_mcp_reference_analysis.md`
**Status:** In Progress

## 1. Project Setup

| Step                         | Status |
| :--------------------------- | :----- |
| 1.1 Create Project Directory | Done   |
| 1.2 Scaffold Project         | Done   |
| 1.3 Initialize Environment   | Done   |
| 1.4 Add Dependencies         | Done   |

**Details:**

1.  **Create Project Directory:** Create `tools/mcp_server/`.
2.  **Scaffold Project:** Use the `create-mcp-server` tool (or manually replicate its structure) within `tools/mcp_server/`.
    - Name: `mcp_server`
3.  **Initialize Environment:** `cd tools/mcp_server && uv venv && uv sync --dev`
4.  **Add Dependencies:** `uv add markdown-it-py requests beautifulsoup4` (or alternative libs).

## 2. Implement Link Checker Tool (TDD)

| Step                                  | Status                   |
| :------------------------------------ | :----------------------- |
| 2.1 Setup Testing Framework           | Done                     |
| 2.2 Write Link Extraction Test (Red)  | Done                     |
| 2.3 Implement Link Extraction (Green) | Done (Using markdown-it) |
| 2.4 Refactor Link Extraction          | Needs Review             |
| 2.5 Write Link Checking Test (Red)    | Done                     |
| 2.6 Implement Link Checking (Green)   | Done (Manual Redirects)  |
| 2.7 Refactor Link Checking            | Needs Review             |
| 2.8 Integrate Logic into Server       | Done                     |
| 2.9 Remove Unused Capabilities        | Done                     |
| 2.10 Configure Main                   | Done                     |

**Details:**

1.  **Setup Testing Framework:**
    - Add `pytest`, `pytest-asyncio` to `[project.optional-dependencies.test]` in `pyproject.toml`.
    - Run `uv sync --all-extras`.
    - Create `tests/` directory.
    - **Note:** A `Makefile` was later introduced to standardize environment setup and test execution (`make install-dev`, `make test`) due to environment/dependency issues encountered during development.
2.  **Write Link Extraction Test (Red):**
    - Create `tests/test_link_checker.py`.
    - Write a test function (e.g., `test_extracts_simple_http_link`) that asserts a known link is extracted from a sample Markdown string. Use a placeholder function import.
    - Verify the test fails (e.g., `uv run pytest tests/`).
3.  **Implement Link Extraction (Green):**
    - Create `src/mcp_server/tools/link_checker.py` with `_extract_links`.
    - Write minimal code using `markdown-it-py` or regex to make `test_extracts_simple_http_link` pass.
4.  **Refactor Link Extraction:** Clean up the extraction code and test.
5.  **Write Link Checking Test (Red):**
    - Add a test (e.g., `test_checks_valid_link`) using `pytest.mark.asyncio`.
    - Mock `requests.head` or `requests.get` to return a 200 status.
    - Assert the link is reported as valid by a new placeholder function (e.g., `_check_link_status`).
    - Verify the test fails.
6.  **Implement Link Checking (Green):** Implemented `_check_link_status` with `aiohttp`. Required manual redirect handling as `allow_redirects=True` didn't work reliably with `aioresponses` mocking.
7.  **Refactor Link Checking:** Required significant troubleshooting for `aioresponses` fixture loading. Workaround: manual instantiation (`with aioresponses():`) used instead of fixture injection. Code now ready for refactoring review.
8.  **Integrate Logic into Server:**
    - Modify `handle_call_tool` in `server.py` to call helper functions from `tools.link_checker`.
    - Handle file reading and error checking (`file_path` exists).
    - Format the final result string.
9.  **Remove Unused Capabilities:** Remove example resource/prompt handlers from `server.py`.
10. **Configure Main:** Ensure `main()` in `server.py` is correctly configured.

## 3. Testing (Server Level)

| Step                               | Status                |                                             |
| :--------------------------------- | :-------------------- | :------------------------------------------ |
| 3.1 Manual Test                    | Skipped (Impractical) | # Protocol framing blocks simple stdin test |
| 3.2 Configure and Test with Cursor | Pending               |                                             |

**Details:**

1.  **Manual Test:** Attempted manual test via stdin piping (`cat ... | make run`), but server hangs waiting for initialization. MCP protocol requires specific message framing (`Content-Length` headers) which is impractical to simulate reliably via basic shell commands. Requires a proper MCP client or dedicated integration test.
2.  **Configure and Test with Cursor:**
    - Ensure MCP is enabled in Cursor Settings (`Features > MCP Servers`).
    - Create/edit the MCP JSON configuration file (e.g., `~/.cursor-mcp/servers.json`).
    - Add an entry for this server:
      ```json
      {
        "name": "Local Link Checker",
        "type": "command",
        "serverURL": "cd /path/to/career-agent/tools/mcp_server && make run" // Replace with actual absolute path
      }
      ```
    - Restart Cursor.
    - Test by invoking `@check-markdown-links` in Cursor Chat/Agent with the path to `test_links.md`.

## 4. Documentation

| Step                 | Status |
| :------------------- | :----- |
| 4.1 Update README.md | Done   |

**Details:**

1.  **Update `README.md`:** Add purpose, install, run instructions (`uv run mcp_server`), tool details.

## 5. Next Steps / Future Enhancements

_(No status tracking needed here)_

- Input Markdown content directly instead of file path.
- Caching results.
- Ignoring specific domains/links.
- Support for relative links (requires base URL context).
- More robust error handling and reporting.
