"""Parsers for the different type of Zotero items"""
from typing import List, Dict, Tuple, Any
from abc import ABC, abstractmethod
from pyzotero import zotero

from bs4 import BeautifulSoup, Tag

from .log import logger


class PyzoteroClient(zotero.Zotero):
    """Wrapper around Zotero class"""

    def __init__(self, library_id, library_type, local=True):
        super().__init__(library_id=library_id,
                            library_type=library_type,
                            local=local)

    def query_library(self, limit: int, query: str) -> List:
        """Query the zotero library via query string"""

        self.add_parameters(limit=limit, q=query, qmode="everything")
        found_items : List = self.items() # type: ignore
        logger.info("Search results: %d item(s) found%s",
                len(found_items),
                '' if found_items else ' - no items match the search query')
        _assert_list(found_items)
        return found_items
    

class PyzoteroParsingStrategy(ABC):
    """Abstract pyzoter parsing class, template for parsers for specific item types"""

    def __init__(self):
        pass

    @abstractmethod
    def parse_title(self, item_data: Dict, item_parent_data: Dict | None) -> Dict:
        pass

    @abstractmethod
    def parse_content(self, item_data: Dict) -> Dict:
        pass

class NotePyzoteroParsingStrategy(PyzoteroParsingStrategy):
    """Parser for zotero notes"""

    def parse_title(self, item_data: Dict, item_parent_data: Dict | None = None) -> str:
        """Parse the title of a note item from note field"""

        note_html = item_data.get("note")
        parsed_html = BeautifulSoup(note_html, "html.parser") # type: ignore
        note_div = parsed_html.find("div", {"data-schema-version": "9"})
        _assert_tag(note_div)
        
        note_title = None
        for child_element in note_div.contents: # type: ignore
            # Check if the child is a Tag and is an h1
            if isinstance(child_element, Tag):
                if child_element.name == "h1":
                    note_title = child_element.get_text()
                    logger.info("Found note title: %s", note_title)
                    break

        if note_title is None:
            note_title = note_div.contents[0].get_text() # type: ignore
            logger.info("Found no note title inside h1 tag, therefore took first element: %s", note_title)

        return note_title

    def parse_content(self, item_data: Dict) -> Dict:
        """Parse the content for a item for the LLM"""
        return {}
    

class ItemPyzoteroParsingStrategy(PyzoteroParsingStrategy):
    """Parser for zotero items besides notes"""
    def parse_title(self, item_data: Dict, item_parent_data: Dict | None) -> str | None:
        """Extract title from parent item, because more informative"""
        # For all items besides notes the item_parent_title is more informative than the item title
        return item_parent_data.get("title") # type: ignore

    def parse_content(self, item_data: Dict)  -> Dict:
        """Parse the content for a item for the LLM"""
        return {}

class PyzoteroParser:
    """Implements the pyzotero parser, parses common fieds, and selects correct parser depending on item type"""

    def __init__(self, pyzotero_client: PyzoteroClient, 
                 strategy: PyzoteroParsingStrategy | None = None):
        """"""
        self.pyzotero_client = pyzotero_client
        self._strategy = strategy

    def auto_set_strategy(self, item_type: str | None, item_content_type: str | None, item_data: Dict,
                           item_parent_type: str | None, item_parent_content_type: str | None, item_parent_data: Dict):
        """"""
        if item_content_type.startswith("image/") and item_parent_type == "note": # type: ignore
            pass # Pass because these are embedded images in notes, which are not relevant currently for title parsing
        if item_type == "note":
            self.set_strategy(NotePyzoteroParsingStrategy())
        else:
            self.set_strategy(ItemPyzoteroParsingStrategy())

    def set_strategy(self, strategy: PyzoteroParsingStrategy):
        """"""
        self._strategy = strategy

    def parse_items_metadata(self, found_items: List) -> List:
        """Parses important fields of a list of items"""

        _assert_list(found_items)
        parsed_items_metadata = [self._parse_item_metadata(found_item) for found_item in found_items]

        return parsed_items_metadata


    def _parse_item_metadata(self, found_item: Dict) -> Dict:
        """Parses important fields of one item which all zotero items have"""
        _assert_dict(found_item)
        item_key = found_item.get("key")
        item_data = found_item.get("data", {})
        _assert_dict(item_data)

        item_type = item_data.get("itemType")
        item_content_type = item_data.get("contentType")

        # Check if the item has collections
        item_collection_keys = item_data.get("collections")
        # Check if item has a parentItem
        item_parent_key = item_data.get("parentItem")
        item_parent_data = self.get_parent_item_data(item_parent_key)
        item_parent_type = item_parent_data.get("itemType")
        item_parent_content_type = item_parent_data.get("contentType")
        item_collection_keys = item_collection_keys or item_parent_data.get("collections")
        _assert_list(item_collection_keys)

        item_collection_names = [self.get_item_collections_names(item_collection_key)[0]
                                    for item_collection_key in item_collection_keys]  #type: ignore

        self.auto_set_strategy(item_type, item_content_type, item_data,
                               item_parent_type, item_parent_content_type, item_parent_data)
        
        item_title = self._strategy.parse_title(item_data, item_parent_data) #type: ignore

        item_metadata = {
            "itemKey": item_key,
            "itemType": item_type,
            "itemTitle": item_title,
            "itemCollectionNames": item_collection_names
        }
        return item_metadata

    def get_parent_item_data(self, item_parent_key: str | None) -> Dict:
        """Calls the zotero API and returns the data of a parent Item"""
        if not item_parent_key:
            return {}
        item_parent : Dict = self.pyzotero_client.item(item_parent_key) # type: ignore
        logger.info("Item has a parent item with key: %s", item_parent_key)
        item_parent_data = item_parent.get("data", {})

        return item_parent_data
    
    def get_item_collections_names(self, collection_key: str | Dict, depth: int = 0) -> Tuple[List[str],int]:
        """Recursively retrieves the names of the collection and all of its parent collections."""
        
        if depth > 100:
            raise RecursionError("Created an infinite recursion!")

        if isinstance(collection_key, dict):
            collection_key = list(collection_key.values()) # type: ignore

        logger.info("Depth %d: Processing collection key: %s", depth, collection_key)
        collection: Dict = self.pyzotero_client.collection(collection_key) # type: ignore
        _assert_dict(collection)
        collection_data = collection.get("data", {}) # type: ignore
        _assert_dict(collection_data)
        collection_name = collection_data.get("name")
        parent_collection_key = collection_data.get("parentCollection")

        if not parent_collection_key:
            total_depth = depth
            return [f"Collection depth=0: {collection_name}"], total_depth

        parent_collections, total_depth = self.get_item_collections_names(parent_collection_key, depth + 1)
        # Calculate reversed depth (0 at top, increasing as we go down)
        reversed_depth = total_depth - depth
        collection_entry = f"Collection depth={reversed_depth}: {collection_name}"

        return parent_collections + [collection_entry], total_depth


def _assert_list(instance: Any):
    if not isinstance(instance, list):
        raise TypeError(f"The found items need to be a of type: {type(list())} \
                            but it is of type: {type(instance)}")

def _assert_dict(instance: Any):
    if not isinstance(instance, dict):
        raise TypeError(f"The found item need to be a of type {type(dict())}, \
                        but is of type: {type(instance)}.")
    if not instance:
        raise ValueError(f"Dict shouldn't be empty: {instance}")

def _assert_tag(instance: Any):
    if not isinstance(instance, Tag):
        raise TypeError(f"The found item need to be a of type {type(Tag)}, \
                                but is of type: {type(instance)}.")



