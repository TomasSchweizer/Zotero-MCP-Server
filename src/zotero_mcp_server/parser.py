"""Parsers for the different type of Zotero items"""
from bs4 import BeautifulSoup



def note_parser(note_html: str) -> str:
    """Parses the html returned from a zotero note."""
    soup = BeautifulSoup(note_html, 'html.parser')
    div = soup.find('div', {'data-schema-version': '9'})
    if div:
        # Iterate through the immediate children of the <div>
        first_h1 = None
        for child in div.contents:
            # Check if the child is a Tag and is an h1
            if child.name == 'h1':
                first_h1 = child.get_text()
                break
    
    if first_h1 is None:
        raise RuntimeError("No <h1> tag found in the specified HTML structure.")
    
    return first_h1
