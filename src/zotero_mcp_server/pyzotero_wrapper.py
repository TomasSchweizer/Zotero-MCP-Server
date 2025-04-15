"""A Pyzotero Wrapper class and Parser class for the different type of Zotero items."""

from typing import List, Dict, Tuple, Any
from abc import ABC, abstractmethod
from io import BytesIO

from pyzotero import zotero
from bs4 import BeautifulSoup, Tag
import fitz

from .log import logger


class PyzoteroClient(zotero.Zotero):
    """Wrapper around Zotero class."""

    def __init__(self, library_id, library_type, local=True):
        """Initialize the Pyzotero client."""

        super().__init__(library_id=library_id,
                            library_type=library_type,
                            local=local)

    def query_library(self, limit: int, query: str) -> List:
        """Query the zotero library via query string."""

        self.add_parameters(limit=limit, q=query, qmode="everything")
        found_items : List = self.items() # type: ignore
        logger.info("Search results: %d item(s) found%s",
                len(found_items),
                '' if found_items else ' - no items match the search query')
        _assert_list(found_items)
        return found_items

    def retrieve_items(self, item_keys: List) -> List:
        """Retrieve one or more items via key from zotero library."""        
        _assert_list(item_keys)
        retrieved_items = [self.item(str(item_key)) for item_key in item_keys] # type: ignore
        return retrieved_items

class PyzoteroParsingStrategy(ABC):
    """Abstract pyzoter parsing class, template for parsers for specific item types."""

    @abstractmethod
    def parse_title(self, item_data: Dict, item_parent_data: Dict) -> Tuple[str | None, str | None]:
        """Parse the title."""
        return (None, None)


    @abstractmethod
    def parse_content(self, item_data: Dict) -> Dict:
        """Parse the content."""
        return {}

class NotePyzoteroParsingStrategy(PyzoteroParsingStrategy):
    """Parser for zotero notes."""

    def parse_title(self, item_data: Dict, item_parent_data: Dict) -> Tuple[str | None, str | None]:
        """Parse the title of a note item from note field."""

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

        item_parent_title = item_parent_data.get("title") # type: ignore
        return note_title, item_parent_title

    def parse_content(self, item_data: Dict) -> Dict:
        """Parse the content for a item for the LLM."""
        return item_data.get("note") # type: ignore


class ItemPyzoteroParsingStrategy(PyzoteroParsingStrategy):
    """Parser for zotero items besides notes"""

    def parse_title(self, item_data: Dict, item_parent_data: Dict) -> Tuple[str | None, str | None]:
        """Extract title from parent item, because more informative"""
        # For all items besides notes the item_parent_title is more informative than the item title
        return item_data.get("title"), item_parent_data.get("title") # type: ignore

    def parse_content(self, item_data: Dict)  -> Dict:
        """Parse the content for a generic item for the LLM."""
        return {}

class PDFAttachmentPyzoteroParsingStrategy(ItemPyzoteroParsingStrategy):
    """Parser for zotero items which are pdf attachments."""

    def __init__(self, pyzotero_client: PyzoteroClient):
        """Initialize the PDF parser with the Pyzotero client."""
        self.pyzotero_client = pyzotero_client

    def parse_content(self, item_data: Dict)  -> str:
        """Parse the text content of a PDF attachment."""        

        pdf_bytes_io = BytesIO(self.pyzotero_client.file(item_data.get("key"))) #type: ignore
        pdf_text =""

        with fitz.open(stream=pdf_bytes_io, filetype="pdf") as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pdf_text += page.get_text("text") #type: ignore

        return pdf_text

class PyzoteroParser:
    """Parses Zotero items metadata and content."""

    def __init__(self, pyzotero_client: PyzoteroClient,
                 strategy: PyzoteroParsingStrategy | None = None):
        """"""
        self.pyzotero_client = pyzotero_client
        self._strategy = strategy

    def auto_set_strategy(self, item_type: str | None, item_content_type: str | None,
                          item_data: Dict, item_parent_type: str | None = None,
                          item_parent_content_type: str | None = None, item_parent_data: Dict | None = None):
        """Automatically sets the parsing strategy based on item type and content type."""

        if item_type == "note":
            self.set_strategy(NotePyzoteroParsingStrategy())
        elif item_content_type == "application/pdf":
            self.set_strategy(PDFAttachmentPyzoteroParsingStrategy(self.pyzotero_client))
        else:
            self.set_strategy(ItemPyzoteroParsingStrategy())

    def set_strategy(self, strategy: PyzoteroParsingStrategy):
        """Sets the parsing strategy for the parser."""
        self._strategy = strategy

    def parse_items_metadata(self, found_items: List) -> List:
        """Parses important metadata of a list of Zotero items."""

        _assert_list(found_items)
        parsed_items_metadata = [self._parse_item_metadata(found_item) for found_item in found_items]

        return parsed_items_metadata

    def _parse_item_metadata(self, found_item: Dict) -> Dict:
        """Parses important metadata of a single Zotero item."""

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
        item_collection_keys = item_collection_keys if isinstance(item_collection_keys, list) \
                                                    else item_parent_data.get("collections")

        item_collection_names = [self.get_item_collections_names(item_collection_key)[0]
                                    for item_collection_key in item_collection_keys]  #type: ignore

        self.auto_set_strategy(item_type, item_content_type, item_data,
                               item_parent_type, item_parent_content_type, item_parent_data)

        item_title, item_parent_title = self._strategy.parse_title(item_data, item_parent_data) #type: ignore

        item_metadata = {
            "itemKey": item_key,
            "itemType": item_type,
            "itemTitle": item_title,
            "itemParentTitle": item_parent_title,
            "itemCollectionNames": item_collection_names
        }
        return item_metadata

    def parse_items_content(self, retrieved_items: List) -> List:
        """Parses the content of a list of retrieved Zotero items."""

        _assert_list(retrieved_items)
        parsed_items_content = [self._parse_item_content(retrieved_item) for retrieved_item in retrieved_items]

        return parsed_items_content


    def _parse_item_content(self, retrieved_item: Dict) -> Dict:
        """Parses the content of a single retrieved Zotero item."""

        _assert_dict(retrieved_item)
        item_key = retrieved_item.get("key")
        item_data = retrieved_item.get("data", {})
        _assert_dict(item_data)
        item_type = item_data.get("itemType")
        item_content_type = item_data.get("contentType")

        self.auto_set_strategy(item_type, item_content_type, item_data)

        item_title, _ = self._strategy.parse_title(item_data, {}) # type: ignore
        item_content = self._strategy.parse_content(item_data) # type: ignore

        return {
            "itemKey": item_key,
            "itemTitle": item_title,
            "itemContent": item_content
        }

    def get_parent_item_data(self, item_parent_key: str | None) -> Dict:
        """Retrieves and returns the data of a parent Zotero item."""

        if not item_parent_key:
            return {}
        item_parent : Dict = self.pyzotero_client.item(item_parent_key) # type: ignore
        logger.info("Item has a parent item with key: %s", item_parent_key)
        item_parent_data = item_parent.get("data", {})

        return item_parent_data

    def get_item_collections_names(self, collection_key: str | Dict, depth: int = 0) -> Tuple[List[str],int]:
        """Recursively retrieves the names of a collection and its parent collections."""

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

        parent_collections, total_depth = self.get_item_collections_names(parent_collection_key, depth + 1) #type: ignore
        # Calculate reversed depth (0 at top, increasing as we go down)
        reversed_depth = total_depth - depth
        collection_entry = f"Collection depth={reversed_depth}: {collection_name}"

        return parent_collections + [collection_entry], total_depth


def _assert_list(instance: Any):
    """Asserts that the input is a list."""
    if not isinstance(instance, list):
        raise TypeError(f"The found items need to be a of type: {type([])} \
                            but it is of type: {type(instance)}")

def _assert_dict(instance: Any):
    """Asserts that the input is a list."""
    if not isinstance(instance, dict):
        raise TypeError(f"The found item need to be a of type {type({})}, \
                        but is of type: {type(instance)}.")
    if not instance:
        raise ValueError(f"Dict shouldn't be empty: {instance}")

def _assert_tag(instance: Any):
    """Asserts that the input is a BeautifulSoup Tag object."""
    if not isinstance(instance, Tag):
        raise TypeError(f"The found item need to be a of type {type(Tag)}, \
                                but is of type: {type(instance)}.")
