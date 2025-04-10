"""Parsers for the different type of Zotero items"""
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
from pyzotero import zotero

from bs4 import BeautifulSoup, Tag

from .log import logger


class PyzoteroClient(zotero.Zotero):

    def __init__(self, library_id, library_type, local=True):
        super().__init__(library_id=library_id,
                            library_type=library_type,
                            local=local)
        
    def query_library(self, limit: int, query: str) -> List:
        self.add_parameters(limit=limit, q=query, qmode="everything")
        found_items : List = self.items() # type: ignore
        logger.info("Search results: %d item(s) found%s",
                len(found_items),
                '' if found_items else ' - no items match the search query')
        assert isinstance(found_items, list)
        if not isinstance(found_items, list):
            raise TypeError(f"The found items need to be a of type: {type(list())} \
                                but it is of type: {type(found_items)}")
        return found_items
    

class PyzoteroParser(ABC):

    def __init__(self, pyzotero_client: PyzoteroClient):
        self.pyzotero_client = pyzotero_client

    @abstractmethod
    def parse_title(self, found_item: List) -> Dict:
        pass
    
    @abstractmethod
    def parse_content(self, found_items: List) -> Dict:
        pass



def note_parser(note_html: str) -> str:
    """Parses the html returned from a zotero note."""
    soup = BeautifulSoup(note_html, "html.parser")
    div = soup.find("div", {"data-schema-version": "9"})
    assert isinstance(div, Tag)
    if not isinstance(div, Tag):
        raise TypeError(f"The found item need to be a of type {type(Tag)}, \
                                but is of type: {type(div)}.")

    note_title = None
    for child_element in div.contents:
        # Check if the child is a Tag and is an h1
        if isinstance(child_element, Tag):
            if child_element.name == "h1":
                note_title = child_element.get_text()
                logger.info("Found note title: %s", note_title)
                break

    if note_title is None:
        note_title = div.contents[0].get_text()
        logger.info("Found no note title inside h1 tag, therefore took first element: %s", note_title)

    return note_title