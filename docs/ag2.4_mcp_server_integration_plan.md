# Integration Plan: MCP Server with Cursor

**Date:** 2025-04-04
**Agent:** Developer Agent (Instance 4)
**Goal:** Configure Cursor to use the custom `mcp-tools` server and test the `check-markdown-links` tool.

## Final Working Configuration Steps

_(Note: Previous steps involving simpler configurations or shell commands failed due to Cursor's execution environment on Linux. The following configuration using direct `uv run` with absolute paths is required.)_

1.  **Enable MCP in Cursor:**

    - [x] Navigate to `Cursor Settings > Features` (Human)
    - [x] Ensure the `MCP Servers` feature is enabled (Human)

2.  **Determine Absolute Paths:**

    - [ ] In your activated **project** virtual environment, run `which uv` to get the absolute path to the `uv` executable (e.g., `/home/user/project/.venv/bin/uv`). (Human)
    - [ ] Determine the absolute path to the `tools/mcp_server` directory within your project (e.g., `/home/user/project/tools/mcp_server`). (Human)

3.  **Configure Server in Cursor:**

    - [x] Locate or create the global MCP JSON configuration file at `~/.cursor/mcp.json` (Human)
    - [x] Add/Update the server entry using the **exact** absolute paths determined above (Human):
      ```json
      {
        "mcpServers": {
          "local-link-checker": {
            "name": "Local Link Checker",
            "type": "command",
            "command": "/absolute/path/to/.venv/bin/uv", // <-- From step 2
            "args": [
              "run",
              "--directory",
              "/absolute/path/to/tools/mcp_server", // <-- From step 2
              "mcp_server"
            ]
          }
        }
      }
      ```

4.  **Restart Cursor:**

    - [x] Close and reopen Cursor to ensure it loads the updated MCP server configuration (Human)

5.  **Test Tool in Cursor:**
    - [x] Open a chat or activate the Agent within Cursor (Human)
    - [ ] Invoke the tool using the `@` symbol (e.g., `@Local Link Checker`) and providing the `file_path` argument **relative to the `tools/mcp_server` directory** (Human):
          Example: `@Local Link Checker file_path:test_links.md`
    - [ ] Observe the output provided by the Agent; verify it matches the expected report format (Human)
    - [ ] (Optional) Check the server startup logs (`tools/mcp_server/src/mcp_server/mcp_server_startup.log`) if issues occur. (Human)
