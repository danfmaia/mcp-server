---
description: Coding pattern preferences for all developer agents
globs:
---

# Coding pattern preferences

- Always prefer simple solutions
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code and functionality
- Write code that takes into account the different environments: dev, test, and prod
- You are careful to only make changes that are requested or you are confident are well understood and related to the change being requested
- When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for the existing implementation. And if you finally do this, make sure to remove the old implementation afterwards so we don't have duplicate logic.
- Keep the codebase very clean and organized
- Avoid writing scripts in files if possible, especially if the script is likely only to be run once.
- If any script is needed for an operation and is likely to be used only once, don't forget to clean up after the successful use, after the user approved the results.
- Avoid having files over 200-300 lines of code. Refactor at that point.
- Mocking data is only needed for tests, never mock data for dev or prod
- Never add stubbing or fake data patterns to code that affects the dev or prod environments
- Never overwrite my .env file without first asking and confirming

## Linting Patterns

- **Strictness:** Adhere to configured linter rules (e.g., ruff, pylint) to maintain code quality and consistency.
- **Line Length:** While aiming for standard line lengths (e.g., 80 or 100 characters), **ignore linter errors for lines exceeding the limit up to 120 characters** if breaking the line significantly harms readability (e.g., complex function signatures, dictionary definitions, long strings). Prioritize readability over strict adherence in these edge cases within the 120-character bound.
- **Type Hinting:** Add type hints for all new functions and methods. Strive to add hints to existing code when modifying it.
- **Error Resolution:** Always attempt to resolve linter errors identified during code generation or modification, unless explicitly permitted by other rules (like the extended line length allowance).
