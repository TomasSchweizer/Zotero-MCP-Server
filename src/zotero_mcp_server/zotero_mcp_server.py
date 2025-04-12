"""
A simple MCP server which allows querying PDFs and Notes from Zotero.
"""
from typing import Tuple, List, Dict
import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

from .log import logger
from .pyzotero_wrapper import PyzoteroClient, PyzoteroParser


# Load environment variables
load_dotenv()
LIBRARY_ID = os.getenv("LIBRARY_ID")
LIBRARY_TYPE = os.getenv("LIBRARY_TYPE")

pyzotero_client = PyzoteroClient(library_id=LIBRARY_ID,
                                    library_type=LIBRARY_TYPE,
                                    local=True)
pyzotero_parser = PyzoteroParser(pyzotero_client=pyzotero_client)

mcp = FastMCP(name="ZoteroMCPServer", version="0.1.0")


@mcp.tool()
def search_zotero_library(limit: int, query: str) -> Tuple[str, List]:
    """
    Search the Zotero library for items matching the provided query.
    
    This function queries the Zotero library with the specified search parameters,
    parses the metadata of found items, and returns both a formatted status message
    and the list of parsed item metadata.
    
    Args:
        limit (int): Maximum number of items to return in the search results.
        query (str): Search query string to find matching items in the Zotero library.
            The query uses Zotero's "everything" mode, searching across all fields.
    
    Returns:
        Tuple[str, List]: A tuple containing:
            - str: Status message indicating the number of items found.
            - List: List of dictionaries containing parsed metadata for each found item.
            Each dictionary includes keys such as "itemKey", "itemType", "itemTitle",
            and "itemCollectionNames".
    
    Example:
        >>> status, results = search_zotero_library(10, "machine learning")
        >>> print(status)
        "Search results: 5 items found"
    """

    found_items = pyzotero_client.query_library(limit=limit, query=query)
    if not found_items:
        return "Search results: 0 items found - no items match the search query" , found_items

    parsed_items_metadata = pyzotero_parser.parse_items_metadata(found_items=found_items)

    return f"Search results: {len(parsed_items_metadata)} item{'s' if len(parsed_items_metadata) > 1 else ''} found", \
            parsed_items_metadata

@mcp.tool()
def retrieve_zotero_item_content(item_key: str) -> Dict:
    """
    Retrieve and parse the content of a specific Zotero item by its key.
    
    This function retrieves a single item from the Zotero library using its unique key,
    then parses the item's content into a structured format suitable for processing.
    The parsing strategy is automatically determined based on the item type (note, PDF, etc.).
    
    Args:
        item_key (str): The unique identifier key of the Zotero item to retrieve.
    
    Returns:
        Dict: A dictionary containing the parsed item content with the following keys:
            - "itemKey": The unique key identifier of the item.
            - "itemTitle": The title of the item, extracted based on item type.
            - "itemContent": The content of the item, which varies by type:
                - For notes: HTML content of the note
                - For PDFs: Extracted text content
                - For other items: May contain minimal or empty content
    
    Example:
        >>> item_content = retrieve_zotero_item("ABC123XYZ")
        >>> print(item_content["itemTitle"])
        "Machine Learning Fundamentals"
    """
    retrieved_item = pyzotero_client.retrieve_item(item_key)

    parsed_item_content = pyzotero_parser.parse_item_content(retrieved_item)

    return parsed_item_content

if __name__ == "__main__":
    logger.info("Starting ZoteroMCPServer ...")
    mcp.run()
