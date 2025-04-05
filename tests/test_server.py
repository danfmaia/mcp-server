from unittest.mock import AsyncMock, MagicMock, patch

import mcp.types as types
import pytest

# Import functions to test from server.py
# Adjust the import path based on your project structure if necessary
from mcp_server.server import handle_call_tool, handle_list_tools

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_handle_list_tools_returns_correct_tool():
    """Verify that handle_list_tools returns the expected tool definition."""
    tools = await handle_list_tools()
    assert isinstance(tools, list)
    assert len(tools) == 1
    tool = tools[0]
    assert isinstance(tool, types.Tool)
    assert tool.name == "check-markdown-links"
    assert tool.description == (
        "Checks HTTP/HTTPS links in a given Markdown file."
    )
    assert tool.inputSchema is not None
    assert tool.inputSchema.get('type') == 'object'
    assert 'file_path' in tool.inputSchema.get('properties', {})
    assert tool.inputSchema['properties']['file_path']['type'] == 'string'
    description = tool.inputSchema['properties']['file_path']['description']
    assert "Absolute or relative path" in description
    assert tool.inputSchema.get('required') == ["file_path"]


# --- Tests for handle_call_tool ---

async def test_handle_call_tool_unknown_tool_raises_error():
    """Test calling an unknown tool name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool: unknown-tool-name"):
        await handle_call_tool(name="unknown-tool-name", arguments={})


async def test_handle_call_tool_missing_arguments_raises_error():
    """Test calling check-markdown-links with None arguments raises ValueError."""
    with pytest.raises(ValueError, match="Missing arguments"):
        await handle_call_tool(name="check-markdown-links", arguments=None)


async def test_handle_call_tool_missing_file_path_raises_error():
    """Test calling check-markdown-links with missing file_path raises ValueError."""
    match_str = "Missing required argument: file_path"
    with pytest.raises(ValueError, match=match_str):
        await handle_call_tool(
            name="check-markdown-links",
            arguments={"other_arg": 123}
        )


# Helper to create an async mock for aiofiles.open
def async_mock_open(read_data):
    mock_file = AsyncMock()
    # Mock the read method to be awaitable and return data
    mock_file.read.return_value = read_data

    # Mock the async context manager methods
    async_context_manager = AsyncMock()
    async_context_manager.__aenter__.return_value = mock_file
    # __aexit__ doesn't need a specific return value for this test
    async_context_manager.__aexit__.return_value = None

    mock_open_func = MagicMock(return_value=async_context_manager)
    return mock_open_func


@patch('mcp_server.server.check_links_in_content')
@patch(
    'aiofiles.open',
    new_callable=lambda: async_mock_open(
        read_data="[Valid Link](http://valid.com)")
)
async def test_handle_call_tool_success(mock_aio_open, mock_check_links):
    """Test the success path for check-markdown-links."""
    # Arrange: Configure the mock return value for check_links_in_content
    mock_check_links.return_value = {
        'total': 1,
        'valid': ['http://valid.com'],
        'broken': [],
        'errors': []
    }
    file_path_arg = "dummy/path.md"

    # Act: Call the handler
    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    # Assert: Check mocks and results
    # Check that the function returned by the patch (our MagicMock)
    # was called once. This represents calling aiofiles.open().
    mock_aio_open.assert_called_once()

    mock_check_links.assert_awaited_once_with("[Valid Link](http://valid.com)")

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)
    assert content.type == "text"
    assert f"Link Check Report for: {file_path_arg}" in content.text
    assert "Total Links Found: 1" in content.text
    assert "Valid Links (1):" in content.text
    assert "- http://valid.com" in content.text
    assert "Broken Links (0):" in content.text
    assert "Errored Links (0):" in content.text

# Need to adjust the other tests that mock aiofiles.open similarly


# Provide empty read_data
@patch('aiofiles.open', new_callable=lambda: async_mock_open(read_data=""))
async def test_handle_call_tool_file_not_found(mock_aio_open):
    """Test the case where the file_path does not exist."""
    # Set the side effect on the __aenter__ part of the mock
    mock_aio_open.return_value.__aenter__.side_effect = FileNotFoundError(
        "Mock file not found"
    )
    file_path_arg = "nonexistent/path.md"

    # Act
    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    # Assert
    mock_aio_open.assert_called_once()  # Check if aiofiles.open was called

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)
    assert content.type == "text"
    assert "Error: File not found" in content.text
    # Check if the path is mentioned in the error
    assert file_path_arg in content.text


# Provide empty read_data
@patch('aiofiles.open', new_callable=lambda: async_mock_open(read_data=""))
async def test_handle_call_tool_other_exception(mock_aio_open):
    """Test the case where an unexpected exception occurs during file read."""
    # Set the side effect on the __aenter__ part of the mock
    mock_aio_open.return_value.__aenter__.side_effect = PermissionError(
        "Mock permission denied"
    )
    file_path_arg = "unreadable/path.md"

    # Act
    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    # Assert
    mock_aio_open.assert_called_once()  # Check if aiofiles.open was called

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)
    assert content.type == "text"
    assert "Error processing file" in content.text
    assert file_path_arg in content.text
    # Check if the exception type is mentioned
    assert "PermissionError" in content.text
    # Check if the exception message is mentioned
    assert "Mock permission denied" in content.text


@patch('mcp_server.server.check_links_in_content')
@patch(
    'aiofiles.open',
    new_callable=lambda: async_mock_open(
        read_data="Content doesn't matter here")
)
async def test_handle_call_tool_report_formatting_broken_links(mock_aio_open, mock_check_links):
    """Test report formatting specifically for broken links."""
    mock_check_links.return_value = {
        'total': 2,
        'valid': ['http://valid.com'],
        'broken': [{'url': 'http://broken.com', 'reason': '404 Not Found'}],
        'errors': []
    }
    file_path_arg = "dummy/report_broken.md"

    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    assert isinstance(result[0], types.TextContent)
    text = result[0].text
    assert f"Link Check Report for: {file_path_arg}" in text
    assert "Total Links Found: 2" in text
    assert "Valid Links (1):" in text
    assert "- http://valid.com" in text
    assert "Broken Links (1):" in text
    assert "- http://broken.com (Reason: 404 Not Found)" in text
    assert "Errored Links (0):" in text


@patch('mcp_server.server.check_links_in_content')
@patch(
    'aiofiles.open',
    new_callable=lambda: async_mock_open(
        read_data="Content doesn't matter here")
)
async def test_handle_call_tool_report_formatting_errored_links(mock_aio_open, mock_check_links):
    """Test report formatting specifically for errored links."""
    mock_check_links.return_value = {
        'total': 2,
        'valid': ['http://valid.com'],
        'broken': [],
        'errors': [{'url': 'http://error.com', 'reason': 'Timeout'}]
    }
    file_path_arg = "dummy/report_error.md"

    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    assert isinstance(result[0], types.TextContent)
    text = result[0].text
    assert f"Link Check Report for: {file_path_arg}" in text
    assert "Total Links Found: 2" in text
    assert "Valid Links (1):" in text
    assert "- http://valid.com" in text
    assert "Broken Links (0):" in text
    assert "Errored Links (1):" in text
    assert "- http://error.com (Reason: Timeout)" in text


@patch('mcp_server.server.check_links_in_content')
@patch(
    'aiofiles.open',
    new_callable=lambda: async_mock_open(
        read_data="Content doesn't matter here")
)
async def test_handle_call_tool_report_formatting_no_links(mock_aio_open, mock_check_links):
    """Test report formatting when no links are found."""
    mock_check_links.return_value = {
        'total': 0,
        'valid': [],
        'broken': [],
        'errors': []
    }
    file_path_arg = "dummy/report_none.md"

    result = await handle_call_tool(
        name="check-markdown-links",
        arguments={"file_path": file_path_arg}
    )

    assert isinstance(result[0], types.TextContent)
    text = result[0].text
    assert f"Link Check Report for: {file_path_arg}" in text
    assert "Total Links Found: 0" in text
    assert "Valid Links (0):" in text
    assert "Broken Links (0):" in text
    assert "Errored Links (0):" in text
    # Check that specific link lines are NOT present
    assert "- http" not in text
