# src/mcp_link_checker/server.py

import asyncio
import logging
import os  # Import os for path manipulation
import sys
from pathlib import Path

import aiofiles  # Added for async file reading
import mcp.server.stdio
import mcp.types as types
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

# --- Tool Definitions ---


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("Handling list_tools request")
    return [
        # Tool 1: Single File
        types.Tool(
            name="check_markdown_link_file",
            description="Checks HTTP/HTTPS links in a single Markdown file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the single Markdown file."
                    }
                },
                "required": ["file_path"],
            },
        ),
        # Tool 2: List of Files
        types.Tool(
            name="check_markdown_link_files",
            description="Checks HTTP/HTTPS links in a list of Markdown files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of paths to specific Markdown files."
                    }
                },
                "required": ["file_paths"],
            },
        ),
        # Tool 3: Directory
        types.Tool(
            name="check_markdown_link_directory",
            description="Checks HTTP/HTTPS links in all *.md files within a directory (recursively).",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to scan."
                    }
                },
                "required": ["directory_path"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[
    types.TextContent | types.ImageContent | types.EmbeddedResource
]:
    """Handle tool execution requests."""
    logger.info(f"Handling call_tool request for tool: {name}")

    # Define project root for path resolution
    PROJECT_ROOT = Path("/home/danfmaia/_repos/mcp-server")

    results_list = []
    processed_files = []
    error_files = {}
    report_source_info = f"Tool: {name}"  # Default source info

    if name == "check_markdown_link_file":
        if not arguments or "file_path" not in arguments:
            raise ValueError("Missing required argument: file_path")
        file_path_str = arguments["file_path"]
        # Resolve path relative to project root
        file_path_resolved = (PROJECT_ROOT / file_path_str).resolve()
        paths_to_process = [file_path_resolved]
        report_source_info = f"File: {file_path_str}"

    elif name == "check_markdown_link_files":
        if not arguments or "file_paths" not in arguments:
            raise ValueError("Missing required argument: file_paths")
        file_paths_list = arguments["file_paths"]
        if not isinstance(file_paths_list, list):
            raise ValueError(
                "Argument 'file_paths' must be a list of strings.")
        # Resolve paths relative to project root
        paths_to_process = [
            (PROJECT_ROOT / p).resolve() for p in file_paths_list
        ]
        report_source_info = f"Files Processed ({len(paths_to_process)}):\n" + "\n".join(
            f"  - {p}" for p in file_paths_list)  # Report original paths

    elif name == "check_markdown_link_directory":
        if not arguments or "directory_path" not in arguments:
            raise ValueError("Missing required argument: directory_path")
        directory_path_str = arguments["directory_path"]
        # Resolve the directory path relative to PROJECT_ROOT
        scan_dir = (PROJECT_ROOT / directory_path_str).resolve()
        # Log resolved path
        logger.info(f"Checking resolved path for directory: {scan_dir}")
        if not scan_dir.exists():
            logger.error(f"Resolved path does not exist: {scan_dir}")
            raise ValueError(
                f"Directory target does not exist: {directory_path_str}")
        if not scan_dir.is_dir():
            logger.error(
                f"Resolved path exists but is not a directory: {scan_dir}")
            raise ValueError(f"Path is not a directory: {directory_path_str}")
        logger.info(f"Scanning directory recursively: {scan_dir}")
        paths_to_process = [
            p for p in scan_dir.rglob('*.md') if p.is_file()]
        logger.info(
            f"Found {len(paths_to_process)} Markdown files to process.")
        report_source_info = f"Directory Scanned: {directory_path_str}"
        if not paths_to_process:
            return [types.TextContent(type="text", text=f"No Markdown files found in directory: {directory_path_str}")]

    else:
        logger.error(f"Unknown tool requested: {name}")
        raise ValueError(f"Unknown tool: {name}")

    # --- Centralized File Processing Logic ---
    for file_path in paths_to_process:
        current_path_str = str(file_path)
        # Default, maybe map back later if complex
        # original_path_repr = current_path_str # Removed: Unused variable
        # (For simplicity, we'll use the resolved path string in reports for now)
        logger.info(f"Checking links in file: {current_path_str}")
        try:
            async with aiofiles.open(file_path, encoding='utf-8') as f:
                content = await f.read()
            logger.info(f"Read {len(content)} bytes from {current_path_str}")
            link_results = await check_links_in_content(content)
            logger.info(
                f"Link checking completed for {current_path_str}. "
                f"Results: {link_results}")
            results_list.append(link_results)
            processed_files.append(current_path_str)  # Report resolved path

        except FileNotFoundError:
            err_msg = f"Error: File not found at {current_path_str}"
            logger.error(err_msg)
            error_files[current_path_str] = "File not found"
        except Exception as e:
            err_msg = (
                f"Error processing file {current_path_str}: "
                f"{type(e).__name__} - {e}")
            logger.exception(
                f"Error during link check for {current_path_str}")
            error_files[current_path_str] = f"{type(e).__name__}"

    # --- Format the Report (Use existing helpers) ---
    if name == "check_markdown_link_file":
        # For single file, report based on original input path if possible
        input_path = arguments.get("file_path", "")
        result_text = _format_single_file_report(
            input_path, results_list, error_files)
    else:  # Consolidated report for list or directory
        result_text = _format_consolidated_report(
            report_source_info, results_list, processed_files, error_files)

    return [
        types.TextContent(
            type="text",
            text=result_text.strip(),
        )
    ]

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
