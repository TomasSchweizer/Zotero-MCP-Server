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
<div align="center">
<video src="https://github.com/TomasSchweizer/Zotero-MCP-Server/assets/ZoteroMCPServer_example-datalakes.mp4" controls="controls" muted="muted" playsinline="playsinline">
</video>
</div>
