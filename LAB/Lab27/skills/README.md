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
