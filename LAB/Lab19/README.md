# Lab 19: Local AI Routing Assistant with RESTCONF and MCP

This folder contains the learner guide and working Python files for a local Ollama chatbot that answers questions from live IOS XE routing data. Start with [Lab19.md](Lab19.md).

The solution is deliberately read-only. A FastMCP server owns RESTCONF access, normalizes the operational RIB, and exposes three bounded tools. The local language model can reason over those results but cannot send arbitrary RESTCONF requests or change device configuration.

