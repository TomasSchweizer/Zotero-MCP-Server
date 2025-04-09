"""
A simple MCP server which allows querying PDFs and Notes from Zotero.
"""

from typing import Tuple, List, Dict
import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from pyzotero import zotero
#from bs4 import BeautifulSoup

from .log import logger
from .parser import note_title_parser


# Load envs
load_dotenv()
LIBRARY_ID = os.getenv("LIBRARY_ID")
LIBRARY_TYPE = os.getenv("LIBRARY_TYPE")



# Setup
zotero_client = zotero.Zotero(library_id=LIBRARY_ID,
                                library_type=LIBRARY_TYPE,
                                local=True)

mcp = FastMCP(name="ZoteroMCPServer",
                    version = "0.1.0"
                  )

@mcp.tool()
def search_zotero_library(limit: int, query: str):
    """Search zotero library via text query""" # TODO extend the description

    found_items = pyzotero_search_library(limit=limit, query=query)

    parsed_items = pyzotero_search_parser(found_items=found_items)

    return parsed_items

def pyzotero_search_library(limit: int, query: str) -> List:
    """Search zotero library using pyzotero via text query"""
    zotero_client.add_parameters(limit=limit, q=query, qmode="everything")
    found_items = zotero_client.items() # type: ignore 
    logger.info("Search results: %d item(s) found%s",
            len(found_items),
            '' if found_items else ' - no items match the search query')
    assert isinstance(found_items, list)
    if not isinstance(found_items, list):
        raise TypeError(f"The found items need to be a of type: {type(list())} \
                            but it is of type: {type(found_items)}")
    return found_items

def pyzotero_search_parser(found_items: List) -> Dict:
    """Parse the found items of the zotero client"""

    search_results = {}

    for found_item in found_items:
        if not isinstance(found_item, dict):
            raise TypeError(f"The found item need to be a of type {type(dict())}, \
                                but is of type: {type(found_item)}.")
        item_key = found_item["key"]
        item_data = found_item["data"]
        item_type = item_data["itemType"]
        item_collection_keys = item_data["collections"]

        item_collection_names = [
            get_parent_collections(item_collection_key)[0]
            for item_collection_key in item_collection_keys
        ]

        if item_type not in search_results:
            search_results[item_type] = []

        if item_type=="note":
            item_title = note_title_parser(item_data["note"])
            search_results[item_type].append({
                "itemKey": item_key,
                "itemType": item_type,
                "itemTitle": item_title,
                "itemCollectionNames": item_collection_names
            })
        else:
            print("Not Implemented!")

    return search_results

def get_parent_collections(collection_key: str, depth: int = 0) -> Tuple[List[str],int]:
    """Recursively retrieves the names of a collection and all of its parent collections.
    
    Args:
        collection_key: The key of the collection to retrieve.
        depth: Current recursion depth (0 for the initial call).
        max_depth: Maximum depth determined during recursion (used for reversing depth numbers).
    
    Returns:
        A list of collection names from parent to child with reversed depth numbering.
    """
    # For debugging, you can print the current depth
    print(f"{'  ' * depth}Depth {depth}: Processing collection key: {collection_key}")

    collection_dict: Dict = zotero_client.collection(collection_key) # type: ignore
    assert isinstance(collection_dict, dict)
    if not isinstance(collection_dict, dict):
        raise TypeError(f"The found item need to be a of type {type(dict())}, \
                            but is of type: {type(collection_dict)}.")
    collection_data = collection_dict["data"]
    collection_name = collection_data["name"]
    parent_collection_key = collection_data["parentCollection"]

    # Print info about the current collection
    #print(f"{'  ' * depth}Depth {depth}: Found collection '{collection_name}'")

    if parent_collection_key is False:
        #print(f"{'  ' * depth}Depth {depth}: Reached top-level collection, returning and adding '{collection_name}'")
        # We've reached the top, so this is our base case
        # Calculate the total depth of the hierarchy
        total_depth = depth
        
        # For the top-level collection, the reversed depth is always 0
        return [f"Collection depth=0: {collection_name}"], total_depth

    # Recursive case - increment depth for the next call
    #print(f"{'  ' * depth}Depth {depth}: Going up to parent collection: {parent_collection_key}")
    parent_collections, total_depth = get_parent_collections(parent_collection_key, depth + 1)
    
    # Calculate reversed depth (0 at top, increasing as we go down)
    reversed_depth = total_depth - depth

    #print(f"{'  ' * depth}Depth {depth}: Returned from recursion, adding '{collection_name}' with reversed depth {reversed_depth}")
    collection_entry = f"Collection depth={reversed_depth}: {collection_name}"

    return parent_collections + [collection_entry], total_depth


if __name__ == "__main__":

    # Setup logger
    logger.info("Setup logger done: %s", str(logger))

    # Run mpc server.
    logger.info("Starting Zotero MCP server ...")
    mcp.run()
