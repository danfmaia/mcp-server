# tests/test_link_checker.py

# from unittest.mock import MagicMock, AsyncMock # No longer needed for these tests
import asyncio

# import re # Removed unused import
from unittest.mock import patch

import aiohttp
import pytest  # Re-enabled for asyncio decorator
from aioresponses import aioresponses

# Updated import path - Re-enable when tests are uncommented
from mcp_server.tools.link_checker import (
    _check_link_status,
    _extract_links,
    check_links_in_content,
)

# --- Extraction Tests (Keep commented for now, focus on checking tests) ---


def test_extracts_no_links():
    """Test that no links are found in plain text."""
    markdown = "This is some text without any links."
    assert _extract_links(markdown) == []


def test_extracts_simple_http_link():
    """Test extracting a single basic HTTP link."""
    markdown = "Check this out: http://example.com"
    expected = ["http://example.com"]
    assert _extract_links(markdown) == expected


def test_extracts_simple_https_link():
    """Test extracting a single basic HTTPS link."""
    markdown = "Another link https://example.org/page is here."
    expected = ["https://example.org/page"]
    assert _extract_links(markdown) == expected


def test_extracts_link_in_markdown_syntax():
    """Test extracting a link within Markdown []() syntax."""
    markdown = "A [link](http://example.com/markdown) is here."
    expected = ["http://example.com/markdown"]
    assert _extract_links(markdown) == expected


def test_extracts_multiple_links():
    """Test extracting multiple links of different types."""
    markdown = "Visit http://one.com and [this one](https://two.org/path?q=1)."
    expected = ["http://one.com", "https://two.org/path?q=1"]
    # Use set comparison for order independence if needed
    assert sorted(_extract_links(markdown)) == sorted(expected)

# --- Tests for _check_link_status (Manual aioresponses Instantiation) ---


@pytest.mark.asyncio
async def test_check_link_status_valid():  # Removed aioresponses param
    """Test checks valid (200 OK) link using manual aioresponses."""
    url = "http://valid-example.com"
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, status=200)
            status, error = await _check_link_status(session, url)
    assert status == "OK"
    assert error is None


@pytest.mark.asyncio
async def test_check_link_status_redirect_ok():  # Removed aioresponses param
    """Test checks valid redirected (302 Found) link using manual aioresponses."""
    url = "http://redirect-example.com"
    final_url = 'http://final-destination.com'
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, status=302, headers={'Location': final_url})
            m.head(final_url, status=200)
            status, error = await _check_link_status(session, url)
    assert status == "OK"
    assert error is None


@pytest.mark.asyncio
async def test_check_link_status_broken():  # Removed aioresponses param
    """Test checks broken (404 Not Found) link using manual aioresponses."""
    url = "https://broken-example.org"
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, status=404, reason="Not Found")
            status, error = await _check_link_status(session, url)
    assert status == "BROKEN"
    assert error == "404 Not Found"


@pytest.mark.asyncio
async def test_check_link_status_timeout():  # Removed aioresponses param
    """Test checks link timeout using manual aioresponses."""
    url = "https://timeout-example.net"
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, exception=asyncio.TimeoutError())
            status, error = await _check_link_status(session, url)
    assert status == "ERROR"
    assert error == "Timeout"


@pytest.mark.asyncio
async def test_check_link_status_client_error():  # Removed aioresponses param
    """Test checks client error using manual aioresponses."""
    url = "https://conn-error-example.dev"
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, exception=aiohttp.ClientConnectionError(
                "Connection refused"))
            status, error = await _check_link_status(session, url)
    assert status == "ERROR"
    assert error == "ClientConnectionError"


@pytest.mark.asyncio
async def test_check_link_status_unexpected_error():  # Removed aioresponses param
    """Test checks unexpected (non-aiohttp) error using manual aioresponses."""
    url = "https://unexpected-error.com"
    async with aiohttp.ClientSession() as session:  # Create session first
        with aioresponses() as m:
            m.head(url, exception=ValueError("Test unexpected"))
            status, error = await _check_link_status(session, url)
    assert status == "ERROR"
    assert error == "Unexpected: ValueError"

# --- Tests for check_links_in_content (Orchestration) ---


@pytest.mark.asyncio
@patch('mcp_server.tools.link_checker._extract_links')
# Patch session creation
@patch('mcp_server.tools.link_checker.aiohttp.ClientSession')
async def test_check_links_in_content_no_links(mock_session, mock_extract):
    """Test check_links_in_content when no links are extracted."""
    mock_extract.return_value = []
    content = "No links here."

    result = await check_links_in_content(content)

    mock_extract.assert_called_once_with(content)
    mock_session.assert_not_called()  # Session shouldn't be created if no links
    assert result == {"total": 0, "valid": [], "broken": [], "errors": []}


@pytest.mark.asyncio
@patch('mcp_server.tools.link_checker._extract_links')
@patch('mcp_server.tools.link_checker._check_link_status')
async def test_check_links_in_content_all_valid(mock_check_status, mock_extract):
    """Test check_links_in_content with only valid links."""
    links = ["http://valid1.com", "https://valid2.org"]
    mock_extract.return_value = links
    mock_check_status.side_effect = [("OK", None), ("OK", None)]
    content = "Valid links only"

    result = await check_links_in_content(content)

    mock_extract.assert_called_once_with(content)
    assert mock_check_status.call_count == len(links)

    # Verify calls by checking call_args_list, ignoring the first arg (session)
    calls = mock_check_status.call_args_list
    # Extract the second argument (the link) from each call
    called_links = [c.args[1] for c in calls]
    assert sorted(called_links) == sorted(links)

    assert result == {
        "total": 2,
        "valid": links,
        "broken": [],
        "errors": []
    }


@pytest.mark.asyncio
@patch('mcp_server.tools.link_checker._extract_links')
@patch('mcp_server.tools.link_checker._check_link_status')
async def test_check_links_in_content_mixed_results(mock_check_status, mock_extract):
    """Test check_links_in_content with a mix of valid, broken, and error statuses."""
    links = ["http://valid.com", "https://broken.com", "http://error.com"]
    mock_extract.return_value = links
    # Simulate results: OK, BROKEN, ERROR
    mock_check_status.side_effect = [
        ("OK", None),
        ("BROKEN", "404 Not Found"),
        ("ERROR", "Timeout")
    ]
    content = "Mixed links"

    result = await check_links_in_content(content)

    mock_extract.assert_called_once_with(content)
    assert mock_check_status.call_count == len(links)

    assert result == {
        "total": 3,
        "valid": ["http://valid.com"],
        "broken": [{"url": "https://broken.com", "reason": "404 Not Found"}],
        "errors": [{"url": "http://error.com", "reason": "Timeout"}]
    }


@pytest.mark.asyncio
@patch('mcp_server.tools.link_checker._extract_links')
@patch('mcp_server.tools.link_checker._check_link_status')
async def test_check_links_in_content_gather_exception(mock_check_status, mock_extract):
    """Test check_links_in_content when asyncio.gather raises an exception for a task."""
    links = ["http://valid.com", "https://fails.com"]
    mock_extract.return_value = links
    # Simulate OK for first, Exception for second
    mock_check_status.side_effect = [("OK", None), ValueError("Task failed")]
    content = "Link check fails"

    # We need to patch asyncio.gather to simulate an exception being returned
    # Patching _check_link_status to raise is simpler for task failure simulation

    result = await check_links_in_content(content)

    mock_extract.assert_called_once_with(content)
    assert mock_check_status.call_count == len(links)

    assert result == {
        "total": 2,
        "valid": ["http://valid.com"],
        "broken": [],
        "errors": [{"url": "https://fails.com",
                   "reason": "Task Exception: ValueError"}]
    }


@pytest.mark.asyncio
@patch('mcp_server.tools.link_checker._extract_links')
@patch('mcp_server.tools.link_checker._check_link_status')
async def test_check_links_in_content_unexpected_result_type(mock_check_status, mock_extract):
    """Test handling of an unexpected result type from _check_link_status."""
    links = ["http://weird.com"]
    mock_extract.return_value = links
    # Simulate an unexpected return value (not tuple or Exception)
    mock_check_status.return_value = "Just a string"
    content = "Weird result"

    result = await check_links_in_content(content)

    mock_extract.assert_called_once_with(content)
    assert mock_check_status.call_count == len(links)

    assert result == {
        "total": 1,
        "valid": [],
        "broken": [],
        "errors": [{"url": "http://weird.com",
                   "reason": "Unexpected: str"}]
    }
