"""Tests for the Zotero MCP Server implementation"""

import logging
import json

import pytest

from zotero_mcp_server.zotero_mcp_server import ZoteroMCPServer
from zotero_mcp_server.pyzotero_wrapper import PyzoteroClient, NotePyzoteroParsingStrategy, ItemPyzoteroParsingStrategy, PyzoteroParser


logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
test_logger = logging.getLogger(__name__)

@pytest.fixture(scope="function", name="static_pyzotero_items_fixture")
def static_pyzotero_items():
    """Fixture to load static pyzotero responses from a JSON file."""
    
    return _read_json("./tests/test_pyzotero_items.json")

@pytest.fixture(scope="function", name="notes_items_fixture")
def notes_items(static_pyzotero_items_fixture):
    """Fixture to extract the note items from the static pyzotero items"""
    return static_pyzotero_items_fixture["notes"]

@pytest.fixture(scope="function", name="notes_html_fixture")
def notes_html(notes_items_fixture):
    """Fixture to extract the notes html from note items."""
    return [note_item["data"]["note"] for note_item in notes_items_fixture]

@pytest.fixture(scope="function", name="notes_titles_fixture")
def notes_titles(notes_items_fixture):
    """Fixture to extract the notes html from note items."""
    return [note_item["data"]["test_note_title"] for note_item in notes_items_fixture]


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

