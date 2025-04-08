"""
A simple MCP server which allows querying PDFs and Notes from Zotero.
"""
from typing import List, Dict, TypeAlias
import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from pyzotero import zotero
from bs4 import BeautifulSoup

from parser import note_parser
from log import setup_logging

NestedDict: TypeAlias = Dict[str, 'NestedDict']

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
def search_library(limit: int, query: str):
    """Search zotero library via text query"""

    zotero_client.add_parameters(limit=limit, q=query, qmode="everything")
    found_items = zotero_client.top()
    if not isinstance(found_items, list):
        raise TypeError(f"The found items need to be a of type: {type(list())} \
                            but it is of type: {type(found_items)}") 

    parsed_items = search_parser(found_items)    
    
    return parsed_items

def search_parser(found_items: List[NestedDict]) -> NestedDict:
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
            get_parent_collections(item_collection_key)
            for item_collection_key in item_collection_keys
        ]

        if item_type not in search_results.keys():
            search_results[item_type] = []

        if item_type=="note":
            item_title = note_parser(item_data["note"])
            search_results[item_type].append({
                "itemKey": item_key,
                "itemType": item_type,
                "itemTitle": item_title,
                "itemCollectionNames": item_collection_names
            })
        else:
            print("Not Implemented!")
    
    return search_results

def get_parent_collections(collection_key: str) -> List[str]:
    """Recursively retrieves the names of a collection and all of its parent collections."""
    
    collection_dict = zotero_client.collection(collection_key)
    if not isinstance(collection_dict, dict):
        raise TypeError(f"The found item need to be a of type {type(dict())}, \
                            but is of type: {type(collection_dict)}.")    
    collection_data = collection_dict["data"]
    collection_name = collection_data["name"]
    parent_collection_key = collection_data["parentCollection"]

    if parent_collection_key is False:
        return list(collection_name)
    
    return list(collection_name) + get_parent_collections(parent_collection_key)


if __name__ == "__main__":



    # Setup logger
    logger = setup_logging()
    logger.info(f"Setup logger done: {logger}")

    # Run mpc server.
    logger.info("Starting Zotero MCP server ...")
    mcp.run()