# Skill Collection

Each skill is one Markdown file with YAML front matter followed by a concise
operational procedure. The loader ignores this README file.

```yaml
---
name: lowercase_skill_name
description: One sentence explaining when the skill is useful.
triggers:
  - phrase that must appear in the learner question
required_tools:
  - exact_mcp_tool_name
enabled: true
---
```

The body should define activation conditions, ordered evidence-gathering steps,
interpretation rules, stopping conditions, and a safety boundary. Adding a
Markdown file does not grant new authority: every required tool must already be
exposed by the MCP server, or startup validation rejects the skill.

## When a Skill Needs New Evidence

Do not place an imaginary tool name under `required_tools`. First add the
capability to the application:

1. Confirm the model and resource in Yangsuite.
2. Implement a focused RESTCONF function in its own Python module.
3. Validate inputs and return a bounded normalized dictionary.
4. Wrap the function with `@mcp.tool()` in `mcp_server.py`.
5. Add parser and validation tests.
6. Run `python scripts/check_lab27.py` and confirm discovery.
7. Add the exact discovered tool name to the Markdown skill.

Prefer one narrow operational function over a generic URL, shell, CLI, or
configuration tool. The skill explains how to use evidence; the MCP server
defines which evidence the agent is actually authorized to retrieve.
