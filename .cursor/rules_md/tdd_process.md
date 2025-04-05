---
description: Establishes TDD as the preferred development methodology for this project.
globs:
alwaysApply: false
---

# Test-Driven Development (TDD) Process

**Status:** Active

## Core Principle

For all new feature development, tool implementation (e.g., MCP server tools), utility scripts, or significant refactoring within this project, a **Test-Driven Development (TDD)** approach is the strongly preferred methodology.

## Workflow

The standard TDD cycle should be followed:

1.  **Red:** Write an automated test case that defines a desired improvement or new function. This test **must fail** initially because the feature doesn't exist yet.
2.  **Green:** Write the **minimum amount** of production code necessary to make the failing test pass.
3.  **Refactor:** Clean up the newly written code (and potentially the test code) for clarity, simplicity, performance, and maintainability, ensuring all tests continue to pass.

Repeat this cycle for small increments of functionality.

## Applicability

This applies particularly to:

- Backend logic
- API endpoints
- Tool implementations (like MCP tools)
- Data processing scripts
- Utility functions

While TDD for UI components or complex integrations might require different testing strategies (e.g., integration tests, end-to-end tests), the underlying principle of writing tests early and ensuring testability should still be prioritized.

## Goal

To build a more robust, maintainable, and verifiable codebase by ensuring functionality is specified and validated through automated tests _before_ or _during_ implementation.
