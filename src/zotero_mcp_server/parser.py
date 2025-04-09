"""Parsers for the different type of Zotero items"""

from bs4 import BeautifulSoup, Tag

from .log import logger

def note_title_parser(note_html: str) -> str:
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