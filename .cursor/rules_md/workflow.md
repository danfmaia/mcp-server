---
description: Standard operating procedures for AI agents in this project.
globs:
alwaysApply: false
---

# Multi-Agent Workflow Rules

This document outlines the standard operating procedures applicable to all AI agents collaborating within this project.

## Core Principles (Apply to All Agents)

- **Minimalism**: Keep folder structures and documentation lean and focused. Avoid unnecessary files or excessive detail where a concise summary suffices.
- **Consistency**: Follow established patterns for file naming, documentation structure, and communication logging.
- **Direct Editing**: Prefer direct updates to existing files over creating temporary draft files, where applicable to the agent's role.
- **Plan Before Acting**: For non-trivial tasks, perform necessary analysis (documenting if complex) and create a clear execution plan (`_plan.md`) before implementing changes or taking significant action. **Plans should be structured to enable status tracking for individual tasks or steps** (e.g., using prefixes like `[ ]`/`[x]`, or explicit status labels per item).

## Agent Roles and Responsibilities

This section outlines the defined AI Agent roles within this project.

### Career Agent (Primary)

- **Role:** Manage Dan Maia's job search, career development, and professional growth, balancing immediate employment needs with long-term goals.
- **Responsibilities:** See system prompt for details.
- **System Prompt:** See [1-career-agent](mdc:agents/1-career-agent.mdc)

### Developer Agent

- **Role:** Research, design, implement, and maintain technical tools, automations, and code components to support the overall workflow.
- **Responsibilities:** See system prompt for details.
- **System Prompt:** See [2-developer-agent](mdc:agents/2-developer-agent.mdc) _(Note: corresponding .mdc file uses this pattern)_

## General File Management

- Agent should request confirmation before deleting files or folders unless correcting an agent error (like deleting a temporary draft file).
- **Naming Conventions:**
  - **Analyses/Reports/etc.:** Use descriptive names with suffixes like `_analysis.md`, `_report.md`, `_strategy.md`, `_research.md`. Located in `leads/analyses/` or other relevant directories (e.g., `docs/analyses/`).
  - **Requirements Docs:** Use `_reqs.md` suffix (e.g., `feature_x_reqs.md`). Located in `docs/requirements/`.
  - **Execution Plans:** Use `_plan.md` suffix (e.g., `task_y_plan.md`). Located in `docs/plans/` or other relevant directories.
  - **Message Files:** Follow `msg[NNN](-in|-out)?_[Sender]-[Receiver]_[topic].md`. See [.messages/README.md](../../.messages/README.md) for full details. Located in `.messages/direct/`.
  - **Lead Folders (Dirs):** Use `[Num]_[Company]_[Role]` pattern. Located in `leads/`.
  - **Editable Rule Files:** Use underscores (e.g., `1_career_agent.md`). Located in `.cursor/rules_md/`.
  - **Authoritative Rule Files:** Use hyphens (e.g., `1-career-agent.mdc`). Located in `.cursor/rules/`.

## Rule File Management (.md vs .mdc Workaround)

- **Authoritative Files:** The `.mdc` files located under `.cursor/rules/` are the authoritative rule definitions used by Cursor.
- **Editable Files:** Due to potential difficulties editing `.mdc` files directly via tools, corresponding `.md` files are maintained under `.cursor/rules_md/`. These `.md` files are the designated targets for AI-driven edits.
- **Manual Sync Required:** After an `.md` rule file is modified by an agent, the **User** is responsible for manually copying the _entire updated content_ from the `.md` file and pasting it into the corresponding `.mdc` file, replacing its contents. This ensures the authoritative `.mdc` file stays synchronized with the edited `.md` version.

## Internal Agent Communication Protocol

- **Mechanism:** Communication and handoffs between internal AI agents (e.g., Career Agent to Developer Agent, or between different instances of the same agent role) MUST be performed by creating structured message files within the `.messages/direct/` directory.
- **Format & Naming:** Strictly adhere to the file naming conventions and content structure defined in **[.messages/README.md](mdc:.messages/README.md)**.
- **User Mediation:** The User (Dan) will manually switch agent contexts and provide the relevant message file content as input to the receiving agent. Direct agent-to-agent communication is not possible.
- **Purpose:** This ensures a clear, logged history of internal tasks, delegations, and information handoffs.

---

_This is a living document. Update as workflows evolve._
