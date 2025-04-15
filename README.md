# Zotero MCP Server 



## Development

Install the project in development mode, so that imports work correctly.
This allows to import functions from my package into tests like this:
```python
from zotero_mcp_server.zotero_mcp_server import pyzotero_search_library
```
Imports in the module/package itself are done via relaive paths.

```bash
uv pip install -e
```

https://github.com/user-attachments/assets/7b422a20-f326-4cf9-bc4f-654a783c0933


## Similar Repositories

[zotero-mcp-server by swairshah](https://github.com/swairshah/zotero-mcp-server)

[mcp-pyzotero by gyger](https://github.com/gyger/mcp-pyzotero)