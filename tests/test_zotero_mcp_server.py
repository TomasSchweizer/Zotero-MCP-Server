"""Tests for the Zotero MCP Server implementation"""

import logging
import json
import re

import pytest

from zotero_mcp_server.zotero_mcp_server import search_zotero_library, retrieve_zotero_items_content


logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
test_logger = logging.getLogger(__name__)


@pytest.fixture(scope="function",
                name="load_patch_data_query_library_fixture",
                params=["./tests/tests_data/patch_query_library_response_limit-10000_query-04 Bridge the gap from current state to ideal state.json",
                        "./tests/tests_data/patch_query_library_response_limit-10000_query-Intelligence.json",
                        "./tests/tests_data/patch_query_library_response_limit-10000_query-OWASP.json",
                        "./tests/tests_data/patch_query_library_response_limit-10000_query-Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz.json",
                        "./tests/tests_data/patch_query_library_response_limit-10000_query-Snyk.json"
                        ]
)
def load_patch_data_query_library(request):
    """Load patch data to test querying the library"""
    tests_data_path = request.param
    test_data = _read_json(tests_data_path)

    inputs_query_library = {"limit": int(re.search(r"limit-(\d+)", tests_data_path).group(1)), #type: ignore
                            "query": re.search(r"query-(.*?)\.json", tests_data_path).group(1)} #type: ignore
    patch_found_items = test_data.get("found_items")
    test_parsed_items_metadata =  test_data.get("parsed_items_metadata")

    return inputs_query_library, patch_found_items, test_parsed_items_metadata

@pytest.fixture(scope="function",
                name="patch_query_library_fixture")
def patch_query_library(monkeypatch, load_patch_data_query_library_fixture):
    """Mocks the PyzoteroClient.query_library method."""
    inputs_query_library, patch_found_items, test_parsed_items_metadata = load_patch_data_query_library_fixture

    monkeypatch.setattr(
        "zotero_mcp_server.pyzotero_wrapper.PyzoteroClient.query_library",
        lambda self, limit, query: patch_found_items
    )
    return inputs_query_library, patch_found_items, test_parsed_items_metadata

def test_search_zotero_library(patch_query_library_fixture) -> None:
    """Tests the search_zotero_library function."""
    #test_logger.info(patch_query_library_fixture[0])
    inputs_query_library, patch_found_items, expected_parsed_items_metadata = patch_query_library_fixture
    limit = inputs_query_library["limit"]
    test_logger.info(limit)
    query = inputs_query_library["query"]

    status_message, parsed_items_metadata = search_zotero_library(limit, query)

    if not patch_found_items:
        expected_status_message = "Search results: 0 items found - no items match the search query"
    else:
        expected_status_message = f"Search results: {len(parsed_items_metadata)} item{'s' if len(parsed_items_metadata) > 1 else ''} found"
    assert status_message == expected_status_message, f"Expected '{expected_status_message}', got '{status_message}'"
    assert parsed_items_metadata == expected_parsed_items_metadata, "Parsed metadata does not match expected metadata"

@pytest.fixture(scope="function",
                name="load_test_data_retrieve_zotero_items_content_fixture",
                params=["./tests/tests_data/test_data_retrieve_zotero_items_content.json"]
                )

def load_test_data_retrieve_zotero_items_content(request):
    """Load test data for retrieving item content."""
    tests_data_path = request.param
    test_data = _read_json(tests_data_path)

    item_keys = test_data.get("item_keys")
    test_retrieved_items_content =  test_data.get("retrieved_items_content")

    return item_keys, test_retrieved_items_content

def test_retrieve_zotero_items_content(load_test_data_retrieve_zotero_items_content_fixture):
    """Tests the retrieve_zotero_items_content function."""

    item_keys, test_retrieved_items_content = load_test_data_retrieve_zotero_items_content_fixture
    retrieved_items_content = retrieve_zotero_items_content(item_keys)

    assert test_retrieved_items_content == retrieved_items_content, "Parsed content does not match expected content"

def _read_json(filename: str) -> dict:
    """Reads data from a JSON file and returns it as a Python dictionary.

    Args:cl
        filename (str): The name of the JSON file to read.

    Returns:
        dict: A Python dictionary representing the data from the JSON file.
              Returns an empty dictionary if the file is not found or an error occurs.
    """
    try:
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filename}'. \
              The file might be corrupted or not valid JSON.")
        return {}
    except IOError as e:
        print(f"Error reading file '{filename}': {e}")
        return {}
