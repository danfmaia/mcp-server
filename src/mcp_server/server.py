# src/mcp_link_checker/server.py

import asyncio
import logging
import os  # Import os for path manipulation
import sys
from pathlib import Path

import aiofiles  # Added for async file reading
import mcp.server.stdio
import mcp.types as types
import pathspec  # Import pathspec
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .tools.link_checker import check_links_in_content

# --- Early File Logging Setup ---
log_file_path = os.path.join(os.path.dirname(
    __file__), 'mcp_server_startup.log')
try:
    # Configure root logger for file output before anything else runs
    file_handler = logging.FileHandler(
        log_file_path, mode='w')  # Overwrite log each time
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    root_logger = logging.getLogger()  # Get root logger
    root_logger.setLevel(logging.DEBUG)  # Capture everything
    root_logger.addHandler(file_handler)

    root_logger.info(f"--- Script start logging to {log_file_path} ---")
    root_logger.info(f"Python executable: {sys.executable}")
    root_logger.info(f"sys.path: {sys.path}")
    root_logger.info(f"Current working directory: {os.getcwd()}")
except Exception as e:
    # If logging setup fails, print to stderr and exit
    print(
        f"CRITICAL: Failed to set up file logging to {log_file_path}: {e}", file=sys.stderr)
    sys.exit(1)  # Exit if we can't even log
# --- End Early File Logging Setup ---

# import json # Removed unused import


# Import the link checking function

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    # Formatted log
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SERVER_NAME = "mcp-tools"
SERVER_VERSION = "0.1.0"

# --- Server Initialization ---
server = Server(SERVER_NAME)

# --- Helper Functions ---


def _format_link_report_details(link_results: dict) -> str:
    """Formats the Valid/Broken/Errored link details into a string."""
    details_text = ""
    # Always include headers, even if the list is empty
    details_text += f"  Valid Links ({len(link_results['valid'])}):\n"
    if link_results['valid']:
        for link in link_results['valid']:
            details_text += f"    - {link}\n"

    details_text += f"  Broken Links ({len(link_results['broken'])}):\n"
    if link_results['broken']:
        for item in link_results['broken']:
            details_text += f"    - {item['url']} (Reason: {item['reason']})\n"

    details_text += f"  Errored Links ({len(link_results['errors'])}):\n"
    if link_results['errors']:
        for item in link_results['errors']:
            details_text += f"    - {item['url']} (Reason: {item['reason']})\n"
    return details_text

# --- Helper Functions for Report Formatting ---


def _format_single_file_report(file_path_str, results_list, error_files) -> str:
    """Formats the report for a single file processing result."""
    if results_list:  # Only if processing was successful
        link_results = results_list[0]
        result_text = f"Link Check Report for: {file_path_str}\n"
        result_text += f"Total Links Found: {link_results['total']}\n"
        result_text += _format_link_report_details(link_results)
    else:  # Error processing the single file
        # Error message is already logged, report the error status
        error_reason = list(error_files.values())[0]
        result_text = (
            f"Error processing file: {file_path_str} - "
            f"Reason: {error_reason}")
    return result_text


def _format_consolidated_report(report_source_info, results_list, processed_files, error_files) -> str:
    """Formats the consolidated report for multiple file processing results."""
    total_links = sum(r['total'] for r in results_list)
    total_valid = sum(len(r['valid']) for r in results_list)
    total_broken = sum(len(r['broken']) for r in results_list)
    total_errors = sum(len(r['errors']) for r in results_list)

    result_text = "Consolidated Link Check Report\n"
    result_text += f"{report_source_info}\n"
    # List processed/error files only if it was a list/directory input
    if processed_files:
        result_text += f"Files Processed ({len(processed_files)}):\n"
        for pf in processed_files:
            result_text += f"  - {pf}\n"
    if error_files:
        result_text += f"Files with Errors ({len(error_files)}):\n"
        for ef, reason in error_files.items():
            result_text += f"  - {ef} (Reason: {reason})\n"

    result_text += "---\n"
    result_text += "Overall Summary:\n"
    result_text += f"  Total Links Found: {total_links}\n"
    result_text += f"  Valid Links: {total_valid}\n"
    result_text += f"  Broken Links: {total_broken}\n"
    result_text += f"  Errored Links: {total_errors}\n"
    result_text += "---\n"
    result_text += "Details:\n"

    for i, pf in enumerate(processed_files):
        link_results = results_list[i]
        if link_results['total'] > 0:  # Only add details if links were found
            result_text += f"\nFile: {pf}\n"
            # Use helper function for details
            result_text += _format_link_report_details(link_results)
    return result_text

# --- Helper Function for Single File Check ---


async def _check_single_file(file_path: Path) -> dict | str:
    """Asynchronously checks links in a single file, returns results or error string."""
    file_path_str = str(file_path)
    try:
        logger.info(f"Checking links in file: {file_path_str}")
        async with aiofiles.open(file_path, encoding='utf-8') as f:
            content = await f.read()
        logger.info(f"Read {len(content)} bytes from {file_path_str}")
        # Perform link checking
        link_results = await check_links_in_content(content)
        logger.info(
            f"Link checking completed for {file_path_str}. Results: {link_results}")
        return link_results  # Return results dictionary
    except FileNotFoundError:
        error_msg = f"File not found at {file_path_str}"
        logger.error(f"Error: {error_msg}")
        return error_msg  # Return error string
    except Exception as e:
        error_msg = f"Error during link check for {file_path_str}: {e.__class__.__name__}"
        logger.exception(
            f"Error during link check for {file_path_str}")  # Log full traceback
        return error_msg  # Return error string

# --- Tool Definitions ---


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("Handling list_tools request")
    # Define the tools provided by this server
    tools = [
        types.Tool(
            name="check_markdown_link_file",
            description="Checks HTTP/HTTPS links in a single Markdown file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the single Markdown file.",
                    }
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="check_markdown_link_files",
            description="Checks HTTP/HTTPS links in a list of Markdown files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of paths to specific Markdown files.",
                    }
                },
                "required": ["file_paths"],
            },
        ),
        types.Tool(
            name="check_markdown_link_directory",
            description="Checks HTTP/HTTPS links in all *.md files within a directory (recursively).",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to scan.",
                    }
                },
                "required": ["directory_path"],
            },
        ),
        types.Tool(
            name="check_markdown_links_project",
            description="Checks HTTP/HTTPS links in all project *.md files, respecting .gitignore.",
            inputSchema={
                "type": "object",
                "properties": {},
                # No arguments required
            },
        ),
    ]
    return tools


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[
    types.TextContent | types.ImageContent | types.EmbeddedResource
] | dict:  # Allow dict return for project scan
    """Handle tool execution requests."""
    logger.info(f"Handling call_tool request for tool: {name}")

    # Define project root for path resolution
    PROJECT_ROOT = Path("/home/danfmaia/_repos/mcp-server")

    # Initialize variables used by multiple branches
    paths_to_process = []
    report_source_info = f"Tool: {name}"

    # --- Logic specific to each tool type ---

    if name == "check_markdown_link_file":
        if not arguments or "file_path" not in arguments:
            raise ValueError("Missing required argument: file_path")
        file_path_str = arguments["file_path"]
        paths_to_process = [(PROJECT_ROOT / file_path_str).resolve()]
        report_source_info = f"File: {file_path_str}"

    elif name == "check_markdown_link_files":
        if not arguments or "file_paths" not in arguments:
            raise ValueError("Missing required argument: file_paths")
        file_paths_list = arguments["file_paths"]
        if not isinstance(file_paths_list, list):
            raise ValueError(
                "Argument 'file_paths' must be a list of strings.")
        paths_to_process = [(PROJECT_ROOT / p).resolve()
                            for p in file_paths_list]
        # Report original paths provided by the user
        report_source_info = f"Files Processed ({len(paths_to_process)}):\n" + "\n".join(
            f"  - {p}" for p in file_paths_list)

    elif name == "check_markdown_link_directory":
        if not arguments or "directory_path" not in arguments:
            raise ValueError("Missing required argument: directory_path")
        directory_path_str = arguments["directory_path"]
        scan_dir = (PROJECT_ROOT / directory_path_str).resolve()
        logger.info(f"Checking resolved path for directory: {scan_dir}")
        if not scan_dir.exists():
            logger.error(f"Directory path does not exist: {scan_dir}")
            raise ValueError(
                f"Directory target does not exist: {directory_path_str}")
        if not scan_dir.is_dir():
            logger.error(f"Path is not a directory: {scan_dir}")
            raise ValueError(f"Path is not a directory: {directory_path_str}")
        logger.info(f"Scanning directory recursively: {scan_dir}")
        paths_to_process = [p for p in scan_dir.rglob('*.md') if p.is_file()]
        logger.info(
            f"Found {len(paths_to_process)} Markdown files to process.")
        report_source_info = f"Directory Scanned: {directory_path_str}"
        if not paths_to_process:
            # Return TextContent list even for no files found in directory
            return [types.TextContent(type="text", text=f"No Markdown files found in directory: {directory_path_str}")]

    elif name == "check_markdown_links_project":
        report_source_info = "Project Scan (using .gitignore)"
        # Re-introduce placeholders for gitignore handling with pathspec
        gitignore_path = PROJECT_ROOT / ".gitignore"
        spec = None
        if gitignore_path.is_file():
            try:
                # Read .gitignore content
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    gitignore_content = f.read()
                # Create pathspec from .gitignore lines using gitwildmatch style
                spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, gitignore_content.splitlines()
                )
                logger.info(f"Loaded .gitignore rules from: {gitignore_path}")
            except Exception as e:
                logger.warning(
                    f"Could not read/parse .gitignore file at {gitignore_path}: {e}", exc_info=True)
        else:
            logger.info("No .gitignore file found at project root.")

        logger.info(
            f"Scanning project root recursively for *.md files: {PROJECT_ROOT}")
        all_files_paths = list(PROJECT_ROOT.rglob("*.md"))
        logger.info(
            f"Found {len(all_files_paths)} total Markdown files before filtering.")

        # Filter files using pathspec (if available)
        filtered_files = []
        if spec:
            # Convert Path objects to relative strings for matching
            # Ensure we only check files (rglob might yield dirs)
            all_file_paths_relative_str = [
                str(p.relative_to(PROJECT_ROOT))
                for p in all_files_paths if p.is_file()
            ]
            # Get the set of ignored file paths (as relative strings)
            ignored_files_set = set(
                spec.match_files(all_file_paths_relative_str))
            logger.info(
                f"Found {len(ignored_files_set)} ignored files based on .gitignore")
            # Iterate through original Path objects, keeping those not in the ignored set
            for p in all_files_paths:
                if p.is_file() and str(p.relative_to(PROJECT_ROOT)) not in ignored_files_set:
                    filtered_files.append(p)
        else:
            # No spec (no .gitignore or failed to parse), process all files
            logger.info("No .gitignore spec, processing all found files.")
            for p in all_files_paths:
                if p.is_file():
                    filtered_files.append(p)

        logger.info(
            f"Processing {len(filtered_files)} Markdown files after filtering.")

        if not filtered_files:
            # Use TextContent for consistency
            return [types.TextContent(type="text", text="No processable Markdown files found.")]

        tasks = [asyncio.create_task(_check_single_file(file))
                 for file in filtered_files]
        file_results_list = await asyncio.gather(*tasks)

        results_list = [
            res for res in file_results_list if isinstance(res, dict)]
        error_files = {str(file): reason for file, reason in zip(
            filtered_files, file_results_list) if isinstance(reason, str)}
        # Use filtered_files (Path objects) for reporting file names
        processed_files_paths = [f for f, res in zip(
            filtered_files, file_results_list) if isinstance(res, dict)]
        # Report relative paths from PROJECT_ROOT for readability
        processed_files_rel_str = [
            str(p.relative_to(PROJECT_ROOT)) for p in processed_files_paths]

        report = _format_consolidated_report(
            report_source_info, results_list, processed_files_rel_str, error_files
        )
        # return {"report": report}  # Return dict for project scan
        # Return the formatted report wrapped in TextContent list for consistency
        return [types.TextContent(type="text", text=report)]

    else:
        logger.error(f"Unknown tool requested: {name}")
        raise ValueError(f"Unknown tool: {name}")

    # --- Centralized Processing for file/files/directory tools ---
    # This block only runs if paths_to_process was populated above
    # and the tool wasn't check_markdown_links_project (it exited above)
    results_list_central = []
    processed_files_central = []
    error_files_central = {}
    for file_path in paths_to_process:
        # Report the original path if it was a single file check, else the resolved one
        file_path_str_for_report = arguments.get("file_path", str(
            file_path)) if name == "check_markdown_link_file" else str(file_path)
        # Always use resolved for processing
        file_path_str_for_processing = str(file_path)

        try:
            logger.info(
                f"Checking links in file (central): {file_path_str_for_processing}")
            async with aiofiles.open(file_path_str_for_processing, encoding='utf-8') as f:
                content = await f.read()
            logger.info(
                f"Read {len(content)} bytes from {file_path_str_for_processing} (central)")
            link_results = await check_links_in_content(content)
            logger.info(
                f"Link checking completed for {file_path_str_for_processing}. Results: {link_results} (central)")
            results_list_central.append(link_results)
            processed_files_central.append(file_path_str_for_report)
        except FileNotFoundError:
            error_msg = f"File not found at {file_path_str_for_processing}"
            logger.error(f"Error: {error_msg} (central)")
            # Report error against original path
            error_files_central[file_path_str_for_report] = error_msg
        except Exception as e:
            error_msg = f"Error during link check for {file_path_str_for_processing}: {e.__class__.__name__} (central)"
            logger.exception(
                f"Error during link check for {file_path_str_for_processing} (central)")
            # Report error against original path
            error_files_central[file_path_str_for_report] = error_msg

    # --- Format Report for file/files/directory tools ---
    if len(paths_to_process) == 1 and name == "check_markdown_link_file":
        report = _format_single_file_report(
            arguments.get("file_path", ""),  # Use original path for report
            results_list_central, error_files_central)
    else:
        # report_source_info already contains the list of original paths for 'files'
        # or the directory path for 'directory'
        report = _format_consolidated_report(
            report_source_info, results_list_central, processed_files_central, error_files_central
        )

    # Return the formatted report wrapped in TextContent list
    return [types.TextContent(type="text", text=report)]


# --- Main Server Loop ---


async def main():
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}...")
    try:
        # Reformat async with statement
        stdio_transport = mcp.server.stdio.stdio_server()
        async with stdio_transport as (read_stream, write_stream):
            logger.info("MCP stdio transport established.")
            logger.info("Waiting for initialization...")

            server_capabilities = server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )

            init_options = InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=server_capabilities,
            )

            await server.run(
                read_stream,
                write_stream,
                init_options,
            )
    except Exception:
        logger.exception("Server run loop encountered an error")
        sys.exit(1)
    finally:
        logger.info(f"{SERVER_NAME} shutting down.")


def run_server():
    """Entry point for uv run."""
    asyncio.run(main())


if __name__ == "__main__":
    # Allows running server directly for testing (`python src/.../server.py`)
    # Preferred method is `uv run mcp_server` (updated script name)
    # Keep call here for direct execution compatibility
    run_server()
