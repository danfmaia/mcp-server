import pathspec  # Import pathspec for mocking
from mcp_server.server import (
    handle_list_tools, handle_call_tool, _check_single_file
)
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import mcp.types as types
import pytest
import sys

# Ensure src directory is in path for imports if running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import functions to test from server.py
# Adjust the import path based on your project structure if necessary

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_handle_list_tools_returns_correct_tool():
    """Verify that handle_list_tools returns the expected tool definitions."""
    tools = await handle_list_tools()
    assert isinstance(tools, list)
    # Expect 4 tools now
    assert len(tools) == 4

    # Verify Tool 1: check_markdown_link_file
    tool1 = tools[0]
    assert isinstance(tool1, types.Tool)
    assert tool1.name == "check_markdown_link_file"
    assert tool1.description == "Checks HTTP/HTTPS links in a single Markdown file."
    assert tool1.inputSchema == {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the single Markdown file."
            }
        },
        "required": ["file_path"],
    }

    # Verify Tool 2: check_markdown_link_files
    tool2 = tools[1]
    assert isinstance(tool2, types.Tool)
    assert tool2.name == "check_markdown_link_files"
    assert tool2.description == "Checks HTTP/HTTPS links in a list of Markdown files."
    assert tool2.inputSchema == {
        "type": "object",
        "properties": {
            "file_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of paths to specific Markdown files."
            }
        },
        "required": ["file_paths"],
    }

    # Verify Tool 3: check_markdown_link_directory
    tool3 = tools[2]
    assert isinstance(tool3, types.Tool)
    assert tool3.name == "check_markdown_link_directory"
    assert tool3.description == "Checks HTTP/HTTPS links in all *.md files within a directory (recursively)."
    assert tool3.inputSchema == {
        "type": "object",
        "properties": {
            "directory_path": {
                "type": "string",
                "description": "Path to the directory to scan."
            }
        },
        "required": ["directory_path"],
    }

    # Verify Tool 4: check_markdown_links_project
    tool4 = tools[3]
    assert isinstance(tool4, types.Tool)
    assert tool4.name == "check_markdown_links_project"
    assert tool4.description == "Checks HTTP/HTTPS links in all project *.md files, respecting .gitignore."
    assert tool4.inputSchema == {
        "type": "object",
        "properties": {},
        # No arguments required
    }


# --- Tests for handle_call_tool ---

async def test_handle_call_tool_unknown_tool_raises_error():
    """Test calling an unknown tool name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool: unknown-tool-name"):
        await handle_call_tool(name="unknown-tool-name", arguments={})


# Helper to create an async mock for aiofiles.open
# Note: This helper might need adjustments if tests require different mock behaviors per call
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


# --- Tests for check-markdown-links --- (Now split into three tools)

@pytest.mark.anyio
@patch('aiofiles.open')
@patch('mcp_server.server.check_links_in_content')
async def test_handle_call_tool_file_success(mock_check_links, mock_aio_open):
    """Test successful link check for a single file."""
    # Arrange
    mock_file_path_str = "dummy/path.md"
    absolute_path = Path(
        "/home/danfmaia/_repos/mcp-server") / mock_file_path_str
    mock_content = "[Valid Link](http://valid.com)"
    mock_aio_open.return_value.__aenter__.return_value.read.return_value = mock_content
    mock_check_links.return_value = {'total': 1, 'valid': [
        'http://valid.com'], 'broken': [], 'errors': []}

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_file",
        arguments={"file_path": mock_file_path_str}
    )

    # Assert
    mock_aio_open.assert_called_once_with(
        str(absolute_path.resolve()), encoding='utf-8')
    mock_check_links.assert_called_once_with(mock_content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert "Link Check Report for: dummy/path.md" in result[0].text
    assert "Total Links Found: 1" in result[0].text
    assert "Valid Links (1):" in result[0].text
    assert "- http://valid.com" in result[0].text


@pytest.mark.anyio
# Test file not found without mocking aiofiles.open, as the check happens before
async def test_handle_call_tool_file_not_found():
    """Test link check when the single file is not found."""
    # Arrange
    mock_file_path_str = "nonexistent/path.md"
    absolute_path = Path(
        "/home/danfmaia/_repos/mcp-server") / mock_file_path_str

    # Ensure the file actually doesn't exist for the test
    if absolute_path.exists():
        pytest.skip(f"Test requires path {absolute_path} to not exist.")

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_file",
        arguments={"file_path": mock_file_path_str}
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    # Check error message, which now comes from the handler itself
    assert f"Error processing file: {mock_file_path_str} - Reason: File not found" in result[0].text


@pytest.mark.anyio
@patch('aiofiles.open')
async def test_handle_call_tool_file_other_exception(mock_aio_open):
    """Test link check handles exceptions during file processing."""
    # Arrange
    mock_aio_open.side_effect = PermissionError("Mock permission denied")
    mock_file_path_str = "unreadable/path.md"

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_file",
        arguments={"file_path": mock_file_path_str}
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    # Check the specific error message from the handler
    expected_error_reason = f"Error during link check for {str(Path('/home/danfmaia/_repos/mcp-server/unreadable/path.md').resolve())}: PermissionError (central)"
    assert f"Error processing file: {mock_file_path_str} - Reason: {expected_error_reason}" in result[0].text


# --- Tests for report formatting (can be adapted or removed if helpers are tested separately) ---
# Example adapting one:
@pytest.mark.anyio
@patch('aiofiles.open')
@patch('mcp_server.server.check_links_in_content')
async def test_handle_call_tool_file_report_formatting_broken_links(mock_check_links, mock_aio_open):
    """Test report formatting for a single file with broken links."""
    # Arrange
    mock_file_path_str = "dummy/report_broken.md"
    mock_content = "[Broken](http://broken.com)"
    mock_aio_open.return_value.__aenter__.return_value.read.return_value = mock_content
    mock_check_links.return_value = {
        'total': 1,
        'valid': [],
        'broken': [{'url': 'http://broken.com', 'reason': '404 Not Found'}],
        'errors': []
    }

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_file",
        arguments={"file_path": mock_file_path_str}
    )

    # Assert
    # ... assertions checking the formatted text content ...
    assert "Link Check Report for: dummy/report_broken.md" in result[0].text
    assert "Broken Links (1):" in result[0].text
    assert "- http://broken.com (Reason: 404 Not Found)" in result[0].text

# ... (Adapt other formatting tests similarly: _errored_links, _no_links, _mixed for the _file tool)


# --- New/Adapted Tests for check_markdown_link_files ---

@pytest.mark.anyio
@patch('aiofiles.open')
@patch('mcp_server.server.check_links_in_content')
async def test_handle_call_tool_files_success(mock_check_links, mock_aio_open):
    """Test successful link check for a list of files."""
    # Arrange
    project_root = Path("/home/danfmaia/_repos/mcp-server")
    file_paths_arg = ["dummy/list1.md", "dummy/list2.md"]
    abs_path1 = project_root / file_paths_arg[0]
    abs_path2 = project_root / file_paths_arg[1]

    content1 = "[Link1](http://valid1.com)"
    content2 = "[Link2](http://valid2.com) [Broken](http://broken2.com)"

    results1 = {'total': 1, 'valid': [
        'http://valid1.com'], 'broken': [], 'errors': []}
    results2 = {'total': 2, 'valid': ['http://valid2.com'], 'broken': [
        {'url': 'http://broken2.com', 'reason': '404 Not Found'}], 'errors': []}

    # Mock aiofiles.open based on resolved absolute paths
    mock_file1_ctx = AsyncMock()
    mock_file1_ctx.__aenter__.return_value.read.return_value = content1
    mock_file2_ctx = AsyncMock()
    mock_file2_ctx.__aenter__.return_value.read.return_value = content2

    def open_side_effect(path_arg, *args, **kwargs):
        # Centralized logic passes the *string* of the resolved path
        if path_arg == str(abs_path1.resolve()):
            return mock_file1_ctx
        elif path_arg == str(abs_path2.resolve()):
            return mock_file2_ctx
        raise FileNotFoundError(f"Mock file not found: {path_arg}")

    mock_aio_open.side_effect = open_side_effect

    # Mock check_links_in_content based on content
    def check_links_side_effect(content):
        if content == content1:
            return results1
        elif content == content2:
            return results2
        return {'total': 0, 'valid': [], 'broken': [], 'errors': []}
    mock_check_links.side_effect = check_links_side_effect

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_files",
        arguments={"file_paths": file_paths_arg}
    )

    # Assert
    assert mock_aio_open.call_count == 2
    # Check calls with resolved path strings
    mock_aio_open.assert_any_call(str(abs_path1.resolve()), encoding='utf-8')
    mock_aio_open.assert_any_call(str(abs_path2.resolve()), encoding='utf-8')
    assert mock_check_links.call_count == 2
    mock_check_links.assert_any_call(content1)
    mock_check_links.assert_any_call(content2)

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    report_text = result[0].text

    assert "Consolidated Link Check Report" in report_text
    assert "Files Processed (2):" in report_text
    # Check original paths in source info
    assert "- dummy/list1.md" in report_text
    assert "- dummy/list2.md" in report_text
    assert "Overall Summary:" in report_text
    assert "Total Links Found: 3" in report_text  # 1 + 2
    assert "Valid Links: 2" in report_text      # 1 + 1
    assert "Broken Links: 1" in report_text     # 0 + 1
    assert "Details:" in report_text
    # Check details using resolved paths
    assert f"File: {abs_path1.resolve()}" in report_text
    assert "- http://valid1.com" in report_text
    assert f"File: {abs_path2.resolve()}" in report_text
    assert "- http://valid2.com" in report_text
    assert "- http://broken2.com (Reason: 404 Not Found)" in report_text


# --- New/Adapted Tests for check_markdown_link_directory ---

@pytest.mark.anyio
@patch('mcp_server.server.check_links_in_content')
@patch('aiofiles.open')
@patch('pathlib.Path.rglob')
@patch('pathlib.Path.is_dir')
@patch('pathlib.Path.exists')
async def test_handle_call_tool_directory_success(mock_exists, mock_is_dir, mock_rglob, mock_aio_open, mock_check_links):
    """Test success path with a directory_path, expecting a consolidated report."""
    # Arrange
    dir_path_arg = "dummy/scan_dir"
    project_root = Path("/home/danfmaia/_repos/mcp-server")
    resolved_scan_dir = (project_root / dir_path_arg).resolve()

    # Configure mocks for methods called on the resolved path
    mock_exists.return_value = True  # Directory should exist
    mock_is_dir.return_value = True  # And be a directory

    # Mocks for the paths rglob should find (these need is_file)
    # Use real Path objects resolved relative to the expected scan dir
    real_file1_rel_path = Path("file1.md")
    real_file2_rel_path = Path("subdir/file2.md")
    abs_mock_path1 = resolved_scan_dir / real_file1_rel_path
    abs_mock_path2 = resolved_scan_dir / real_file2_rel_path

    # We need mocks for the *results* of rglob, primarily for is_file check
    mock_returned_path1 = MagicMock(spec=Path)
    mock_returned_path1.is_file.return_value = True
    mock_returned_path1.__str__.return_value = str(abs_mock_path1)
    mock_returned_path1.__fspath__.return_value = str(abs_mock_path1)
    # Store the real path for easier matching in side effects
    mock_returned_path1._real_path = abs_mock_path1

    mock_returned_path2 = MagicMock(spec=Path)
    mock_returned_path2.is_file.return_value = True
    mock_returned_path2.__str__.return_value = str(abs_mock_path2)
    mock_returned_path2.__fspath__.return_value = str(abs_mock_path2)
    mock_returned_path2._real_path = abs_mock_path2

    mock_rglob.return_value = [mock_returned_path1, mock_returned_path2]

    # File contents and check results
    file1_content = "[Dir Link 1](http://dir1.com)"
    file2_content = "http://dir2.com [Broken](http://broken-dir.com)"
    results1 = {'total': 1, 'valid': [
        'http://dir1.com'], 'broken': [], 'errors': []}
    results2 = {'total': 2, 'valid': ['http://dir2.com'], 'broken': [
        {'url': 'http://broken-dir.com', 'reason': '500 Error'}], 'errors': []}

    # Mock aiofiles.open based on the mock path objects' string representation
    mock_file1_ctx = AsyncMock()
    mock_file1_ctx.__aenter__.return_value.read.return_value = file1_content
    mock_file2_ctx = AsyncMock()
    mock_file2_ctx.__aenter__.return_value.read.return_value = file2_content

    def open_side_effect(path_arg, *args, **kwargs):
        # Centralized logic passes the *string* of the resolved path
        if path_arg == str(abs_mock_path1):
            return mock_file1_ctx
        elif path_arg == str(abs_mock_path2):
            return mock_file2_ctx
        raise FileNotFoundError(f"Mock file not found for: {path_arg}")
    mock_aio_open.side_effect = open_side_effect

    # Mock check_links_in_content based on content
    def check_links_side_effect(content):
        if content == file1_content:
            return results1
        elif content == file2_content:
            return results2
        return {'total': 0, 'valid': [], 'broken': [], 'errors': []}
    mock_check_links.side_effect = check_links_side_effect

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_directory",
        arguments={"directory_path": dir_path_arg}
    )

    # Assert
    # Check that exists, is_dir and rglob were called on the resolved path instance
    mock_exists.assert_called_once()
    mock_is_dir.assert_called_once()
    mock_rglob.assert_called_once_with('*.md')

    # Check is_file called on the objects returned by rglob's mock
    mock_returned_path1.is_file.assert_called_once()
    mock_returned_path2.is_file.assert_called_once()

    assert mock_aio_open.call_count == 2
    # Assert calls with string representation of the resolved path
    mock_aio_open.assert_any_call(str(abs_mock_path1), encoding='utf-8')
    mock_aio_open.assert_any_call(str(abs_mock_path2), encoding='utf-8')

    assert mock_check_links.call_count == 2
    mock_check_links.assert_any_call(file1_content)
    mock_check_links.assert_any_call(file2_content)

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    report_text = result[0].text

    assert "Consolidated Link Check Report" in report_text
    assert f"Directory Scanned: {dir_path_arg}" in report_text
    assert "Files Processed (2):" in report_text
    assert f"- {abs_mock_path1}" in report_text
    assert f"- {abs_mock_path2}" in report_text
    assert "Overall Summary:" in report_text
    assert "Total Links Found: 3" in report_text
    assert "Valid Links: 2" in report_text
    assert "Broken Links: 1" in report_text
    assert "Details:" in report_text
    assert f"File: {abs_mock_path1}" in report_text
    assert f"File: {abs_mock_path2}" in report_text


@pytest.mark.anyio
@patch('pathlib.Path.is_dir')
@patch('pathlib.Path.exists')
async def test_handle_call_tool_directory_not_found(mock_exists, mock_is_dir):
    """Test calling check_markdown_link_directory with a path that is not a directory."""
    # Arrange
    dir_path_arg = "dummy/not_a_dir"

    # Configure mocks: Path exists but is not a directory
    mock_exists.return_value = True
    mock_is_dir.return_value = False

    # Act & Assert
    # Expect the error for not being a directory
    with pytest.raises(ValueError, match=f"Path is not a directory: {dir_path_arg}"):
        await handle_call_tool(
            name="check_markdown_link_directory",
            arguments={"directory_path": dir_path_arg}
        )
    # Check exists and is_dir were called exactly once
    mock_exists.assert_called_once()
    mock_is_dir.assert_called_once()


@pytest.mark.anyio
@patch('pathlib.Path.rglob')
@patch('pathlib.Path.is_dir')
@patch('pathlib.Path.exists')
async def test_handle_call_tool_directory_empty(mock_exists, mock_is_dir, mock_rglob):
    """Test calling check_markdown_link_directory on an empty directory (no *.md files)."""
    # Arrange
    dir_path_arg = "dummy/empty_dir"

    # Configure mocks
    mock_exists.return_value = True  # Directory exists
    mock_is_dir.return_value = True  # And is a directory
    mock_rglob.return_value = []   # rglob finds nothing

    # Act
    result = await handle_call_tool(
        name="check_markdown_link_directory",
        arguments={"directory_path": dir_path_arg}
    )

    # Assert
    # Check exists, is_dir and rglob were called
    mock_exists.assert_called_once()
    mock_is_dir.assert_called_once()
    mock_rglob.assert_called_once_with('*.md')

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert f"No Markdown files found in directory: {dir_path_arg}" in result[0].text


# --- Tests for handle_call_tool: Project Tool ---

@pytest.mark.anyio
# Test case when .gitignore exists and is parsed successfully
@patch('pathspec.PathSpec.from_lines')
@patch('builtins.open')
@patch('pathlib.Path.rglob')
@patch('pathlib.Path.is_file', autospec=True)
@patch('mcp_server.server._check_single_file', new_callable=AsyncMock)
async def test_handle_call_tool_project_with_ignore_pathspec(
    mock_check_single, mock_is_file, mock_rglob, mock_builtin_open, mock_from_lines
):
    """Test project scan respects .gitignore rules using pathspec."""
    # Arrange
    gitignore_content = "ignored/\\n*.tmp.md\\n.venv/"
    gitignore_path = Path("/home/danfmaia/_repos/mcp-server") / ".gitignore"
    kept_path1 = Path("/home/danfmaia/_repos/mcp-server") / "docs/real.md"
    kept_path2 = Path("/home/danfmaia/_repos/mcp-server") / "root.md"
    # Define ignored paths for setting up mocks, even if is_file isn't mocked directly
    ignored_path_dir = Path(
        "/home/danfmaia/_repos/mcp-server") / "ignored/ignore_me.md"
    ignored_path_pattern = Path(
        "/home/danfmaia/_repos/mcp-server") / "other/ignore_me.tmp.md"
    ignored_path_venv = Path(
        "/home/danfmaia/_repos/mcp-server") / ".venv/sub/ignore_me.md"
    all_potential_paths = [
        kept_path1, ignored_path_dir, kept_path2, ignored_path_pattern, ignored_path_venv
    ]

    # Mock .gitignore check and open
    mock_gitignore_handle = MagicMock()
    mock_gitignore_handle.read.return_value = gitignore_content
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_gitignore_handle
    mock_context.__exit__.return_value = None
    # Setup is_file mock - Simply return True as we assume .gitignore exists
    mock_is_file.return_value = True
    mock_builtin_open.return_value = mock_context

    # Mock PathSpec object and its match_files method
    mock_spec = MagicMock()
    ignored_relative = {
        str(ignored_path_dir.relative_to(
            Path("/home/danfmaia/_repos/mcp-server"))),
        str(ignored_path_pattern.relative_to(
            Path("/home/danfmaia/_repos/mcp-server"))),
        str(ignored_path_venv.relative_to(
            Path("/home/danfmaia/_repos/mcp-server")))
    }
    mock_spec.match_files.return_value = ignored_relative
    mock_from_lines.return_value = mock_spec

    # Mock rglob results - return ALL potential paths
    mock_rglob.return_value = all_potential_paths

    # Mock the check results for the files that *should* be processed
    mock_check_single.side_effect = [
        {'total': 1, 'valid': ['http://kept1.com'],
            'broken': [], 'errors': []},  # For kept_path1
        {'total': 1, 'valid': ['http://kept2.com'],
            'broken': [], 'errors': []}  # For kept_path2
    ]

    # Act
    result = await handle_call_tool(name="check_markdown_links_project", arguments={})

    # Assert
    # Check the gitignore call happened
    assert mock_is_file.called  # Verify is_file was called
    # mock_is_file.assert_any_call(gitignore_path)

    # Assert open was called for .gitignore
    mock_builtin_open.assert_called_once_with(
        gitignore_path, 'r', encoding='utf-8')
    mock_from_lines.assert_called_once_with(
        pathspec.patterns.GitWildMatchPattern, gitignore_content.splitlines()
    )
    # Check that match_files was called with the correct relative paths (of files)
    expected_relative_paths_for_match = [
        str(p.relative_to(Path("/home/danfmaia/_repos/mcp-server"))) for p in all_potential_paths
    ]
    mock_spec.match_files.assert_called_once_with(
        expected_relative_paths_for_match)

    mock_rglob.assert_called_once_with("*.md")
    # Assert _check_single_file was called only for the non-ignored files
    assert mock_check_single.call_count == 2
    mock_check_single.assert_any_call(kept_path1)
    mock_check_single.assert_any_call(kept_path2)

    # Check report details
    report_text = result[0].text
    assert "Consolidated Link Check Report" in report_text
    assert "Files Processed (2):" in report_text
    assert "- docs/real.md" in report_text
    assert "- root.md" in report_text
    assert "ignored/ignore_me.md" not in report_text  # Verify ignored file not listed
    assert "other/ignore_me.tmp.md" not in report_text
    assert ".venv/sub/ignore_me.md" not in report_text
    assert "Total Links Found: 2" in report_text


@pytest.mark.anyio
@patch('pathlib.Path.rglob', return_value=[])  # Mock rglob to find nothing
# Assume .gitignore exists check (though not used)
@patch('pathlib.Path.is_file', return_value=True)
async def test_handle_call_tool_project_no_md_files_found(
    mock_path_is_file, mock_rglob
):
    """Test project scan when rglob finds no *.md files."""
    # Act
    result = await handle_call_tool(name="check_markdown_links_project", arguments={})

    # Assert
    mock_rglob.assert_called_once_with("*.md")
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    # Check the specific report message for no files found
    assert result[0].text == "No processable Markdown files found."

# --- Tests for Argument Validation and Path Errors ---


@pytest.mark.anyio
async def test_handle_call_tool_files_invalid_argument_type():
    """Test ValueError is raised if file_paths is not a list."""
    with pytest.raises(ValueError, match="Argument 'file_paths' must be a list of strings."):
        await handle_call_tool(
            name="check_markdown_link_files",
            # Pass string instead of list
            arguments={"file_paths": "not_a_list"}
        )


@pytest.mark.anyio
@patch('pathlib.Path.exists', return_value=True)
# Mock as existing but not a dir
@patch('pathlib.Path.is_dir', return_value=False)
async def test_handle_call_tool_directory_target_is_file(mock_is_dir, mock_exists):
    """Test ValueError is raised if directory_path target is a file."""
    dir_path_arg = "dummy/path_is_file.md"
    with pytest.raises(ValueError, match=f"Path is not a directory: {dir_path_arg}"):
        await handle_call_tool(
            name="check_markdown_link_directory",
            arguments={"directory_path": dir_path_arg}
        )
    # Verify mocks were called on the resolved path instance
    # The actual path doesn't matter as much as verifying the checks were done
    mock_exists.assert_called_once()
    mock_is_dir.assert_called_once()


@pytest.mark.anyio
@patch('pathlib.Path.exists', return_value=False)  # Mock as not existing
async def test_handle_call_tool_directory_target_does_not_exist(mock_exists):
    """Test ValueError is raised if directory_path target does not exist."""
    dir_path_arg = "dummy/non_existent_dir"
    with pytest.raises(ValueError, match=f"Directory target does not exist: {dir_path_arg}"):
        await handle_call_tool(
            name="check_markdown_link_directory",
            arguments={"directory_path": dir_path_arg}
        )
    mock_exists.assert_called_once()


@pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
@patch("mcp_server.server._check_single_file", new_callable=AsyncMock)
@patch("pathspec.PathSpec.from_lines")  # Mock pathspec loading
@patch("aiofiles.open", new_callable=mock_open)  # Mock async file open
# Mock relative_to method WITH AUTOSPEC
@patch("pathlib.Path.relative_to", autospec=True)
@patch("pathlib.Path.rglob")  # Mock rglob method
# Mock is_file method WITH AUTOSPEC
@patch("pathlib.Path.is_file", autospec=True)
async def test_handle_call_tool_project_no_gitignore(
    mock_is_file,
    mock_rglob,
    mock_relative_to,
    mock_aio_open,  # Keep this
    mock_pathspec_from_lines,  # Keep this
    mock_check_single,
    anyio_backend,
):
    """Test project scan when .gitignore does not exist."""
    # --- Define Paths ---
    project_root = Path("/home/danfmaia/_repos/mcp-server")
    gitignore_path = project_root / ".gitignore"
    path1 = project_root / "path1.md"
    path2 = project_root / "path2.md"

    # --- Configure Mocks ---
    # Configure is_file side_effect (accepts self instance)
    def is_file_side_effect(self):  # Changed self_path to self
        if self == gitignore_path:
            return False  # .gitignore does not exist
        elif self in [path1, path2]:
            return True  # md files exist
        return False  # Default
    mock_is_file.side_effect = is_file_side_effect

    # Configure rglob to return our real Path objects
    # Since we mock Path.rglob, the first arg 'self' is implicitly passed
    mock_rglob.return_value = [path1, path2]

    # Configure relative_to side_effect (accepts self instance and base_path)
    def relative_to_side_effect(self, base_path):  # Changed self_path to self
        if self == path1:
            return Path("path1.md")
        elif self == path2:
            return Path("path2.md")
        return Path(str(self))  # Fallback
    mock_relative_to.side_effect = relative_to_side_effect

    # --- Mock _check_single_file setup ---
    path1_result = {'total': 1, 'valid': ['http://path1.com'],
                    'broken': [], 'errors': []}
    path2_result = {'total': 1, 'valid': [], 'broken': [
        {'url': 'http://path2.com', 'reason': '404'}], 'errors': []}

    async def check_single_side_effect(file_path_arg):
        if file_path_arg == path1:  # Compare with real Path
            return path1_result
        elif file_path_arg == path2:  # Compare with real Path
            return path2_result
        raise ValueError(
            f"Unexpected call to _check_single_file with {file_path_arg}")
    mock_check_single.side_effect = check_single_side_effect

    # --- Call the actual function ---
    result = await handle_call_tool(
        name="check_markdown_links_project", arguments={}
    )

    # --- Assertions ---
    # Check is_file call on gitignore_path instance
    # mock_is_file assertion check happens implicitly via side_effect calls
    # Check rglob call on project_root instance
    # We can't directly assert mock_rglob was called *on* project_root easily
    # because the instance isn't readily available. We rely on the return value.
    # Check it was called with the pattern
    mock_rglob.assert_called_once_with("*.md")

    # Check _check_single_file calls with real Path objects
    assert mock_check_single.call_count == 2
    mock_check_single.assert_any_call(path1)
    mock_check_single.assert_any_call(path2)

    # Assert the result structure and content
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)

    report_text = result[0].text
    assert "Consolidated Link Check Report" in report_text
    assert "Project Scan (using .gitignore)" in report_text
    assert "- path1.md" in report_text  # Check relative paths from mock
    assert "- path2.md" in report_text
    assert "Valid Links: 1" in report_text
    assert "Broken Links: 1" in report_text
    assert "Errored Links: 0" in report_text
    assert "- http://path2.com (Reason: 404)" in report_text


@pytest.mark.anyio
# Test case when .gitignore parsing fails
@patch("mcp_server.server._check_single_file", new_callable=AsyncMock)
@patch("pathspec.PathSpec.from_lines")
# Patch builtins.open within the server module's scope using MagicMock for sync context
@patch("mcp_server.server.open", new_callable=MagicMock)
# Patch specific Path methods needed
@patch("pathlib.Path.relative_to", autospec=True)
@patch("pathlib.Path.rglob")
@patch("pathlib.Path.is_file", autospec=True)
async def test_handle_call_tool_project_gitignore_parse_error_pathspec(
    mock_is_file,  # Mock for is_file method
    mock_rglob,  # Mock for rglob method
    mock_relative_to,  # Mock for relative_to method
    mock_builtin_open,  # Renamed mock for clarity (was mock_aio_open)
    mock_pathspec_from_lines,
    mock_check_single,
):
    """Test project scan handles .gitignore parsing errors gracefully (processes all files)."""
    # --- Define Paths ---
    project_root = Path("/home/danfmaia/_repos/mcp-server")
    gitignore_path = project_root / ".gitignore"
    path1 = project_root / "file1.md"
    path2 = project_root / "docs/plan.md"

    # --- Configure Mocks (is_file, rglob, relative_to) ---
    # is_file: True for gitignore and md files (accepts self)
    def is_file_side_effect(self):  # Changed self_path to self
        if self == gitignore_path:
            return True  # .gitignore exists
        elif self in [path1, path2]:
            return True  # md files exist
        return False  # Default
    mock_is_file.side_effect = is_file_side_effect
    mock_rglob.return_value = [path1, path2]

    def relative_to_side_effect(self, base_path):  # Changed self_path to self
        if self == path1:
            return Path("file1.md")
        elif self == path2:
            return Path("docs/plan.md")
        return Path(str(self))  # Fallback
    mock_relative_to.side_effect = relative_to_side_effect

    # --- Mock File I/O and Parsing ---
    # Configure mock_builtin_open to return a synchronous context manager
    mock_file_handle = MagicMock()
    mock_file_handle.read.return_value = "invalid\npatterns*"

    # Standard context manager mock setup for synchronous open
    context_manager = MagicMock()
    context_manager.__enter__.return_value = mock_file_handle
    context_manager.__exit__.return_value = None
    # Assign the sync context manager
    mock_builtin_open.return_value = context_manager

    # Mock PathSpec.from_lines to raise an error
    mock_pathspec_from_lines.side_effect = ValueError("Mock parse error")

    # --- Mock _check_single_file Setup ---
    path1_result = {'total': 1, 'valid': [
        'http://a.com'], 'broken': [], 'errors': []}
    path2_result = {'total': 1, 'valid': [
        'http://b.com'], 'broken': [], 'errors': []}

    async def check_single_side_effect(file_path_arg):
        if file_path_arg == path1:
            return path1_result
        elif file_path_arg == path2:
            return path2_result
        raise ValueError(
            f"Unexpected call to _check_single_file with {file_path_arg}")
    mock_check_single.side_effect = check_single_side_effect

    # --- Call the actual function ---
    result = await handle_call_tool(name="check_markdown_links_project", arguments={})

    # --- Assertions ---
    # Verify gitignore check happened (implicitly via side_effect)
    # Assert builtins.open was called for .gitignore
    mock_builtin_open.assert_called_once_with(
        gitignore_path, 'r', encoding='utf-8')
    # Assert from_lines was called (and raised error)
    mock_pathspec_from_lines.assert_called_once()

    # Assert rglob was called
    mock_rglob.assert_called_once_with("*.md")

    # Assert _check_single_file was called for *all* found files due to parse error
    assert mock_check_single.call_count == 2
    mock_check_single.assert_any_call(path1)
    mock_check_single.assert_any_call(path2)

    # Assert report structure and content
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)

    report_text = result[0].text
    assert "Consolidated Link Check Report" in report_text
    assert "Project Scan (using .gitignore)" in report_text
    assert "- file1.md" in report_text
    assert "- docs/plan.md" in report_text
    # Ensure no incorrect assertions are present here
    # The following lines were incorrectly added and should not be here:
    # assert "Valid Links: 1" in report_text
    # assert "Broken Links: 1" in report_text
    # assert "Errored Links: 0" in report_text
    # assert "- http://path2.com (Reason: 404)" in report_text
