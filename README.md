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
<div>
<video controls src="https://github.com/TomasSchweizer/Zotero-MCP-Server/blob/c3500bff057b36daa1e3b6d61fddb4a3e39352bd/assets/ZoteroMCPServer_example-datalakes.mp4" title="Title", controls="controls" muted="muted" playsinline="playsinline"></video>
</div>