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
def retrieve_zotero_items_content(item_keys: List[str]) -> List[Dict[str, str]]:
    """
    Retrieve and parse the content of specific Zotero items by their keys.
    
    This function fetches the full content of one or more Zotero items identified by their keys,
    processes them using the appropriate parser strategy based on item type (note, PDF, etc.),
    and returns the parsed content in a structured format.
    
    Args:
        item_keys (List[str]): A list of Zotero item keys (unique identifiers) for which 
            to retrieve and parse content. Each key should be a string.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries, one for each retrieved item, containing:
            - "itemKey" (str): The unique key identifier of the Zotero item
            - "itemTitle" (str): The title of the item
            - "itemContent" (str or Dict): The parsed content of the item, which may be:
                - HTML content for notes 
                - Extracted text for PDFs
                - Empty dict for items without extractable content
    
    Notes:
        - For PDF attachments, the function extracts and returns the full text content
        - For notes, the function returns the HTML content of the note
        - The parsing strategy is automatically determined based on the item type and content type
    
    Example:
        >>> item_contents = retrieve_zotero_item_content(["ABC123", "DEF456"])
        >>> print(f"Retrieved {len(item_contents)} items")
        "Retrieved 2 items"
    """
    retrieved_items = pyzotero_client.retrieve_items(item_keys)

    parsed_items_content = pyzotero_parser.parse_items_content(retrieved_items)

    return parsed_items_content

if __name__ == "__main__":
    print(search_zotero_library(limit=100, query="03_tcpdump traffic log"))
    logger.info("Starting ZoteroMCPServer ...")
    mcp.run()
