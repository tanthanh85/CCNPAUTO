# Lab 15: Multi-Provider AI Network Assistant with Flask, FastMCP, and RESTCONF

Build a professional dark-theme web assistant that answers questions about the routing table of a Cisco IOS XE reservable sandbox router. The assistant uses:

- Flask for the web UI
- Ollama with local `qwen3:8b`, or an OpenAI or Anthropic API model
- A provider-neutral Python module for switching models through `.env`
- Python FastMCP to expose controlled route-information tools
- RESTCONF inside the MCP server to retrieve live route information

Start with [Lab15.md](Lab15.md).
