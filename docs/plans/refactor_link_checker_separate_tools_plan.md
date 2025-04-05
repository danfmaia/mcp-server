# Plan: Refactor Link Checker to Separate Tools

**Status:** In Progress

**Goal:** Refactor the `check-markdown-links` functionality into three separate tools (`check_markdown_link_file`, `check_markdown_link_files`, `check_markdown_link_directory`) to work around agent limitations with `oneOf` schemas and provide the originally intended bulk processing capabilities.

**References:**

- Original Requirements: `docs/requirements/link_checker_tool_enhancements_reqs.md`
- TDD Process: `.cursor/rules/tdd-process.mdc`
- Workflow Rules: `.cursor/rules/workflow.mdc`

**Execution Plan (Following TDD):**

1.  `[X]` **Branching:** Ensure the codebase reflects the state _after_ the initial bulk implementation (containing logic for `file_paths` and `directory_path`), possibly by checking out the relevant feature branch or merging changes. _(Assumed done by user)_
2.  `[X]` **Schema Refactor (`handle_list_tools`):**
    - In `src/mcp_server/server.py`, modify `handle_list_tools`.
    - Remove the single tool definition with `oneOf`.
    - Define three distinct `types.Tool` entries:
      - `check_markdown_link_file` (schema: `file_path: str`)
      - `check_markdown_link_files` (schema: `file_paths: list[str]`)
      - `check_markdown_link_directory` (schema: `directory_path: str`)
3.  `[X]` **Handler Refactor (`handle_call_tool`):**
    - In `src/mcp_server/server.py`, modify `handle_call_tool`.
    - Update the main `if/elif/else` block to check for the three new tool names.
    - Adapt the argument extraction logic for each tool.
    - **Path Handling:** Explicitly resolve `file_path` (for the `_file` tool) and paths within `file_paths` (for the `_files` tool) against the known project root (`/home/danfmaia/_repos/mcp-server`) before passing them to processing logic. Keep using `.resolve()` for `directory_path`.
    - Reuse existing processing and reporting logic where possible.
4.  `[X]` **Test Updates:**
    - In `tests/test_server.py`, refactor tests related to the link checker.
    - Rename tests for clarity (e.g., `test_handle_call_tool_file_success`, `test_handle_call_tool_files_success`, `test_handle_call_tool_directory_success`).
    - Update tests checking `handle_list_tools` to expect three separate tools with simple schemas.
    - Update call tool tests to invoke the correct new tool names and provide arguments accordingly.
    - Ensure all tests pass (`make test`).
5.  `[X]` **README Update:**
    - Modify `README.md`.
    - Remove documentation for the single `check-markdown-links` tool.
    - Add documentation sections for each of the three new tools, including their names, descriptions, simple input schemas, and example usages.
6.  `[ ]` **Agent Tool Test:** Verify that the AI agent (Gemini) can successfully call each of the three new tools with appropriate arguments (using absolute paths where necessary based on previous findings).
7.  `[ ]` **Final Checks:** Run `make lint` and `make test` again.
8.  `[ ]` **Mark Plan Complete:** Update the status of this plan file to `Completed`.

**Next Step:** Proceed with Step 6: Agent Tool Test (with caveats).
