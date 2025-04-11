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
from .pyzotero_wrapper import PyzoteroClient, PyzoteroParser

mcp = FastMCP(name="ZoteroMCPServer", version="0.1.0")

class ZoteroMCPServer():
    """"""
    def __init__(self):

        # Load environment variables
        load_dotenv()
        library_id = os.getenv("LIBRARY_ID")
        library_type = os.getenv("LIBRARY_TYPE")

        # Initialize clients
        self.pyzotero_client = PyzoteroClient(library_id=library_id,
                                                library_type=library_type,
                                                local=True)
        self.pyzotero_parser = PyzoteroParser(pyzotero_client=self.pyzotero_client)

    @mcp.tool()
    def search_zotero_library(self, limit: int, query: str) -> Tuple[str, List]:
        """"""
        found_items = self.pyzotero_client.query_library(limit=limit, query=query)
        if not found_items:
            return "Search results: 0 items found - no items match the search query" , found_items

        parsed_items_metadata = self.pyzotero_parser.parse_items_metadata(found_items=found_items)

        return f"Search results: {len(parsed_items_metadata)} item{'s' if len(parsed_items_metadata) > 1 else ''} found", \
                parsed_items_metadata

# Usage
if __name__ == "__main__":
    server = ZoteroMCPServer()
    logger.info("Instantiated ZoteroMCPServer")
    logger.info("Starting ZoteroMCPServer ...")
    mcp.run()
