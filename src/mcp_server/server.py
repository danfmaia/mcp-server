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

# --- Tool Definitions ---


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("Handling list_tools request")
    return [
        types.Tool(
            name="check-markdown-links",
            description="Checks HTTP/HTTPS links in a given Markdown file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        # Description broken into two lines
                        "description": (
                            "Absolute or relative path to the Markdown file."
                        )
                    }
                },
                "required": ["file_path"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[
    types.TextContent | types.ImageContent | types.EmbeddedResource
]:
    """Handle tool execution requests."""
    logger.info(f"Handling call_tool request for tool: {name}")
    if name == "check-markdown-links":
        if not arguments:
            raise ValueError("Missing arguments for check-markdown-links")
        file_path_str = arguments.get("file_path")
        if not file_path_str:
            raise ValueError("Missing required argument: file_path")

        logger.info(f"Checking links in file: {file_path_str}")
        file_path = Path(file_path_str).resolve()  # Resolve to absolute path
        result_text = ""

        try:
            async with aiofiles.open(file_path, encoding='utf-8') as f:
                content = await f.read()

            logger.info(f"Read {len(content)} bytes from {file_path}")
            link_results = await check_links_in_content(content)
            logger.info(f"Link checking completed. Results: {link_results}")

            # Format the results into a readable string
            # Example formatting, can be adjusted
            result_text = f"Link Check Report for: {file_path_str}\n"
            result_text += f"Total Links Found: {link_results['total']}\n"
            result_text += f"Valid Links ({len(link_results['valid'])}):\n"
            for link in link_results['valid']:
                result_text += f"  - {link}\n"
            result_text += f"Broken Links ({len(link_results['broken'])}):\n"
            for item in link_results['broken']:
                result_text += f"  - {item['url']} (Reason: {item['reason']})\n"
            result_text += f"Errored Links ({len(link_results['errors'])}):\n"
            for item in link_results['errors']:
                result_text += f"  - {item['url']} (Reason: {item['reason']})\n"

        except FileNotFoundError:
            result_text = f"Error: File not found at {file_path}"
            logger.error(result_text)
        except Exception as e:
            result_text = f"Error processing file {file_path}: {type(e).__name__} - {e}"
            logger.exception(f"Error during link check for {file_path}")

        return [
            types.TextContent(
                type="text",
                text=result_text.strip(),  # Remove trailing newline
            )
        ]
    else:
        logger.error(f"Unknown tool requested: {name}")
        raise ValueError(f"Unknown tool: {name}")

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
