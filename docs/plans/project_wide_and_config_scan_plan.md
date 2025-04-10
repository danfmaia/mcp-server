# Plan: Add Project-Wide and Config-Based Link Scanning

**Status:** Part 1 Complete

**Goal:** Enhance the link checker tools with two new functionalities:

1.  Scan all `.md` files within the project root, excluding files/directories specified in the project's `.gitignore`.
2.  Scan a list of files and/or directories specified in a configuration file.

**References:**

- TDD Process: `.cursor/rules/tdd-process.mdc`
- Workflow Rules: `.cursor/rules/workflow.mdc`
- Previous Plan: `docs/plans/refactor_link_checker_separate_tools_plan.md`

**Execution Plan (Following TDD):**

**Part 1: Project-Wide Scan (Respecting `.gitignore`)**

1.  `[X]` **Dependency:** ~~Add `gitignore-parser` to `pyproject.toml` (`project.dependencies` and `tool.uv.sources`).~~ (Attempted `gitignore-parser`, removed due to runtime issues; implementing manual filtering).
2.  `[X]` **Environment Update:** User runs `make install-dev` to install the new dependency.
3.  `[X]` **Define Tool:** Add `check_markdown_links_project` tool definition (no arguments) to `handle_list_tools` in `src/mcp_server/server.py`.
4.  `[X]` **Implement Handler Logic:**
    - Add an `elif` block for `check_markdown_links_project` in `handle_call_tool`.
    - Use `pathlib.Path.rglob("*.md")` starting from `PROJECT_ROOT`.
    - ~~Safely read and parse `.gitignore` at `PROJECT_ROOT` using `gitignore_parser`.~~
    - ~~Filter the found `.md` files using the parser's `matches` method.~~
    - Implement manual filtering: Define common ignored directory prefixes (e.g., `.venv/`, `ref_repos/`, `.pytest_cache/`). Filter `rglob` results by checking if a file's relative path `startswith` any ignored prefix.
    - Pass the filtered list of absolute paths to the existing centralized processing logic.
    - Ensure a consolidated report is generated.
5.  `[X]` **Add Tests:**
    - In `tests/test_server.py`, add new tests specifically for `check_markdown_links_project`.
    - ~~Include tests mocking `.gitignore` to verify exclusion logic.~~
    - Add tests verifying that files within manually defined ignored directory prefixes are excluded.
    - Test the case where no ignore rules apply (or are needed if manual list covers all).
    - Ensure tests cover finding files and generating the consolidated report.
6.  `[X]` **Update README:** Add documentation for the new `check_markdown_links_project` tool.
7.  `[X]` **Agent Test:** Test calling `check_markdown_links_project` via the agent interface.

**Part 2: Configuration-Based Scan** (Details deferred until Part 1 is complete)

8.  `[ ]` Define configuration format and location (e.g., `mcp_config.toml` or similar at project root).
9.  `[ ]` Define tool (`check_markdown_links_config`) in `handle_list_tools`.
10. `[ ]` Implement logic to read and parse the config file.
11. `[ ]` Implement handler logic in `handle_call_tool` to process configured files/directories.
12. `[ ]` Add tests for config-based scanning.
13. `[ ]` Update README.
14. `[ ]` Agent Test.

**Final Steps**

15. `[X]` **Final Checks:** Run `make lint` and `make test` to ensure everything passes.
16. `[ ]` **Mark Plan Complete:** Update the status of this plan file.

**Next Step:** Proceed with Part 2, Step 8: Define configuration format.
