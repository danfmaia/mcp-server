# Requirements: Link Checker Tool Enhancements

**Status:** Proposed
**Date:** 2025-04-05
**Related Tool:** `mcp_server/local-link-checker`

## Goal

Improve the usability and efficiency of the `check-markdown-links` MCP tool for bulk validation use cases, such as checking all documentation files within a project or integrating into CI/CD pipelines.

## Requirements

1.  **Multiple File Input:** The tool should optionally accept a list of file paths (`file_paths: List[str]`) in a single `call_tool` request, in addition to the current single `file_path: str`.
    *   The tool should process each file in the list.
    *   The result should clearly associate findings (valid, broken, errored links) with their corresponding source file.

2.  **Directory Scanning Input:** The tool should optionally accept a directory path (`directory_path: str`) as input.
    *   When a directory path is provided, the tool should recursively scan that directory for specified file types (defaulting to `.md`).
    *   An optional argument (`include_patterns: List[str]`, e.g., `['*.md', '*.mdc']`) should allow specifying which file patterns to check.
    *   An optional argument (`exclude_patterns: List[str]`, e.g., `['**/node_modules/**', '**/.venv/**']`) should allow excluding specific files or directories.
    *   The tool should process all found files matching the criteria.
    *   The result should clearly associate findings with their corresponding source file.

3.  **Consolidated Reporting:** When processing multiple files (either via list input or directory scan), the output format should be adjusted to handle results from numerous files gracefully. Options include:
    *   A list of individual reports, one per file checked.
    *   A single consolidated report summarizing total files scanned, total links checked, and a list of all broken/errored links grouped by source file.

## Rationale

*   The current one-file-at-a-time invocation is inefficient for checking entire documentation sets (as demonstrated when attempting to validate this project's docs).
*   Directory scanning simplifies checking large numbers of files without needing to manually list them all.
*   Batch processing is essential for potential integration into automated workflows (e.g., pre-commit hooks, CI checks). 