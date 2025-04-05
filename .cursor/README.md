# .cursor Directory README

This directory contains configuration files specifically for the Cursor IDE environment used in the `career-agent` project.

## Structure

- **`rules/`**: Contains the authoritative rule files (`.mdc`) that define the behavior and knowledge of the AI agents (like Career Agent, Developer Agent) and general workflow settings used by Cursor.

  - **Important:** Due to potential bugs in direct AI editing of `.mdc` files, these files should **not** be modified directly by AI agents or manually unless necessary.
  - **`rules/agents/`**: Contains the specific system prompts for different AI agent roles.

- **`rules_md/`**: Contains the editable Markdown (`.md`) versions of the rule files found in `rules/`. This is the **primary location for editing rules**.
  - The structure within `rules_md/` mirrors `rules/` (e.g., `rules_md/agents/`).
  - **Filename Convention:** Note that `.md` files in `rules_md/` use underscores (e.g., `1_career_agent.md`), while the corresponding authoritative `.mdc` files in `rules/` use hyphens (e.g., `1-career-agent.mdc`).

## Synchronization Workflow (`.md` -> `.mdc`)

1.  **Edit Here:** Make all changes to rules within the `.md` files in the `.cursor/rules_md/` directory.
2.  **Run Sync Script:** After editing any `.md` rule file, run the synchronization script from the project root:
    ```bash
    python scripts/sync_rules.py
    ```
    This script automatically copies the content from the updated `.md` files into the corresponding authoritative `.mdc` files in `.cursor/rules/`, handling the filename conversion (underscores to hyphens) and ensuring Cursor uses the latest rule versions.
3.  **Avoid Manual Sync:** The script replaces the previous need for manual copy-pasting between `.md` and `.mdc` files.

## Key Rule Files

- `workflow.mdc` / `workflow.md`: Defines core principles, agent roles, communication protocols, and file management rules for the project.
- `communication-style-prefs.mdc` / `communication-style-prefs.md`: Defines stylistic preferences for drafting external communications.
- `agents/1-career-agent.mdc` / `agents/1_career_agent.md`: System prompt for the main Career Agent.
- `agents/2-developer-agent.mdc` / `agents/2_developer_agent.md`: System prompt for the Developer Agent.

---

_This README helps maintain clarity on how Cursor rules are managed in this project._
